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
#  A) /static/insurance_portal/** → 브릿지 (HEAD/GET 모두 지원)
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

    def _open_file(self, relpath: str) -> tuple[Path | None, str | None]:
        for root in self.candidate_roots:
            f = root / relpath
            if f.exists() and f.is_file():
                ctype, _ = mimetypes.guess_type(str(f))
                return f, ctype or "application/octet-stream"
        return None, None

    def __call__(self, request):
        path = request.path
        if path.startswith(self.URL_PREFIX):
            rel = path[len(self.URL_PREFIX):]
            fpath, ctype = self._open_file(rel)
            if fpath is not None:
                # HEAD는 본문 없이 헤더만
                if request.method == "HEAD":
                    resp = HttpResponse(b"", content_type=ctype, status=200)
                    resp["Content-Length"] = "0"
                else:
                    data = fpath.read_bytes()
                    resp = HttpResponse(data, content_type=ctype, status=200)
                    resp["Content-Length"] = str(len(data))
                resp["Cache-Control"] = "max-age=300, public"
                return resp
        return self.get_response(request)


# ─────────────────────────────────────────────────────────────
#  B) HTML 응답에 번들 + FontAwesome 자동 주입 (로더 의존 제거)
# ─────────────────────────────────────────────────────────────
class PortalAutoInjectMiddleware(MiddlewareMixin):
    EXCLUDE_PREFIXES: tuple[str, ...] = ("/admin", "/static", "/media")
    MARKER = b"<!-- __PORTAL_INJECTED__ -->"

    def __init__(self, get_response):
        super().__init__(get_response)
        # 실제 아카이브 구조 기준으로 "있는 파일만" 선택
        self.css_candidates: list[str] = [
            "/static/insurance_portal/css/portal.bundle.css",
            "/static/insurance_portal/css/portal.css",
        ]
        self.js_candidates: list[str] = [
            "/static/insurance_portal/js/portal.bundle.js",
            "/static/insurance_portal/js/portal.js",
        ]
        # Font Awesome: 로컬 → CDN(jsDelivr 6.5.2) 우선순위
        self.fa_local = "/static/insurance_portal/vendor/fontawesome/css/all.min.css"
        self.fa_cdn_list = [
            "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css",
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css",
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
            if f.exists() and f.is_file():
                return True
        return False

    def _pick_first(self, urls: Iterable[str]) -> str | None:
        for u in urls:
            if u.startswith("/static/") and self._exists(u):
                return u
        return None

    def _has_link(self, html: str, substrings: Iterable[str]) -> bool:
        return any(s in html for s in substrings)

    def __call__(self, request):
        # 정적/관리/미디어는 패스
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

        # 주입은 GET/POST만 (HEAD는 변형 금지)
        if request.method not in ("GET", "POST"):
            return resp

        try:
            charset = resp.charset or "utf-8"
        except Exception:
            charset = "utf-8"

        html = resp.content.decode(charset, errors="ignore")

        # 이미 번들이 포함되어 있으면 스킵
        already_has_css = self._has_link(html, ["/portal.bundle.css", "/portal.css"])
        already_has_js  = self._has_link(html, ["/portal.bundle.js", "/portal.js"])
        already_has_fa  = self._has_link(html, ["fontawesome", "font-awesome", "all.min.css"])

        css_url = None if already_has_css else self._pick_first(self.css_candidates)
        js_url  = None if already_has_js  else self._pick_first(self.js_candidates)

        # FontAwesome: 로컬 우선, 없으면 CDN 1개 고정 주입
        fa_url: str | None = None
        if not already_has_fa:
            if self._exists(self.fa_local):
                fa_url = self.fa_local
            else:
                # CDN은 첫 후보만 주입 (6.5.2)
                fa_url = self.fa_cdn_list[0]

        if not css_url and not js_url and not fa_url:
            return resp  # 주입할 게 없으면 그대로 반환

        inject_parts = ['\n', '<!-- __PORTAL_INJECTED__ -->', '\n']
        if fa_url:
            inject_parts.append(
                f'<link rel="preconnect" href="https://cdn.jsdelivr.net">\n'
                f'<link rel="stylesheet" href="{fa_url}" crossorigin="anonymous" referrerpolicy="no-referrer" />\n'
            )
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
#  D) 지정 경로 폴백
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
