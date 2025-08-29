# insurance_app/services/embedding_provider.py
import os, json, requests, numpy as np
from typing import Sequence, Union

INDEX_DIM = int(os.getenv("INDEX_DIM", os.getenv("TARGET_INDEX_DIM", "1024")))

def _l2n(a: np.ndarray) -> np.ndarray:
    return a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)

class HFRemoteEmbedder:
    def __init__(self, model_id: str, token: str | None, timeout: float = 45.0):
        self.model_id = model_id
        self.timeout = float(os.getenv("HF_INFERENCE_TIMEOUT", timeout))
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._emb_endpoint = f"https://api-inference.huggingface.co/embeddings/{model_id}"
        self._models_endpoint = f"https://api-inference.huggingface.co/models/{model_id}"

    def embed(self, texts: Union[str, Sequence[str]]) -> np.ndarray:
        if isinstance(texts, str): texts = [texts]
        # 1) embeddings 엔드포인트
        try:
            r = requests.post(self._emb_endpoint, headers=self.headers,
                              json={"inputs": list(texts)}, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            arr = np.array(data["embeddings"] if isinstance(data, dict) and "embeddings" in data else data,
                           dtype=np.float32)
        except Exception:
            # 2) models + X-Task 폴백
            hdrs = dict(self.headers); hdrs["X-Task"] = "feature-extraction"
            r = requests.post(self._models_endpoint, headers=hdrs,
                              json={"inputs": list(texts), "options": {"wait_for_model": True}},
                              timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            embs = []
            for item in data:
                a = np.array(item, dtype=np.float32)
                if a.ndim == 2: a = a.mean(axis=0)  # mean pooling
                embs.append(a)
            arr = np.stack(embs, axis=0)
        arr = _l2n(arr)
        if arr.shape[1] != INDEX_DIM:
            raise RuntimeError(f"Embedding dim {arr.shape[1]} != INDEX_DIM {INDEX_DIM}")
        return arr

def get_query_embedder():
    # 원격 임베딩 강제(메모리 1GB에서도 안정)
    model_id = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")
    token = os.getenv("HF_TOKEN")
    return HFRemoteEmbedder(model_id, token)
