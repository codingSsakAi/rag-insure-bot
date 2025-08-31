# insurance_app/pdf_processor.py
import os
import re
import uuid
import json
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional

import PyPDF2

from .utils.vec_compat import add_doc_prefix, adapt_vector, read_index_dim, is_e5
from .pinecone_client import get_index


# ====== 임베딩 모델 이름/환경 ======
DEFAULT_MODEL = (
    os.getenv("EMBED_MODEL")
    or os.getenv("EMBED_MODEL_SMALL")
    or "intfloat/multilingual-e5-small"
)
TOKENIZERS_PARALLELISM = os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


# ====== 무거운 모듈 지연 로딩 ======
_model_cache = {"model": None, "name": None}


def _get_encoder(model_name: str = DEFAULT_MODEL):
    """
    SentenceTransformer를 '필요할 때만' 로딩한다.
    실패(오프라인/미설치/메모리 부족)하면 None을 리턴하여 해싱 임베딩으로 폴백.
    """
    if _model_cache["model"] is not None and _model_cache["name"] == model_name:
        return _model_cache["model"]

    try:
        # 이 시점에서만 무거운 라이브러리 임포트
        from sentence_transformers import SentenceTransformer  # type: ignore

        # 너무 큰 모델 쓰지 않도록 사용자 환경 변수 우선, 기본은 small
        encoder = SentenceTransformer(
            model_name,
            device=os.getenv("SENTENCE_DEVICE", "cpu"),
        )
        # torch 스레드 줄이기(메모리/과부하 방지)
        try:
            import torch  # type: ignore

            torch.set_num_threads(max(1, int(os.getenv("TORCH_NUM_THREADS", "1"))))
        except Exception:
            pass

        _model_cache["model"] = encoder
        _model_cache["name"] = model_name
        return encoder
    except Exception as e:
        # 로드 실패하면 캐시는 None 유지 -> 폴백 경로 사용
        print(f"[pdf_processor] Encoder load failed -> fallback to hashing: {e}")
        return None


