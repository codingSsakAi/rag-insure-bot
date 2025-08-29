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
#  A) /static/insurance_portal/**  →  0826-5/insurance_portal/static/** 브릿지
#     (정적 경로 등록이 안 되어 있어도 원본 파일을 서빙)
# ─────────────────────────────────────────────────────────────
class PortalStaticBridgeMiddleware(MiddlewareMixin):
    """
    /static/insurance_portal/** 요청을 0826-5 폴더(또는 후보 경로)에서 직접 읽어 반환.
    다른 정적 파일은 건드리지 않음.
    """
    URL_PREFIX = "/static/insurance_portal/"

    def __init__(self, get_response):
        super().__init__(get_response)
        # 후보 루트(우선순위: 0826-5 → 프로젝트 루트 → fallback)
        base: Path = settings.BASE_DIR
        self.candidate_roots: list[Path] = [
            base / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
            base / "insurance_portal" / "static" / "insurance_portal",
            base / "insurance_app" / "static" / "insurance_portal",  # 혹시 기존에 원본이 여기 있을 수도 있음
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
            rel = path[len(self.URL_PREFIX):]  # 'js/...' 또는 'css/...' 등
            data, ctype = self._try_open(rel)
            if data is not None:
                resp = HttpResponse(data, content_type=ctype)
                # 간단 캐시 헤더(개발/프리티어 환경)
                resp["Cache-Control"] = "max-age=300, public"
                return resp
        return self.get_response(request)


# ─────────────────────────────────────────────────────────────
#  B) HTML 응답에 원본 토글(CSS/JS) 자동 주입
#     - 템플릿을 수정하지 않아도 됨
# ─────────────────────────────────────────────────────────────
class PortalAutoInjectMiddleware(MiddlewareMixin):
    """
    text/html 응답 본문에 원본 토글 CSS/JS를 자동 삽입.
    - admin/static/media 경로 등은 제외
    - 이미 삽입돼 있으면 재삽입하지 않음
    """
    EXCLUDE_PREFIXES: tuple[str, ...] = ("/admin", "/static", "/media")
    MARKER = b"<!-- __PORTAL_INJECTED__ -->"

    def __init__(self, get_response):
        super().__init__(get_response)
        # 존재 확인용 파일 후보 (있을 때만 링크 주입)
        self.css_candidates: list[str] = [
            "/static/insurance_portal/css/portal.css",
            "/static/insurance_portal/portal.css",
            "/static/insurance_portal/style.css",
            "/static/insurance_portal/styles.css",
            "/static/insurance_portal/css/fab.css",  # 실제 배포본에 존재 확인됨
        ]
        self.js_candidates: list[str] = [
            "/static/insurance_portal/loader_strict.js",  # 우리가 쓰던 로더 (있으면 베스트)
            "/static/insurance_portal/loader.js",
            "/static/insurance_portal/portal.js",
            "/static/insurance_portal/js/portal.js",      # 아카이브에서 확인된 경로
            "/static/insurance_portal/js/navigation_handler.js",  # 실제 배포본에 존재 확인됨
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
        # 제외 경로
        for p in self.EXCLUDE_PREFIXES:
            if request.path.startswith(p):
                return self.get_response(request)

        resp = self.get_response(request)

        # HTML 200 OK 만 대상으로
        ctype = resp.headers.get("Content-Type", "")
        if resp.status_code != 200 or "text/html" not in ctype:
            return resp
        if not hasattr(resp, "content"):
            return resp
        # 이미 삽입됐다면 스킵
        if self.MARKER in resp.content:
            return resp

        # 주입할 리소스 결정(실존하는 것만)
        css_url = self._pick_first(self.css_candidates)
        js_url  = self._pick_first(self.js_candidates)

        if not css_url and not js_url:
            return resp  # 넣을 게 없으면 스킵

        # body 닫히기 직전에 삽입
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
            html = html + payload

        resp.content = html.encode(charset)
        # 길이 갱신
        if resp.has_header("Content-Length"):
            resp.headers["Content-Length"] = str(len(resp.content))
        return resp


# ─────────────────────────────────────────────────────────────
#  C) 예외 로그 강화: 어디서 500이 나는지 스택트레이스 보장
# ─────────────────────────────────────────────────────────────
class ExceptionLoggingMiddleware(MiddlewareMixin):
    """
    모든 예외를 서버 로그에 스택트레이스로 남김.
    기존 동작에는 영향 주지 않고, 디버깅만 돕는다.
    """
    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error("Unhandled exception at %s: %s", request.path, e)
            traceback.print_exc()
            raise


# ─────────────────────────────────────────────────────────────
#  D) 템플릿 폴백: 템플릿이 없어서 500일 때만 최소 페이지 반환
#    (정상 템플릿 존재하면 절대 개입하지 않음)
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
      const j = await r.json(); document.getElementById('out').textContent = JSON.stringify(j, null, 2);
    };
    </script>""",
}

class TemplateFallbackMiddleware(MiddlewareMixin):
    """
    TemplateDoesNotExist 발생시에만 경로별 최소 폴백 HTML을 반환.
    정상 템플릿이 있으면 절대 개입하지 않음.
    """
    def __call__(self, request):
        try:
            return self.get_response(request)
        except TemplateDoesNotExist as e:
            path = request.path or ""
            key = None
            if path.startswith("/glossary"):
                key = "glossary"
            elif path.startswith("/login"):
                key = "login"
            elif path.startswith("/signup"):
                key = "signup"
            elif path.startswith("/insurance-recommendation"):
                key = "insurance_recommendation"

            if key and key in FALLBACK_PAGES:
                logger.warning("Template missing for %s (%s). Serving fallback page.", path, e)
                return HttpResponse(FALLBACK_PAGES[key], content_type="text/html; charset=utf-8", status=200)
            # 폴백 대상이 아니면 원래 예외 재발생
            raise
