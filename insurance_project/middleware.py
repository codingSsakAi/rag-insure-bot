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

# ?????????????????????????????????????????????????????????????
#  A) ?뺤쟻 釉뚮┸吏: /static/insurance_portal/* 瑜??ㅼ젣 議댁옱?섎뒗 ?꾨낫 寃쎈줈?먯꽌 ?쒕튃
#     (媛쒕컻/?대씪?곕뱶 ?섍꼍?먯꽌 STATICFILES ?ㅼ젙??遺덉셿?꾪빐???숈옉 蹂댁옣)
# ?????????????????????????????????????????????????????????????
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
                    # 湲곕낯媛?
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

# ?????????????????????????????????????????????????????????????
#  B) HTML ?묐떟???먮낯 ?좉?/?ы꽭 由ъ냼??**議댁옱?섎뒗 寃껊쭔** ?먮룞 二쇱엯
# ?????????????????????????????????????????????????????????????
class PortalAutoInjectMiddleware(MiddlewareMixin):
    EXCLUDE_PREFIXES: tuple[str, ...] = ("/admin", "/static", "/media")
    MARKER = b"<!-- __PORTAL_INJECTED__ -->"

    def __init__(self, get_response):
        super().__init__(get_response)
        # CSS ?꾨낫 (議댁옱?섎뒗 ??ぉ留??ｌ쓬)
        self.css_candidates: list[str] = [
            "/static/insurance_portal/css/portal.css",
            "/static/insurance_portal/portal.css",
            "/static/insurance_portal/style.css",
            "/static/insurance_portal/styles.css",
            "/static/insurance_portal/css/fab.css",
        ]
        # JS ?꾨낫 (??loader 怨꾩뿴 ?쒖쇅)
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

# ?????????????????????????????????????????????????????????????
#  C) ?덉쇅 濡쒓퉭
# ?????????????????????????????????????????????????????????????
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

# ?????????????????????????????????????????????????????????????
#  D) ?대갚 ?섏씠吏 (?뱀젙 寃쎈줈?먯꽌 ?쒗뵆由??꾨씫/?덉쇅 ??理쒖냼 HTML ?쒓났)
#     ??loader_strict ? 臾닿?, 湲곗〈 ?숈옉 ?좎?
# ?????????????????????????????????????????????????????????????
FALLBACK_PAGES: dict[str, str] = {
    "glossary": """<!doctype html><meta charset="utf-8">
    <title>?⑹뼱吏?/title><h1>?⑹뼱吏?/h1><p>?쒗뵆由우쓣 李얠쓣 ???놁뼱 理쒖냼 ?섏씠吏濡??쒖떆?⑸땲??</p>""",
    "login": """<!doctype html><meta charset="utf-8"><title>濡쒓렇??/title><h1>濡쒓렇??/h1>""",
    "signup": """<!doctype html><meta charset="utf-8"><title>?뚯썝媛??/title><h1>?뚯썝媛??/h1>""",
    "insurance_recommendation": """<!doctype html><meta charset="utf-8"><title>異붿쿇</title><div id="out"></div>""",
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

