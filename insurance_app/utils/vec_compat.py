import os
import numpy as np

def is_e5(model_name: str) -> bool:
    return "e5" in (model_name or "").lower()

def add_doc_prefix(texts, model_name: str):
    if not texts:
        return texts
    if is_e5(model_name):
        return [("passage: " + (t or "")) for t in texts]
    return texts

def add_query_prefix(text: str, model_name: str):
    if is_e5(model_name):
        return "query: " + (text or "")
    return text or ""

def adapt_vectors(vectors, target_dim: int):
    if not vectors:
        return vectors
    v = np.asarray(vectors, dtype="float32")
    if v.ndim == 1:
        v = v.reshape(1, -1)
    n, d = v.shape
    if d == target_dim:
        out = v
    elif d < target_dim:
        out = np.zeros((n, target_dim), dtype="float32")
        out[:, :d] = v
    else:
        out = v[:, :target_dim]
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    out = out / norms
    return out.tolist()

def adapt_vector(vec, target_dim: int):
    if vec is None:
        return None
    return adapt_vectors([vec], target_dim)[0]

def read_index_dim(index, default_dim: int | None = None) -> int:
    try:
        st = index.describe_index_stats()
        dim = st.get("dimension")
        if dim:
            return int(dim)
    except Exception:
        pass
    if default_dim is None:
        default_dim = int(os.getenv("TARGET_INDEX_DIM", os.getenv("INDEX_DIM", "1024")))
    return default_dim
