import os
import re
import unicodedata
from functools import lru_cache
from typing import List, Dict, Optional, Any

# -----------------------
# .env
# -----------------------
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

# 원격 임베딩 프로바이더(로컬 모델 다운로드/로딩 없음)
from insurance_app.services.embedding_provider import get_query_embedder

# 인덱스 차원 읽기 유틸(서버 기동 후, 쿼리 시점에 호출)
from .utils.vec_compat import read_index_dim

# -----------------------
# 설정/가중치
# -----------------------
EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")
INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME", "")
NAMESPACE   = os.getenv("NAMESPACE") or None

W_SEMANTIC = float(os.getenv("W_SEMANTIC", "0.7"))   # 벡터 유사도 가중(보조값; 현재 내부 사용 X)
W_LEXICAL  = float(os.getenv("W_LEXICAL",  "0.3"))   # BM25/토큰겹침 가중(보조값; 현재 내부 사용 X)
W_RECENCY  = float(os.getenv("W_RECENCY",  "0.0"))   # 연도 메타 있을 때만 영향(보조값)

def _is_e5(name: str) -> bool:
    return "e5" in (name or "").lower()

# -----------------------
# Lexical 보조 점수 (BM25 또는 토큰겹침)
# -----------------------
def _collapse_vertical_tokens(s: str) -> str:
    # '**과**<br>**실**<br>...' 같은 세로 토막 제거
    return re.sub(r'(\*\*[가-힣A-Za-z]\*\*)(?:<br>|\n){1,}', '', s or '')

