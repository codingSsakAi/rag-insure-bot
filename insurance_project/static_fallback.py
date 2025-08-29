from pathlib import Path
from typing import List
from django.conf import settings
from django.http import Http404
from django.views.static import serve as static_serve

# 후보 정적 루트 디렉터리들 (존재 여부는 런타임에 확인)
# 아카이브/루트/앱 각각의 static 및 중첩 디렉터리까지 폭넓게 커버
_CANDIDATE_DIRS: List[Path] = [
    settings.BASE_DIR / "insurance_portal" / "static" / "insurance_portal",
    settings.BASE_DIR / "insurance_portal" / "static",
    settings.BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
    settings.BASE_DIR / "0826-5" / "insurance_portal" / "static",
    settings.BASE_DIR / "insurance_app" / "static" / "insurance_portal",
    settings.BASE_DIR / "insurance_app" / "static",
    settings.BASE_DIR / "accident_project" / "static",
]

def _sanitize(rel_path: str) -> str:
    """경로 정규화 및 상위 디렉터리 접근 차단"""
    rel_path = (rel_path or "").lstrip("/").replace("\\", "/")
    parts = [p for p in rel_path.split("/") if p not in ("", ".", "..")]
    return "/".join(parts)

def _variants(rel_path: str) -> List[str]:
    """
    요청 경로에 대해 다음 시나리오를 모두 시도:
      - 그대로
      - insurance_portal/ 접두어 추가
      - insurance_portal/ 접두어 제거
    """
    rel_path = _sanitize(rel_path)
    out = [rel_path]
    if not rel_path.startswith("insurance_portal/"):
        out.append("insurance_portal/" + rel_path)
    else:
        out.append(rel_path[len("insurance_portal/"):])
    # 중복 제거, 순서 유지
    seen, uniq = set(), []
    for v in out:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq

def _iter_existing_roots() -> List[Path]:
    uniq, out = set(), []
    for d in _CANDIDATE_DIRS:
        if d.exists() and d.is_dir():
            if d not in uniq:
                uniq.add(d)
                out.append(d)
    return out

def serve_static_fallback(request, path: str):
    """
    /static/<path> 로 들어온 요청을 다중 루트에서 탐색하여 서빙.
    DEBUG 여부와 상관없이 동작(runserver/프리티어 환경 대응)
    """
    for candidate_rel in _variants(path):
        for root in _iter_existing_roots():
            candidate_abs = root / candidate_rel
            if candidate_abs.exists() and candidate_abs.is_file():
                return static_serve(request, candidate_rel, document_root=str(root))
    raise Http404("static asset not found")

def serve_favicon(request):
    """ /favicon.ico 요청 처리: 후보 루트에서 favicon.ico가 있으면 서빙 """
    names = ["favicon.ico", "insurance_portal/favicon.ico", "images/favicon.ico"]
    for root in _iter_existing_roots():
        for name in names:
            candidate = root / name
            if candidate.exists() and candidate.is_file():
                return static_serve(request, name, document_root=str(root))
    raise Http404("favicon not found")
