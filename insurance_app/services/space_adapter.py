# insurance_app/services/space_adapter.py
import os, threading
import numpy as np
from sentence_transformers import SentenceTransformer

_lock = threading.Lock()
_small = None
_W_query = None
_dim_small = None

def _load_small():
    global _small
    with _lock:
        if _small is None:
            name = os.getenv("EMBED_MODEL_SMALL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            _small = SentenceTransformer(name)
    return _small

def _load_adapter():
    global _W_query, _dim_small
    with _lock:
        if _W_query is None:
            path = os.getenv("SPACE_ADAPTER_PATH", "insurance_app/models/space_adapter_v1.npz")
            if not os.path.exists(path):
                raise RuntimeError(f"SPACE_ADAPTER_PATH not found: {path}")
            data = np.load(path)
            _W_query = data["W_query"]   # (d_small, 1024)
            _dim_small = int(data["dim_small"][0])
    return _W_query, _dim_small

def embed_query_to_e5space(text: str) -> list[float]:
    """
    작은 모델(예: 384/768d) 임베딩 -> 선형사상(W_query) -> L2정규화 -> 1024d(e5 공간)
    """
    small = _load_small()
    x = small.encode([text], normalize_embeddings=True)[0]     # (d_small,)
    Wq, d_small = _load_adapter()
    if x.shape[0] != d_small:
        raise RuntimeError(f"small dim mismatch: {x.shape[0]} vs {d_small}")
    y = np.matmul(x, Wq)                                      # (1024,)
    n = np.linalg.norm(y)
    if n > 0:
        y = y / n
    return y.astype("float32").tolist()
