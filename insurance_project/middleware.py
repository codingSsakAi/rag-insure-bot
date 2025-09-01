# insurance_project/middleware.py
from __future__ import annotations

import mimetypes
import logging
import traceback
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.template import TemplateDoesNotExist

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
#  A) 정적 브릿지: /static/insurance_portal/* 를 실제 존재하는 후보 경로에서 서빙
#     (개발/클라우드 환경에서 STATICFILES 설정이 불완전해도 동작 보장)
# ─────────────────────────────────────────────────────────────
class PortalStaticBridgeMiddleware(MiddlewareMixin):
    URL_PREFIX = "/static/insurance_portal/"

    def __init__(self, get_response):
        super().__init__(get_response)
        base: Path = settings.BASE_DIR
        self.candidate_roots: list[Path] = [
            base / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
            base / "insurance_portal" / "static" / "insurance_portal",
            base / "insurance_app" / "static" / "insurance_portal",
        ]

    def _try_open(self, relpath: str) -> tuple[bytes | None, str | None]:
        for root in self.candidate_roots:
            f = root / relpath
            if f.exists() and f.is_file():
                data = f.read_bytes()
                ctype, _ = mimetypes.guess_type(str(f))
                if not ctype:
                    # 기본값
                    if f.suffix in {".js", ".mjs"}:
                        ctype = "application/javascript; charset=utf-8"
                    elif f.suffix == ".css":
                        ctype = "text/css; charset=utf-8"
                    else:
                        ctype = "application/octet-stream"
                return data, ctype
        return None, None

    def process_request(self, request):
        path = (request.path or "")
        if not path.startswith(self.URL_PREFIX):
            return None
        rel = path[len(self.URL_PREFIX):]
        data, ctype = self._try_open(rel)
        if data is None:
            return None
        return HttpResponse(data, content_type=ctype, status=200)

# ─────────────────────────────────────────────────────────────
#  B) HTML 응답에 원본 토글/포털 리소스 **존재하는 것만** 자동 주입
#     ⚠️ noisy fallback의 원인인 loader_strict.js / loader.js 는 주입 대상에서 제외
# ─────────────────────────────────────────────────────────────
class PortalAutoInjectMiddleware(MiddlewareMixin):
    EXCLUDE_PREFIXES: tuple[str, ...] = ("/admin", "/static", "/media")
    MARKER = b"<!-- __PORTAL_INJECTED__ -->"

    def __init__(self, get_response):
        super().__init__(get_response)
        # CSS 후보 (존재하는 항목만 넣음)
        self.css_candidates: list[str] = [
            "/static/insurance_portal/css/portal.css",
            "/static/insurance_portal/portal.css",
            "/static/insurance_portal/style.css",
            "/static/insurance_portal/styles.css",
            "/static/insurance_portal/css/fab.css",
        ]
        # JS 후보 (※ loader 계열 제외)
        self.js_candidates: list[str] = [
            "/static/insurance_portal/js/portal.js",
            "/static/insurance_portal/js/navigation_handler.js",
            "/static/insurance_portal/js/fab-controller.js",
            "/static/insurance_portal/js/guide.js",
            "/static/insurance_portal/js/knowhow.js",
            "/static/insurance_portal/js/claim_knowledge.js",
            "/static/insurance_portal/js/chatbot.js",
            "/static/insurance_portal/js/fault_answer.js",
        ]

    def _exists(self, url_path: str) -> bool:
        prefix = "/static/insurance_portal/"
        if not url_path.startswith(prefix):
            return False
        rel = url_path[len(prefix):]
        for root in [
            settings.BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
            settings.BASE_DIR / "insurance_portal" / "static" / "insurance_portal",
            settings.BASE_DIR / "insurance_app" / "static" / "insurance_portal",
        ]:
            f = root / rel
            if f.exists():
                return True
        return False

    def _should_skip(self, request) -> bool:
        path = (request.path or "")
        return path.startswith(self.EXCLUDE_PREFIXES)

    def process_response(self, request, response):
        try:
            if self._should_skip(request):
                return response

            ctype = response.get("Content-Type", "") or ""
            if response.status_code != 200 or "text/html" not in ctype.lower():
                return response
            if getattr(response, "streaming", False):
                return response

            body: bytes = response.content
            if self.MARKER in body:
                return response

            try:
                body_str = body.decode(response.charset or "utf-8", errors="ignore")
            except Exception:
                return response

            idx = body_str.lower().rfind("</body>")
            if idx == -1:
                return response

            css_tags: list[str] = []
            for href in self.css_candidates:
                if self._exists(href):
                    css_tags.append(f'<link rel="stylesheet" href="{href}">')

            js_tags: list[str] = []
            for src in self.js_candidates:
                if self._exists(src):
                    js_tags.append(f'<script src="{src}"></script>')

            if not css_tags and not js_tags:
                return response

            snippet = "\n".join(css_tags + js_tags) + "\n" + self.MARKER.decode()
            new_body = body_str[:idx] + snippet + body_str[idx:]
            response.content = new_body.encode(response.charset or "utf-8")
            if response.has_header("Content-Length"):
                response["Content-Length"] = str(len(response.content))
            return response
        except Exception as e:
            logger.error("AutoInject error at %s: %s", getattr(request, "path", "?"), e)
            return response

# ─────────────────────────────────────────────────────────────
#  C) 예외 로깅
# ─────────────────────────────────────────────────────────────
class ExceptionLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error("Unhandled exception at %s: %s", request.path, e)
            traceback.print_exc()
            raise

# ─────────────────────────────────────────────────────────────
#  D) 폴백 페이지 (특정 경로에서 템플릿 누락/예외 시 최소 HTML 제공)
#     ※ loader_strict 와 무관, 기존 동작 유지
# ─────────────────────────────────────────────────────────────
FALLBACK_PAGES: dict[str, str] = {
    "glossary": """<!doctype html><meta charset="utf-8">
    <title>용어집</title><h1>용어집</h1><p>템플릿을 찾을 수 없어 최소 페이지로 표시합니다.</p>""",
    "login": """<!doctype html><meta charset="utf-8"><title>로그인</title><h1>로그인</h1>""",
    "signup": """<!doctype html><meta charset="utf-8"><title>회원가입</title><h1>회원가입</h1>""",
    "insurance_recommendation": """<!doctype html><meta charset="utf-8"><title>추천</title><div id="out"></div>""",
}

def _fallback_key_from_path(path: str) -> str | None:
    if path.startswith("/glossary"):
        return "glossary"
    if path.startswith("/login"):
        return "login"
    if path.startswith("/signup"):
        return "signup"
    if path.startswith("/insurance-recommendation"):
        return "insurance_recommendation"
    return None

class TemplateFallbackMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)

    def __call__(self, request):
        try:
            return self.get_response(request)
        except TemplateDoesNotExist as e:
            key = _fallback_key_from_path(request.path or "")
            if key and key in FALLBACK_PAGES:
                logger.warning("Template missing for %s (%s). Serving fallback page.", request.path, e)
                return HttpResponse(FALLBACK_PAGES[key], content_type="text/html; charset=utf-8", status=200)
            raise
        except Exception as e:
            key = _fallback_key_from_path(request.path or "")
            if key and key in FALLBACK_PAGES:
                logger.error("Exception at %s: %s. Serving fallback page.", request.path, e)
                return HttpResponse(FALLBACK_PAGES[key], content_type="text/html; charset=utf-8", status=200)
            raise
