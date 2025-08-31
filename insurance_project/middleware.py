from __future__ import annotations

import mimetypes
import logging
import re
import traceback
from pathlib import Path
from typing import Iterable

from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.template import TemplateDoesNotExist

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
#  A) /static/insurance_portal/** → 브릿지
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
#  B) HTML 응답 후처리: 포털 리소스 주입 + Font Awesome 링크 교정
# ─────────────────────────────────────────────────────────────
class PortalAutoInjectMiddleware(MiddlewareMixin):
    EXCLUDE_PREFIXES: tuple[str, ...] = ("/admin", "/static", "/media")
    MARKER = b"<!-- __PORTAL_INJECTED__ -->"
    FA_MARKER = "<!-- __FA_FIXED__ -->"

    # 정상 CDN (검증된 버전)
    FA_GOOD = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css"

    # 잘못된/구버전/오타 링크들을 잡아내는 정규식들
    RE_FA_LINKS = [
        # cdnjs - 다양한 버전/오타(all.css, all.min.css 모두)
        re.compile(
            r"""<link\s+[^>]*rel=["']stylesheet["'][^>]*href=["']\s*
            https?://cdnjs\.cloudflare\.com/ajax/libs/font-?awesome/[^"']+/css/all(?:\.min)?\.css[^"']*
            ["'][^>]*>\s*""",
            re.IGNORECASE | re.VERBOSE,
        ),
        # jsDelivr
        re.compile(
            r"""<link\s+[^>]*rel=["']stylesheet["'][^>]*href=["']\s*
            https?://cdn\.jsdelivr\.net/npm/@?fortawesome/font-?awesome[^"']*
            (?:all(?:\.min)?\.css)[^"']*
            ["'][^>]*>\s*""",
            re.IGNORECASE | re.VERBOSE,
        ),
        # use.fontawesome.com (v5/v6 kit CSS 직접 링크)
        re.compile(
            r"""<link\s+[^>]*rel=["']stylesheet["'][^>]*href=["']\s*
            https?://use\.fontawesome\.com/[^"']+/(?:css|releases)/[^"']*/all(?:\.min)?\.css[^"']*
            ["'][^>]*>\s*""",
            re.IGNORECASE | re.VERBOSE,
        ),
    ]

    # CSS 안의 @import 형태도 치환
    RE_FA_IMPORT = re.compile(
        r"""@import\s+url\(\s*["']?\s*https?://(?:cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net|use\.fontawesome\.com)[^)"']+\b(all(?:\.min)?\.css)\s*["']?\s*\)\s*;?""",
        re.IGNORECASE | re.VERBOSE,
    )

    def __init__(self, get_response):
        super().__init__(get_response)
        # 불필요한 404 줄이도록 후보 최소화
        self.css_candidates: list[str] = [
            "/static/insurance_portal/css/portal.css",
            "/static/insurance_portal/portal.css",
        ]
        self.js_candidates: list[str] = [
            "/static/insurance_portal/loader_strict.js",
            "/static/insurance_portal/loader.js",
            "/static/insurance_portal/js/portal.js",
            "/static/insurance_portal/portal.js",
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

    def _fix_fontawesome(self, html: str) -> tuple[str, bool]:
        """문서 내 잘못된 FA 링크/임포트를 전부 제거·치환하고, 없으면 주입."""
        changed = False

        if self.FA_MARKER in html:
            return html, False

        # 1) @import 형태 치환
        html2, n_imp = self.RE_FA_IMPORT.subn(f'@import url("{self.FA_GOOD}");', html)
        if n_imp:
            logger.warning("Replaced %d Font Awesome @import reference(s).", n_imp)
            changed = True
        else:
            html2 = html

        # 2) <link rel=stylesheet ...> 형태 제거 후 정상 CDN 한 번만 삽입
        removed = 0
        for rx in self.RE_FA_LINKS:
            html2, n = rx.subn("", html2)
            removed += n
        if removed:
            logger.warning("Removed %d broken external Font Awesome link(s).", removed)
            changed = True

        # 3) 문서에 FA가 전혀 없으면 정상 CDN 삽입
        if ("font-awesome" not in html2.lower()) and ("all.min.css" not in html2):
            fa_tag = (
                f'{self.FA_MARKER}\n'
                f'<link rel="stylesheet" href="{self.FA_GOOD}" crossorigin="anonymous" referrerpolicy="no-referrer">\n'
            )
            if "</head>" in html2:
                html2 = html2.replace("</head>", fa_tag + "</head>")
            elif "<body" in html2:
                html2 = re.sub(r"(<body[^>]*>)", r"\1\n" + fa_tag, html2, count=1, flags=re.IGNORECASE)
            else:
                html2 = fa_tag + html2
            changed = True

        # 4) 안전망: 이미 잘못된 버전 숫자가 하드코딩돼 있으면 직접 치환
        #   예: 6.5.12 → 6.5.2
        html3, n_ver = re.subn(
            r"(cdnjs\.cloudflare\.com/ajax/libs/font-?awesome/)(\d+\.\d+\.\d+)(/css/all(?:\.min)?\.css)",
            r"\g<1>6.5.2\g<3>",
            html2,
            flags=re.IGNORECASE,
        )
        if n_ver:
            logger.warning("Normalized %d Font Awesome version reference(s) to 6.5.2.", n_ver)
            changed = True

        # 5) 런타임 안전망(헤드에 짧은 스크립트): DOM 파싱 후 잘못된 링크가 있으면 비활성화하고 정상 CDN 추가
        if self.FA_MARKER not in html3:
            runtime_fix = (
                "<script>(function(){"
                "try{var bad=[];var lnks=document.querySelectorAll('link[rel=stylesheet]');"
                "for(var i=0;i<lnks.length;i++){var h=(lnks[i].getAttribute('href')||'').toLowerCase();"
                "if(h.indexOf('fontawesome')>-1||h.indexOf('font-awesome')>-1){"
                "if(h.indexOf('cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css')===-1){bad.push(lnks[i]);}"
                "}}"
                "if(bad.length){for(var j=0;j<bad.length;j++){bad[j].disabled=true;}"
                "var l=document.createElement('link');l.rel='stylesheet';l.href='%s';"
                "l.crossOrigin='anonymous';l.referrerPolicy='no-referrer';document.head.appendChild(l);}"
                "}catch(e){}"
                "})();</script>" % self.FA_GOOD
            )
            if "</head>" in html3:
                html3 = html3.replace("</head>", runtime_fix + "</head>")
            else:
                html3 = runtime_fix + html3
            changed = True

        return html3, changed

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

        # 이미 다른 주입이 있었다면 FA만 보정
        try:
            charset = resp.charset or "utf-8"
        except Exception:
            charset = "utf-8"

        html = resp.content.decode(charset, errors="ignore")

        # Font Awesome 고장 링크 보정
        html, fa_changed = self._fix_fontawesome(html)

        # 포털 CSS/JS 자동 주입 (있을 때만)
        if self.MARKER not in resp.content:
            css_url = self._pick_first(self.css_candidates)
            js_url = self._pick_first(self.js_candidates)

            if css_url or js_url:
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

        if fa_changed or (self.MARKER not in resp.content):
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
#  D) 특정 경로 폴백
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
