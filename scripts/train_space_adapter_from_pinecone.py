from dotenv import load_dotenv
import os, random, numpy as np
from typing import List, Optional, Dict, Any
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import Ridge
load_dotenv()
INDEX_DIM = int(os.getenv("INDEX_DIM", "1024"))
# 공백/빈값은 기본 네임스페이스("")로 강제
NAMESPACE = (os.getenv("NAMESPACE") or "").strip()
SMALL_MODEL = os.getenv("EMBED_MODEL_SMALL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
SAVE_PATH   = os.getenv("SPACE_ADAPTER_PATH", "insurance_app/models/space_adapter_v1.npz")

# 스캔 파라미터(환경변수로 조정 가능)
TARGET_SAMPLES = int(os.getenv("TARGET_SAMPLES", "4000"))  # 목표 학습 샘플 수
SCAN_TOPK      = int(os.getenv("SCAN_TOPK", "128"))        # 라운드당 조회 수
SCAN_ROUNDS    = int(os.getenv("SCAN_ROUNDS", "80"))       # 라운드 수

def _get_matches(res) -> List[Any]:
    return getattr(res, "matches", None) or getattr(res, "data", None) or []

def _get_attr(obj, key: str):
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)

TEXT_KEYS = ("text", "chunk", "content", "clause", "body", "passage", "raw", "paragraph")

def _extract_text(meta: Optional[Dict[str, Any]]) -> Optional[str]:
    if not meta or not isinstance(meta, dict):
        return None
    for k in TEXT_KEYS:
        v = meta.get(k)
        if isinstance(v, str) and len(v.strip()) >= 8:
            return v.strip()[:512]
    # 텍스트 키가 없으면 title/page 조합이라도 사용(품질은 다소 낮음)
    title = meta.get("title") if isinstance(meta.get("title"), str) else None
    page  = meta.get("page")
    if title:
        return f"{title} (p.{page})" if page is not None else title
    return None

def main():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not api_key or not index_name:
        raise SystemExit("PINECONE_API_KEY / PINECONE_INDEX_NAME 필요")
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    seen_ids = set()
    texts, vecs = [], []

    for _ in range(SCAN_ROUNDS):
        # 0 근처 랜덤 벡터로 넓게 샘플링(POST body라 414 없음)
        probe = (np.random.normal(0, 1e-3, size=INDEX_DIM)).astype("float32").tolist()
        res = index.query(
            vector=probe, top_k=SCAN_TOPK,
            include_values=True, include_metadata=True,
            namespace=NAMESPACE
        )
        matches = _get_matches(res) or []
        for m in matches:
            vid = _get_attr(m, "id")
            if not vid or vid in seen_ids:
                continue
            meta = _get_attr(m, "metadata")
            vals = _get_attr(m, "values")
            if not vals or len(vals) != INDEX_DIM:
                continue
            text = _extract_text(meta)
            if not text:
                continue
            seen_ids.add(vid)
            texts.append(text)
            vecs.append(np.asarray(vals, dtype="float32"))
            if len(texts) >= TARGET_SAMPLES:
                break
        if len(texts) >= TARGET_SAMPLES:
            break

    if len(texts) < 200:
        raise SystemExit(f"수집된 (텍스트,벡터) 페어가 너무 적습니다: {len(texts)}개. "
                         f"SCAN_ROUNDS/SCAN_TOPK를 늘리거나, 업로드 시 메타데이터에 'text'/'chunk' 키가 저장됐는지 확인하세요.")

    print(f"[scan] collected pairs = {len(texts)}  dim={len(vecs[0])}")

    # 작은 모델 임베딩
    st = SentenceTransformer(SMALL_MODEL)
    X = st.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True)
    Y = np.vstack(vecs)

    # X @ W ≈ Y (Ridge, no intercept)
    from sklearn.linear_model import Ridge
    reg = Ridge(alpha=1.0, fit_intercept=False, random_state=0)
    reg.fit(X, Y)
    W = reg.coef_.T.astype("float32")  # (d_small, 1024)

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    np.savez(SAVE_PATH, W_query=W, W_doc=W, dim_small=np.array([X.shape[1]], dtype="int32"))
    print(f"[scan] saved adapter: {SAVE_PATH}  (W {W.shape}, samples {len(texts)})")

if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    random.seed(0); np.random.seed(0)
    main()
