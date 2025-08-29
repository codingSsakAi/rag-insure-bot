from pathlib import Path
from typing import List
from django.conf import settings
from django.http import Http404
from django.views.static import serve as static_serve

# 후보 정적 루트 디렉터리들 (존재 여부는 런타임에 확인)
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
    rel_path = (rel_path or "").lstrip("/").replace("\\", "/")
    parts = [p for p in rel_path.split("/") if p not in ("", ".", "..")]
    return "/".join(parts)

def _variants(rel_path: str) -> List[str]:
    rel_path = _sanitize(rel_path)
    out = [rel_path]
    if not rel_path.startswith("insurance_portal/"):
        out.append("insurance_portal/" + rel_path)
    else:
        out.append(rel_path[len("insurance_portal/"):])
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
    for candidate_rel in _variants(path):
        for root in _iter_existing_roots():
            candidate_abs = root / candidate_rel
            if candidate_abs.exists() and candidate_abs.is_file():
                return static_serve(request, candidate_rel, document_root=str(root))
    raise Http404("static asset not found")

def serve_favicon(request):
    names = ["favicon.ico", "insurance_portal/favicon.ico", "images/favicon.ico"]
    for root in _iter_existing_roots():
        for name in names:
            candidate = root / name
            if candidate.exists() and candidate.is_file():
                return static_serve(request, name, document_root=str(root))
    raise Http404("favicon not found")