# ====== 경량 해싱 임베딩 폴백 ======
def _hash_embed(text: str, dim: int = 384) -> List[float]:
    """
    외부 모델 없이 동작하는 매우 가벼운 임베딩(Deterministic).
    - 토큰을 md5 해싱해서 차원에 누적 (sign 포함)
    - 마지막에 L2 정규화
    """
    vec = [0.0] * dim
    for tok in re.findall(r"\w+", (text or "").lower()):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 1) & 1) else -1.0
        vec[idx] += sign

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class EnhancedPDFProcessor:
    """
    기존 퍼블릭 API를 그대로 유지:
      - extract_text_from_pdf
      - smart_chunk_text / split_long_article / general_chunk_text
      - embed_text
      - upload_chunks_to_pinecone
      - process_company_documents / process_all_companies
      - search_company_clauses / get_company_statistics
      - determine_document_type
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or DEFAULT_MODEL
        self.index = get_index()  # Pinecone 인덱스는 기존대로 즉시 준비
        self.documents_path = Path(__file__).parent / "documents"
        self.insurance_companies = [
            "삼성화재",
            "현대해상",
            "메리츠화재",
            "DB손해보험",
            "롯데손해보험",
            "하나손해보험",
            "흥국화재",
            "MG손해보험",
            "캐롯손해보험",
        ]

    # ---------- PDF 텍스트 추출 ----------
    def extract_text_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """PDF에서 텍스트 추출 (간단/안정)"""
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n\n=== 페이지 {page_num + 1} ===\n{page_text}"
        except Exception as e:
            print(f"[pdf_processor] PDF read error ({pdf_path}): {e}")
            return None
        return text or None

    # ---------- 스마트 청킹 ----------
    def smart_chunk_text(
        self, text: str, company_name: str, document_type: str
    ) -> List[Dict]:
        """보험 약관에 특화된 스마트 청킹"""
        if not text:
            return []

        chunks: List[Dict] = []

        # 조문별로 분할 (제X조, 제X장, 제X절 등)
        article_pattern = r"(제\s*\d+\s*[조장절].*?)(?=제\s*\d+\s*[조장절]|$)"
        articles = re.findall(article_pattern, text, re.DOTALL)

        if not articles:
            # 조문이 없는 경우 일반적인 청킹
            return self.general_chunk_text(text, company_name, document_type)

        for i, article in enumerate(articles):
            article = article.strip()
            if len(article) < 50:  # 너무 짧은 조문은 스킵
                continue

            # 조문 제목 추출
            title_match = re.match(r"(제\s*\d+\s*[조장절][^:\n]*)", article)
            article_title = title_match.group(1) if title_match else f"조문 {i + 1}"

            # 긴 조문은 소절로 나누기
            if len(article) > 1000:
                sub_chunks = self.split_long_article(article, article_title)
                for ch in sub_chunks:
                    ch["company"] = company_name
                    ch["document_type"] = document_type
                chunks.extend(sub_chunks)
            else:
                chunks.append(
                    {
                        "text": article,
                        "title": article_title,
                        "company": company_name,
                        "document_type": document_type,
                        "chunk_type": "article",
                        "length": len(article),
                    }
                )

        return chunks

    def split_long_article(self, article: str, article_title: str) -> List[Dict]:
        """긴 조문을 소절로 분할"""
        chunks: List[Dict] = []

        # 항목별로 분할 (1., 2., 가., 나., ①, ② ...)
        item_pattern = r"([1-9]\.|[가-힣]\.|①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩)"
        parts = re.split(item_pattern, article)

        current_chunk = parts[0] if parts else article

        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                item_marker = parts[i]
                item_content = parts[i + 1]

                if len(current_chunk) > 800:
                    chunks.append(
                        {
                            "text": current_chunk.strip(),
                            "title": article_title,
                            "company": "",
                            "document_type": "",
                            "chunk_type": "article_part",
                            "length": len(current_chunk),
                        }
                    )
                    current_chunk = f"{article_title}\n{item_marker}{item_content}"
                else:
                    current_chunk += f"{item_marker}{item_content}"

        if current_chunk.strip():
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "title": article_title,
                    "company": "",
                    "document_type": "",
                    "chunk_type": "article_part",
                    "length": len(current_chunk),
                }
            )

        return chunks

    def general_chunk_text(
        self, text: str, company_name: str, document_type: str
    ) -> List[Dict]:
        """일반적인 텍스트 청킹"""
        chunks: List[Dict] = []
        sentences = re.split(r"[.!?]\s+", text)

        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) > 800 and current_chunk:
                chunks.append(
                    {
                        "text": current_chunk.strip(),
                        "title": f"내용 {len(chunks) + 1}",
                        "company": company_name,
                        "document_type": document_type,
                        "chunk_type": "general",
                        "length": len(current_chunk),
                    }
                )
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence

        if current_chunk.strip():
            chunks.append(
                {
                    "text": current_chunk.strip(),
                    "title": f"내용 {len(chunks) + 1}",
                    "company": company_name,
                    "document_type": document_type,
                    "chunk_type": "general",
                    "length": len(current_chunk),
                }
            )

        return chunks

    # ---------- 임베딩 ----------
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        텍스트를 벡터로 임베딩.
        - 우선 SentenceTransformer 시도(지연 로딩)
        - 실패 시 해싱 임베딩 폴백
        - 마지막에 Pinecone 인덱스 차원에 맞게 adapt
        """
        try:
            target_dim = read_index_dim(self.index) or 384
        except Exception:
            target_dim = 384

        try:
            doc_texts = add_doc_prefix([text], self.model_name)
            encoder = _get_encoder(self.model_name)
            if encoder is not None:
                vec = encoder.encode(
                    doc_texts[0],
                    normalize_embeddings=False,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                base = vec.tolist()
            else:
                base = _hash_embed(doc_texts[0], dim=min(target_dim, 384))
        except Exception as e:
            print(f"[pdf_processor] embed error -> fallback hashing: {e}")
            base = _hash_embed(text, dim=min(target_dim, 384))

        try:
            adapted = adapt_vector(base, target_dim)
            return adapted
        except Exception as e:
            print(f"[pdf_processor] adapt_vector error: {e}")
            return None

    # ---------- Pinecone 업로드 ----------
    def upload_chunks_to_pinecone(
        self, chunks: List[Dict], namespace: str = "insurance"
    ) -> bool:
        """청크들을 Pinecone에 업로드"""
        if not chunks:
            return False

        vectors = []
        successful_chunks = 0

        for chunk in chunks:
            emb = self.embed_text(chunk["text"])
            if emb:
                vector_id = f"{chunk.get('company','')}_{chunk.get('document_type','')}_{str(uuid.uuid4())[:8]}"
                vectors.append(
                    {
                        "id": vector_id,
                        "values": emb,
                        "metadata": {
                            "text": chunk["text"][:1000],
                            "full_text": chunk["text"],
                            "title": chunk.get("title", ""),
                            "company": chunk.get("company", ""),
                            "document_type": chunk.get("document_type", ""),
                            "chunk_type": chunk.get("chunk_type", ""),
                            "length": chunk.get("length", 0),
                            "file": chunk.get("file", ""),
                            "page": chunk.get("page", ""),
                        },
                    }
                )
                successful_chunks += 1

        if not vectors:
            return False

        try:
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
                print(f"[pdf_processor] Upsert batch {i//batch_size + 1}: {len(batch)}")

            print(f"✅ {successful_chunks}개 청크 업로드 완료 (ns={namespace})")
            return True
        except Exception as e:
            print(f"[pdf_processor] Pinecone upsert error: {e}")
            return False

    # ---------- 회사별/전체 처리 ----------
    def process_company_documents(self, company_name: str) -> bool:
        """특정 보험사의 모든 문서 처리"""
        company_path = self.documents_path / company_name
        if not company_path.exists():
            print(f"❌ {company_name} 폴더 없음: {company_path}")
            return False

        pdf_files = list(company_path.glob("*.pdf"))
        if not pdf_files:
            print(f"❌ {company_name} 폴더에 PDF 없음")
            return False

        print(f"📂 {company_name} 처리 시작: {len(pdf_files)}개 PDF")
        total_chunks = 0
        processed_files = 0

        for pdf_file in pdf_files:
            print(f"  📄 처리: {pdf_file.name}")
            document_type = self.determine_document_type(pdf_file.name)

            text = self.extract_text_from_pdf(pdf_file)
            if not text:
                print(f"    ❌ 텍스트 추출 실패: {pdf_file.name}")
                continue

            print(f"    📝 추출 텍스트: {len(text):,} chars")
            rel_file = f"{company_name}/{pdf_file.name}"

            chunks = self.smart_chunk_text(text, company_name, document_type)
            print(f"    🔪 청크 수: {len(chunks)}")

            for ch in chunks:
                ch["company"] = company_name
                ch["document_type"] = document_type
                ch["file"] = rel_file

            if self.upload_chunks_to_pinecone(
                chunks, namespace=f"insurance_{company_name.replace(' ', '_')}"
            ):
                total_chunks += len(chunks)
                processed_files += 1
                print(f"    ✅ 업로드 완료: {pdf_file.name}")
            else:
                print(f"    ❌ 업로드 실패: {pdf_file.name}")

        print(
            f"🎉 {company_name} 완료: {processed_files}/{len(pdf_files)} 파일, 총 {total_chunks} 청크"
        )
        return processed_files > 0

    def determine_document_type(self, filename: str) -> str:
        """파일명으로 문서 타입 결정"""
        fn = filename.lower()
        # 한글 키워드 판단은 원문 문자열로도 처리
        if "약관" in filename:
            if "특약" in filename:
                return "특약약관"
            elif "자동차" in filename:
                return "자동차보험약관"
            else:
                return "보험약관"
        if "상품설명서" in filename:
            return "상품설명서"
        if "안내서" in filename:
            return "안내서"
        # 영문/소문자 케이스
        if "clause" in fn:
            return "보험약관"
        if "guide" in fn:
            return "안내서"
        return "기타문서"

    def process_all_companies(self) -> Dict[str, bool]:
        """모든 보험사 문서 처리"""
        results: Dict[str, bool] = {}
        print("🚀 모든 보험사 문서 처리 시작")
        for company in self.insurance_companies:
            print(f"\n{'=' * 50}\n처리 대상: {company}\n{'=' * 50}")
            ok = self.process_company_documents(company)
            results[company] = ok
            print(f"{'✅ 성공' if ok else '❌ 실패'}: {company}")

        success = sum(1 for v in results.values() if v)
        print(f"\n{'=' * 50}\n📊 전체 결과: {success}/{len(results)} 성공\n{'=' * 50}")
        for c, v in results.items():
            print(f"{c}: {'✅ 성공' if v else '❌ 실패'}")
        return results

    # ---------- 검색 ----------
    def search_company_clauses(
        self, query: str, company_name: Optional[str] = None, top_k: int = 5
    ) -> List[Dict]:
        """특정 보험사나 전체에서 약관 검색"""
        query_emb = self.embed_text(query)
        if not query_emb:
            return []

        try:
            namespace = (
                f"insurance_{company_name.replace(' ', '_')}"
                if company_name
                else "insurance"
            )
            res = self.index.query(
                vector=query_emb,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
                filter={"company": company_name} if company_name else None,
            )

            hits = []
            for match in res.get("matches", []):
                md = match.get("metadata", {}) or {}
                hits.append(
                    {
                        "text": md.get("full_text", md.get("text", "")),
                        "title": md.get("title", ""),
                        "company": md.get("company", ""),
                        "document_type": md.get("document_type", ""),
                        "chunk_type": md.get("chunk_type", ""),
                        "score": match.get("score", 0),
                        "length": md.get("length", 0),
                    }
                )
            return hits
        except Exception as e:
            print(f"[pdf_processor] search error: {e}")
            return []

    # ---------- 통계 ----------
    def get_company_statistics(self) -> Dict[str, Any]:
        """각 보험사별 문서 통계"""
        stats: Dict[str, Any] = {}
        try:
            index_stats = self.index.describe_index_stats() or {}
            ns = (index_stats.get("namespaces", {}) or {})
        except Exception as e:
            print(f"[pdf_processor] describe_index_stats error: {e}")
            ns = {}

        for company in self.insurance_companies:
            namespace = f"insurance_{company.replace(' ', '_')}"
            try:
                comp = ns.get(namespace, {}) or {}
                stats[company] = {
                    "vector_count": comp.get("vector_count", 0),
                    "has_documents": (comp.get("vector_count", 0) > 0),
                }
            except Exception as e:
                stats[company] = {
                    "vector_count": 0,
                    "has_documents": False,
                    "error": str(e),
                }
        return stats


# ---------- 기존 함수들과의 호환성 래퍼 ----------
def search_similar_clauses(
    query: str, company_name: Optional[str] = None, top_k: int = 5
) -> List[Dict]:
    processor = EnhancedPDFProcessor()
    return processor.search_company_clauses(query, company_name, top_k)


def process_pdf_to_pinecone(
    pdf_path: str, company_name: str, document_type: Optional[str] = None
) -> bool:
    processor = EnhancedPDFProcessor()
    if not document_type:
        document_type = processor.determine_document_type(Path(pdf_path).name)

    text = processor.extract_text_from_pdf(Path(pdf_path))
    if not text:
        return False

    chunks = processor.smart_chunk_text(text, company_name, document_type)
    for ch in chunks:
        ch["company"] = company_name
        ch["document_type"] = document_type

    return processor.upload_chunks_to_pinecone(chunks)


def initialize_insurance_documents():
    """모든 보험사 문서를 초기화하는 함수"""
    processor = EnhancedPDFProcessor()
    return processor.process_all_companies()
