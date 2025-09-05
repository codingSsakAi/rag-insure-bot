import os, numpy as np
from typing import Sequence
from huggingface_hub import InferenceClient

INDEX_DIM = int(os.getenv("INDEX_DIM", os.getenv("TARGET_INDEX_DIM", "1024")))

def _l2n(a: np.ndarray) -> np.ndarray:
    return a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)

class HFRemoteEmbedder:
    def __init__(self, model_id: str, token: str | None, timeout: float = 15.0):
        self.model_id = model_id
        self.client = InferenceClient(model=model_id, token=token, timeout=timeout)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        embs = []
        for t in texts:
            v = self.client.feature_extraction(t)
            a = np.asarray(v, dtype=np.float32)
            if a.ndim == 2:
                a = a.mean(axis=0)
            embs.append(a)
        arr = np.stack(embs, axis=0)
        arr = _l2n(arr)
        if arr.shape[1] != INDEX_DIM:
            raise RuntimeError(f"Embedding dim {arr.shape[1]} != INDEX_DIM {INDEX_DIM}")
        return arr

def get_query_embedder():
    model_id = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")
    token = os.getenv("HF_TOKEN")
    return HFRemoteEmbedder(model_id, token)
