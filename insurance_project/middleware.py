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
#  A) /static/insurance_portal/** → 0826-5 … 브릿지
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
                return data, ctype or "application/octet-stream"
        return None, None

    def __call__(self, request):
        path = request.path
        if path.startswith(self.URL_PREFIX):
            rel = path[len(self.URL_PREFIX):]
            data, ctype = self._try_open(rel)
            if data is not None:
                resp = HttpResponse(data, content_type=ctype)
                resp["Cache-Control"] = "max-age=300, public"
                return resp
        return self.get_response(request)


# ─────────────────────────────────────────────────────────────
#  B) HTML 응답에 원본 토글 CSS/JS 자동 주입
# ─────────────────────────────────────────────────────────────
class PortalAutoInjectMiddleware(MiddlewareMixin):
    EXCLUDE_PREFIXES: tuple[str, ...] = ("/admin", "/static", "/media")
    MARKER = b"<!-- __PORTAL_INJECTED__ -->"

    def __init__(self, get_response):
        super().__init__(get_response)
        self.css_candidates: list[str] = [
            "/static/insurance_portal/css/portal.css",
            "/static/insurance_portal/portal.css",
            "/static/insurance_portal/style.css",
            "/static/insurance_portal/styles.css",
            "/static/insurance_portal/css/fab.css",
        ]
        self.js_candidates: list[str] = [
            "/static/insurance_portal/loader_strict.js",
            "/static/insurance_portal/loader.js",
            "/static/insurance_portal/portal.js",
            "/static/insurance_portal/js/portal.js",
            "/static/insurance_portal/js/navigation_handler.js",
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

    def _pick_first(self, urls: Iterable[str]) -> str | None:
        for u in urls:
            if self._exists(u):
                return u
        return None

    def __call__(self, request):
        for p in self.EXCLUDE_PREFIXES:
            if request.path.startswith(p):
                return self.get_response(request)

        resp = self.get_response(request)

        ctype = resp.headers.get("Content-Type", "")
        if resp.status_code != 200 or "text/html" not in ctype:
            return resp
        if not hasattr(resp, "content"):
            return resp
        if self.MARKER in resp.content:
            return resp

        css_url = self._pick_first(self.css_candidates)
        js_url  = self._pick_first(self.js_candidates)
        if not css_url and not js_url:
            return resp

        try:
            charset = resp.charset or "utf-8"
        except Exception:
            charset = "utf-8"

        html = resp.content.decode(charset, errors="ignore")
        inject_parts = ['\n', '<!-- __PORTAL_INJECTED__ -->', '\n']
        if css_url:
            inject_parts.append(f'<link rel="stylesheet" href="{css_url}?v=1" />\n')
        if js_url:
            inject_parts.append(f'<script src="{js_url}?v=1" defer></script>\n')

        payload = "".join(inject_parts)
        if "</body>" in html:
            html = html.replace("</body>", payload + "</body>")
        else:
            html += payload

        resp.content = html.encode(charset)
        if resp.has_header("Content-Length"):
            resp.headers["Content-Length"] = str(len(resp.content))
        return resp


# ─────────────────────────────────────────────────────────────
#  C) 예외 로그 강화
# ─────────────────────────────────────────────────────────────
class ExceptionLoggingMiddleware(MiddlewareMixin):
    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error("Unhandled exception at %s: %s", request.path, e)
            traceback.print_exc()
            raise


# ─────────────────────────────────────────────────────────────
#  D) 폴백: 지정된 경로에서는 어떤 예외든 최소 HTML로 200 보장
#     (정상 템플릿/뷰가 있으면 개입하지 않음)
# ─────────────────────────────────────────────────────────────
FALLBACK_PAGES: dict[str, str] = {
    "glossary": """<!doctype html><meta charset="utf-8">
    <title>용어집</title><h1>용어집</h1><p>템플릿을 찾을 수 없어 최소 페이지로 표시합니다.</p>""",
    "login": """<!doctype html><meta charset="utf-8">
    <title>로그인</title><h1>로그인</h1>
    <form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="">
    <label>아이디 <input name="username"></label><br>
    <label>비밀번호 <input type="password" name="password"></label><br>
    <button type="submit">로그인</button></form>""",
    "signup": """<!doctype html><meta charset="utf-8">
    <title>회원가입</title><h1>회원가입</h1>
    <form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="">
    <label>아이디 <input name="username"></label><br>
    <label>비밀번호 <input type="password" name="password1"></label><br>
    <label>비밀번호 확인 <input type="password" name="password2"></label><br>
    <button type="submit">가입</button></form>""",
    "insurance_recommendation": """<!doctype html><meta charset="utf-8">
    <title>AI 약관 검색</title><h1>AI 약관 검색</h1>
    <form id="f"><input id="q" placeholder="질문을 입력하세요">
    <button>검색</button></form><pre id="out"></pre>
    <script>
    document.getElementById('f').onsubmit = async (e) => {
      e.preventDefault();
      const r = await fetch('/insurance-recommendation/', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({query: document.getElementById('q').value})
      });
      try { const j = await r.json(); document.getElementById('out').textContent = JSON.stringify(j, null, 2); }
      catch (err) { document.getElementById('out').textContent = '응답 형식 오류'; }
    };
    </script>""",
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
    """
    - TemplateDoesNotExist는 물론, 지정 경로의 모든 예외에 대해 폴백 HTML 제공.
    - 정상 템플릿/뷰가 있으면 절대 개입하지 않음.
    """
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