def _tokenize_lex(s: str) -> list:
    s = s.lower()
    s = re.sub(r"[^0-9a-z가-힣\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return [t for t in s.split() if len(t) > 1]

def _bm25_scores(query: str, docs: list) -> list:
    try:
        from rank_bm25 import BM25Okapi  # 선택 설치
        corpus = [_tokenize_lex(d) for d in docs]
        bm = BM25Okapi(corpus)
        return bm.get_scores(_tokenize_lex(query)).tolist()
    except Exception:
        # Fallback: 단순 토큰 교집합 크기
        q = set(_tokenize_lex(query))
        return [float(len(q & set(_tokenize_lex(d)))) for d in docs]

def _zscore(xs: list) -> list:
    if not xs: return xs
    m = sum(xs)/len(xs)
    v = sum((x-m)**2 for x in xs)/len(xs)
    sd = (v ** 0.5) if v > 0 else 1.0
    return [(x-m)/sd for x in xs]

def _recency_boost(years: list) -> list:
    # 최신 연도일수록 높게. 메타에 'year' 없으면 0.
    now = 2025
    boosts = []
    for y in years:
        try:
            y = int(y)
        except Exception:
            y = None
        if y is None:
            boosts.append(0.0)
        else:
            delta = max(0, now - y)
            boosts.append(1.0/(1.0 + 0.25*delta))
    return boosts

# -----------------------
# 기본 정리
# -----------------------
def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _join_short_chopped_hangul(s: str) -> str:
    def _join_once(txt: str, n: int) -> str:
        pattern = r"(?:\b[가-힣]\b(?:\s+\b[가-힣]\b){" + str(n-1) + r"})"
        def repl(m): return re.sub(r"\s+", "", m.group(0))
        return re.sub(pattern, repl, txt)
    s = _join_once(s, 3)
    s = _join_once(s, 2)
    return s

def _collapse_adjacent_word_dups(s: str) -> str:
    return re.sub(r"\b([가-힣A-Za-z]{2,})\b(?:\s+\1\b)+", r"\1", s)

def _display_clean(s: str) -> str:
    if not s: return s
    s = _collapse_vertical_tokens(s)
    s = _join_short_chopped_hangul(s)
    s = _collapse_adjacent_word_dups(s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

def _is_noise(text: str) -> bool:
    if not text: return True
    t = text.strip()
    if len(t) < 25: return True
    toks = t.split()
    if not toks: return True
    single_ko = sum(1 for w in toks if len(w) == 1 and re.match(r"[가-힣]", w))
    if single_ko / len(toks) > 0.30: return True
    return False

# -----------------------
# Pinecone (지연 로드)
# -----------------------
from pinecone import Pinecone

@lru_cache(maxsize=1)
def _get_pinecone_index():
    api_key = os.getenv("PINECONE_API_KEY") or ""
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY가 비어 있습니다.")
    if not INDEX_NAME:
        raise RuntimeError("PINECONE_INDEX_NAME(.env)이 비어 있습니다.")
    pc = Pinecone(api_key=api_key)
    return pc.Index(INDEX_NAME)

@lru_cache(maxsize=1)
def _get_index_dim() -> int:
    default_dim = int(os.getenv('INDEX_DIM', os.getenv('TARGET_INDEX_DIM', '1024')))
    idx = _get_pinecone_index()
    return read_index_dim(idx, default_dim)

# -----------------------
# (선택) 재랭커도 지연 로드
# -----------------------
@lru_cache(maxsize=1)
def _get_reranker():
    if os.getenv("USE_RERANKER", "0") != "1":
        return None
    try:
        from sentence_transformers import CrossEncoder
        model_id = os.getenv("RERANKER_MODEL", "jinaai/jina-reranker-v2-base-multilingual")
        return CrossEncoder(model_id)
    except Exception as e:
        print(f"[WARN] Reranker load failed: {e}")
        return None

# -----------------------
# 검색
# -----------------------
def retrieve(query: str,
             top_k: int = 5,
             candidate_k: int = 20,
             company: Optional[str] = None,
             filters: Optional[Dict[str, Any]] = None,
             min_score: float = 0.0) -> List[Dict[str, Any]]:
    """
    순수 RAG용 조회. 결과는 정리된 텍스트와 메타데이터 포함.
    - 모든 외부 네트워크 초기화는 '지연 로드' → 서버 기동이 빨라지고 503(포트 미바인딩) 방지
    - 임베딩은 원격(HF Inference API) 사용 → 1GB 메모리에서 안정
    - e5 계열 인덱스와 호환되도록 query prefix 자동 적용
    """
    # 0) 필수 리소스 준비(최초 1회만 네트워크 접근)
    index = _get_pinecone_index()
    index_dim = _get_index_dim()

    # 1) 쿼리 정규화 + e5 query prefix
    norm = _normalize(query)
    q_text = f"query: {norm}" if _is_e5(EMBED_MODEL) else norm

    # 2) 쿼리 임베딩(원격)
    _embedder = get_query_embedder()                # HF 원격 또는 구성된 프로바이더
    q_vec_np = _embedder.embed([q_text])[0]         # numpy.ndarray([index_dim], float32)
    if q_vec_np.shape[0] != index_dim:
        raise RuntimeError(f"Embedding dim {q_vec_np.shape[0]} != index dim {index_dim}")
    q_emb = q_vec_np.astype("float32").tolist()     # Pinecone에 넣을 list[float]

    # 3) 필터 구성
    pine_filter: Dict[str, Any] = dict(filters or {})
    if company:
        pine_filter["company"] = company

    # 4) Pinecone 질의
    res = index.query(
        vector=q_emb,
        top_k=max(candidate_k, top_k),
        include_metadata=True,
        filter=pine_filter if pine_filter else None,
        namespace=NAMESPACE
    )

    # 5) 후처리 / 노이즈 컷
    prelim: List[Dict[str, Any]] = []
    for m in res.get("matches", []) or []:
        meta = m.get("metadata", {}) or {}
        raw = meta.get("text") or meta.get("chunk") or ""
        if _is_noise(raw):
            continue
        prelim.append({
            "score": m.get("score", 0.0),
            "text": raw,
            "company": meta.get("company", ""),
            "file": meta.get("file", ""),
            "page": meta.get("page", ""),
            "chunk_idx": meta.get("chunk_idx", ""),
        })

    if min_score > 0:
        prelim = [x for x in prelim if x["score"] >= min_score]

    final = sorted(prelim, key=lambda x: x["score"], reverse=True)[:top_k]
    return final


def retrieve_insurance_clauses(query: str,
                               top_k: int = 5,
                               company: Optional[str] = None,
                               candidate_k: int = 20,
                               filters: Optional[Dict[str, Any]] = None,
                               min_score: float = 0.0) -> List[Dict[str, Any]]:
    return retrieve(query, top_k=top_k, candidate_k=candidate_k,
                    company=company, filters=filters, min_score=min_score)
