# scripts/inspect_pinecone_metadata.py  (진단 강화판)
import os, json, random, numpy as np
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

def _matches(res):
    return getattr(res, "matches", None) or getattr(res, "data", None) or []

def _ns_map(stats):
    # SDK 객체/딕셔너리 모두 대응
    m = getattr(stats, "namespaces", None)
    if m is None and hasattr(stats, "to_dict"):
        d = stats.to_dict()
        m = d.get("namespaces")
    if m is None and isinstance(stats, dict):
        m = stats.get("namespaces")
    return m or {}

def main():
    api = os.getenv("PINECONE_API_KEY")
    idxname = os.getenv("PINECONE_INDEX_NAME")
    if not api or not idxname:
        raise SystemExit("PINECONE_API_KEY / PINECONE_INDEX_NAME 필요")

    INDEX_DIM = int(os.getenv("INDEX_DIM", "1024"))
    pc = Pinecone(api_key=api)
    idx = pc.Index(idxname)

    # 1) 인덱스 상태/네임스페이스 나열
    try:
        stats = idx.describe_index_stats()
        ns_map = _ns_map(stats)
        print("=== namespaces ===")
        print(json.dumps({k: v.get("vector_count") if isinstance(v, dict) else v for k, v in ns_map.items()}, ensure_ascii=False))
    except Exception as e:
        print("describe_index_stats error:", repr(e))

    # 2) 서로 다른 namespace 값으로 질의 시도
    probe = np.random.normal(0, 1.0, size=INDEX_DIM).astype("float32")
    probe /= (np.linalg.norm(probe) + 1e-12)
    tried = [os.getenv("NAMESPACE") or None, "", "__default__"]
    seen_ids = set()

    for ns in tried:
        try:
            res = idx.query(vector=probe.tolist(), top_k=10, include_values=False, include_metadata=True, namespace=(ns if ns not in ("", None) else ("" if ns=="" else None)))
            ms = _matches(res) or []
            print(f"\n--- query ns={repr(ns)}  matches={len(ms)} ---")
            for i, m in enumerate(ms, start=1):
                mid  = getattr(m, "id", None) or (m.get("id") if isinstance(m, dict) else None)
                meta = getattr(m, "metadata", None) or (m.get("metadata") if isinstance(m, dict) else {})
                if not mid or mid in seen_ids: 
                    continue
                seen_ids.add(mid)
                keys = list(meta.keys()) if isinstance(meta, dict) else []
                sample = {}
                if isinstance(meta, dict):
                    for k, v in meta.items():
                        if isinstance(v, str):
                            sample[k] = {"len": len(v), "preview": v[:100]}
                        elif isinstance(v, (int, float)):
                            sample[k] = v
                print(json.dumps({"i": i, "id": mid, "keys": keys, "sample": sample}, ensure_ascii=False))
            if ms:
                break
        except Exception as e:
            print(f"query error ns={repr(ns)}:", repr(e))

if __name__ == "__main__":
    main()
