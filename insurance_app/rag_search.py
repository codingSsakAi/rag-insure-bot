from .utils.vec_compat import add_query_prefix, adapt_vector, read_index_dim
import os
from .pinecone_client import get_index
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
index = get_index()

def rag_search(query, insurer=None, top_k=5):
    q_text = add_query_prefix(query, os.getenv("EMBED_MODEL", ""))
    q_small = model.encode([q_text])[0].tolist()
    q_vec = adapt_vector(q_small, read_index_dim(index))
    res = index.query(vector=q_vec, top_k=top_k, include_metadata=True)
    matches = [m for m in res["matches"] if insurer is None or m["metadata"]["insurer"] == insurer]
    return matches
