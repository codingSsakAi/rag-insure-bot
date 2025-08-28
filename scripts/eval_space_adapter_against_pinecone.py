# scripts/eval_space_adapter_against_pinecone.py
import os, re, hashlib, random, pathlib, logging, warnings
from typing import List, Tuple
import numpy as np

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

load_dotenv()
warnings.filterwarnings("ignore")
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.ERROR)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
NAMESPACE = os.getenv("NAMESPACE") or None
INDEX_DIM = int(os.getenv("INDEX_DIM", "1024"))
ADAPTER_PATH = os.getenv("SPACE_ADAPTER_PATH", "insurance_app/models/space_adapter_v1.npz")
DOC_ROOT = os.getenv("DOC_ROOT", "insurance_app/documents")
SMALL_MODEL = os.getenv("EMBED_MODEL_SMALL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
N_TEST = int(os.getenv("N_TEST", "500"))
SMALL_BATCH = int(os.getenv("SMALL_BATCH", "256"))
FETCH_BATCH = int(os.getenv("FETCH_BATCH", "256"))

def normalize_text(s: str) -> str:
    s = s.replace("\x00"," ")
    s = re.sub(r"\s+"," ", s)
    return s.strip()

def chunk_text(text: str, max_chars: int = 900) -> List[str]:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    chunks, acc = [], []
    cur = 0
    for ln in lines:
        if cur + len(ln) > max_chars:
            if acc: chunks.append("\n".join(acc)); acc = []; cur = 0
        acc.append(ln[:512]); cur += min(len(ln), 512)
    if acc: chunks.append("\n".join(acc))
    return chunks

def hash_id(company: str, file: str, page: int, idx: int) -> str:
    return hashlib.md5(f"{company}::{file}::{page}::{idx}".encode("utf-8")).hexdigest()

def collect_pairs(root: str, n: int) -> List[Tuple[str, str]]:
    import pdfplumber
    pairs = []
    for comp_dir in pathlib.Path(root).iterdir():
        if not comp_dir.is_dir(): continue
        for pdf_path in comp_dir.glob("*.pdf"):
            try:
                with pdfplumber.open(str(pdf_path)) as pdf:
                    for p_idx, p in enumerate(pdf.pages, start=1):
                        raw = normalize_text(p.extract_text() or "")
                        chunks = chunk_text(raw)
                        for c_idx, ch in enumerate(chunks, start=1):
                            vid = hash_id(comp_dir.name, pdf_path.name, p_idx, c_idx)
                            pairs.append((vid, ch))
                            if len(pairs) >= n:
                                return pairs
            except Exception:
                continue
    return pairs

def batched(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def main():
    if not os.path.exists(ADAPTER_PATH):
        raise SystemExit(f"어댑터가 없습니다: {ADAPTER_PATH}")
    data = np.load(ADAPTER_PATH)
    Wq = data["W_query"]; d_small = int(data["dim_small"][0])

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)

    pairs = collect_pairs(DOC_ROOT, N_TEST)
    if not pairs:
        raise SystemExit("평가용 텍스트가 없습니다.")

    # teacher from Pinecone
    Y_list, X_texts = [], []
    for batch in batched(pairs, FETCH_BATCH):
        ids = [vid for (vid, _) in batch]
        fetched = index.fetch(ids=ids, namespace=NAMESPACE)
        vecs = fetched.get("vectors") or {}
        for vid, tx in batch:
            item = vecs.get(vid)
            if not item: continue
            values = item.get("values") or item.get("vector") or []
            if not values or len(values) != INDEX_DIM: continue
            Y_list.append(np.asarray(values, dtype="float32"))
            X_texts.append(tx)
    if not Y_list:
        raise SystemExit("Pinecone로부터 교사 벡터를 가져오지 못했습니다.")

    Y = np.vstack(Y_list)
    small = SentenceTransformer(SMALL_MODEL)
    X_list = []
    for chunk in batched(X_texts, SMALL_BATCH):
        X_list.append(small.encode(chunk, normalize_embeddings=True, convert_to_numpy=True))
    X = np.vstack(X_list)
    if X.shape[1] != d_small:
        raise SystemExit(f"차원 불일치: small {X.shape[1]} vs adapter {d_small}")

    Y_hat = X @ Wq
    Y_hat /= (np.linalg.norm(Y_hat, axis=1, keepdims=True) + 1e-12)
    Y /= (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-12)

    cos = np.sum(Y_hat * Y, axis=1)
    print(f"n={len(cos)} mean={cos.mean():.4f} median={np.median(cos):.4f} p10={np.percentile(cos,10):.4f} p90={np.percentile(cos,90):.4f}")

if __name__ == "__main__":
    main()
