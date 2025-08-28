from .utils.vec_compat import add_doc_prefix, adapt_vectors, adapt_vector, read_index_dim
import os
from sentence_transformers import SentenceTransformer
from .models import Clause
from .pinecone_client import get_index

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
index = get_index()

def upload_clauses_to_pinecone():
    clauses = Clause.objects.all()
    texts = [c.text for c in clauses]
    texts = add_doc_prefix(texts, os.getenv("EMBED_MODEL", ""))
    embeddings = model.encode(texts)
    vectors = [
        {
            "id": str(c.id),
            "values": adapt_vector(emb.tolist() if hasattr(emb, "tolist") else emb, read_index_dim(index)),
            "metadata": {
                "insurer": c.insurer, "title": c.title,
                "clause_number": c.clause_number, "page": c.page, "pdf_link": c.pdf_link
            }
        } for c, emb in zip(clauses, embeddings)
    ]
    index.upsert(vectors=vectors)
