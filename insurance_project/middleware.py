# insurance_project/middleware.py
from __future__ import annotations
import mimetypes
from pathlib import Path
from typing import Callable
from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse

class PortalStaticBridgeMiddleware:
    """
    /static/insurance_portal/** 요청만 디스크에서 직접 찾아 올바른 MIME으로 반환.
    기존 기능은 그대로 유지.
    우선순위:
      1) <BASE_DIR>/0826-5/insurance_portal/static/insurance_portal
      2) <BASE_DIR>/insurance_app/static/insurance_portal
    """

    URL_PREFIX = "/static/insurance_portal/"

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        base = Path(settings.BASE_DIR).resolve()
        self.roots = [
            (base / "0826-5" / "insurance_portal" / "static" / "insurance_portal").resolve(),
            (base / "insurance_app" / "static" / "insurance_portal").resolve(),
        ]

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path
        if not path.startswith(self.URL_PREFIX):
            return self.get_response(request)

        rel_path = path[len(self.URL_PREFIX):].lstrip("/")
        for root in self.roots:
            candidate = (root / rel_path).resolve()
            if not str(candidate).startswith(str(root)):
                continue
            if candidate.is_file():
                ctype, _ = mimetypes.guess_type(str(candidate))
                resp = FileResponse(open(candidate, "rb"), content_type=ctype or "application/octet-stream")
                try:
                    resp["Content-Length"] = candidate.stat().st_size
                except Exception:
                    pass
                resp["Cache-Control"] = "public, max-age=3600"
                return resp
        return HttpResponse(status=404)
