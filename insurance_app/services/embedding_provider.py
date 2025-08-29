# insurance_app/services/embedding_provider.py
import os
import json
import time
from typing import List, Union, Sequence
import numpy as np
import requests

INDEX_DIM = int(os.getenv("INDEX_DIM", os.getenv("TARGET_INDEX_DIM", "1024")))

def _l2n(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / n

class HFRemoteEmbedder:
    """
    Hugging Face Inference API로 동일 모델(e5-large 등)을 호출하여
    로컬 메모리/다운로드 없이 쿼리 임베딩을 계산합니다.
    """
    def __init__(self, model_id: str, token: str | None, timeout: float = 45.0):
        self.model_id = model_id
        self.timeout = timeout
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._emb_endpoint = f"https://api-inference.huggingface.co/embeddings/{model_id}"
        self._feat_endpoint = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_id}"

    def _post(self, url: str, payload: dict) -> Union[dict, list]:
        r = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
        r.raise_for_status()
        try:
            return r.json()
        except json.JSONDecodeError:
            raise RuntimeError(f"Non-JSON response from {url}")

    def embed(self, texts: Union[str, Sequence[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        # 1) 신형 embeddings 엔드포인트 시도
        try:
            data = self._post(self._emb_endpoint, {"inputs": list(texts)})
            if isinstance(data, dict) and "embeddings" in data:
                arr = np.array(data["embeddings"], dtype=np.float32)
            else:
                arr = np.array(data, dtype=np.float32)
        except Exception:
            # 2) 구형 feature-extraction 파이프라인 폴백
            data = self._post(self._feat_endpoint, {
                "inputs": list(texts),
                "options": {"wait_for_model": True}
            })
            # 각 아이템이 [seq_len, hidden]이면 mean pooling
            embs = []
            for item in data:
                a = np.array(item, dtype=np.float32)
                if a.ndim == 2:
                    a = a.mean(axis=0)
                embs.append(a)
            arr = np.stack(embs, axis=0)

        # 공통 정규화
        arr = _l2n(arr)

        # 차원 확인(인덱스 호환성 보장)
        if arr.shape[1] != INDEX_DIM:
            raise RuntimeError(
                f"Embedding dim {arr.shape[1]} != INDEX_DIM {INDEX_DIM}. "
                f"모델({self.model_id})과 인덱스 차원이 불일치합니다."
            )
        return arr

def get_query_embedder():
    """
    환경변수로 프로바이더 선택.
    - EMBED_PROVIDER=hf-remote  → 원격 e5-large(권장)
    - EMBED_PROVIDER=hf-small-adapter 또는 USE_SPACE_ADAPTER=1 → B안(아래) 사용
    - 그 외 → (로컬 로딩) 비권장/메모리 부족 환경에서 실패 가능
    """
    provider = (os.getenv("EMBED_PROVIDER") or "hf-remote").lower()
    if provider == "hf-remote":
        model_id = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")
        token = os.getenv("HF_TOKEN")
        return HFRemoteEmbedder(model_id, token)
    elif provider == "hf-small-adapter" or os.getenv("USE_SPACE_ADAPTER") == "1":
        from .space_adapter import HFSmallLocalAdapter
        small_id = os.getenv("EMBED_MODEL_SMALL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        adapter_path = os.getenv("SPACE_ADAPTER_PATH", "insurance_app/models/space_adapter_v1.npz")
        return HFSmallLocalAdapter(small_id, adapter_path, out_dim=INDEX_DIM)
    else:
        # 로컬 무거운 모델 로딩(메모리 1GB에서는 실패 가능)
        from sentence_transformers import SentenceTransformer
        st = SentenceTransformer(os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large"))
        def _embed(txts):
            if isinstance(txts, str):
                txts = [txts]
            arr = st.encode(list(txts), convert_to_numpy=True).astype(np.float32)
            arr = _l2n(arr)
            if arr.shape[1] != INDEX_DIM:
                raise RuntimeError(f"Local embedding dim {arr.shape[1]} != INDEX_DIM {INDEX_DIM}")
            return arr
        return type("STEmbedder",(object,),{"embed":_embed})
