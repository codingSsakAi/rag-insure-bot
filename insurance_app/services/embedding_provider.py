# insurance_app/services/embedding_provider.py
import os, time, requests, numpy as np
from typing import Sequence, Union
from huggingface_hub import InferenceClient, HfApi

INDEX_DIM = int(os.getenv("INDEX_DIM", os.getenv("TARGET_INDEX_DIM", "1024")))
HF_TIMEOUT = float(os.getenv("HF_INFERENCE_TIMEOUT", "60"))
HF_RETRIES = int(os.getenv("EMBED_RETRY", "3"))

def _l2n(a: np.ndarray) -> np.ndarray:
    return a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)

class HFRemoteEmbedder:
    def __init__(self, model_id: str, token: str | None, timeout: float = HF_TIMEOUT, retries: int = HF_RETRIES):
        self.model_id = model_id
        self.token = token
        self.client = InferenceClient(model=model_id, token=token, timeout=timeout)
        self.api = HfApi(token=token)
        self.timeout = timeout
        self.retries = retries
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._models_url = f"https://api-inference.huggingface.co/models/{model_id}"

    def _fallback_models_endpoint(self, text: str) -> np.ndarray:
        r = requests.post(
            self._models_url,
            headers={**self.headers, "X-Task": "feature-extraction"},
            json={"inputs": text, "options": {"wait_for_model": True}},
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        a = np.asarray(data, dtype=np.float32)
        if a.ndim == 2:
            a = a.mean(axis=0)
        return a

    def embed(self, texts: Union[str, Sequence[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        embs = []
        last_err = None
        for t in texts:
            ok = False
            for i in range(self.retries):
                try:
                    v = self.client.feature_extraction(t, wait_for_model=True)
                    a = np.asarray(v, dtype=np.float32)
                    if a.ndim == 2:
                        a = a.mean(axis=0)
                    embs.append(a)
                    ok = True
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(min(4.0, 0.7 * (i + 1) ** 2))
            if not ok:
                a = self._fallback_models_endpoint(t)
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

def warmup_embedding_model():
    if os.getenv("HF_WARMUP", "1") != "1":
        return
    try:
        embedder = get_query_embedder()
        try:
            embedder.api.model_info(embedder.model_id)
        except Exception:
            pass
        try:
            embedder.embed(["ping"])
        except Exception:
            pass
    except Exception:
        pass
