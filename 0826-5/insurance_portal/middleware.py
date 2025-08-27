# insurance_portal/middleware.py
# -----------------------------------------------------------------------------
# PortalInjectorMiddleware
# - 모든 HTML 응답에 포털 번들을 자동 삽입
#   · </head> 직전에: templates/insurance_portal/_bundle_head.html
#   · </body> 직전에: templates/insurance_portal/_bundle_body.html
# - 로그인/회원가입/관리자/정적/API 등은 settings의 제외 규칙으로 스킵
# - 비-HTML, 스트리밍, 압축 응답, 비-200 응답은 스킵
# - Content-Length 갱신 처리
# -----------------------------------------------------------------------------

import re
from django.conf import settings
from django.template.loader import render_to_string

HEAD_CLOSE_RE = re.compile(br"</head\s*>", re.IGNORECASE)
BODY_CLOSE_RE = re.compile(br"</body\s*>", re.IGNORECASE)

def _has_compression(response) -> bool:
    enc = response.get("Content-Encoding", "")
    return bool(enc) and enc.lower() in ("gzip", "br", "deflate")

def _is_html(response) -> bool:
    ctype = response.get("Content-Type", "")
    return ctype.lower().startswith("text/html")

def _should_skip(request, response) -> bool:
    # 상태/형태 체크
    if getattr(response, "streaming", False):
        return True
    if response.status_code != 200:
        return True
    if not _is_html(response):
        return True
    if _has_compression(response):
        return True

    # 경로 프리픽스 제외
    path = (request.path or "")
    for prefix in getattr(settings, "PORTAL_INJECT_EXCLUDED_PATH_PREFIXES", []):
        if path.startswith(prefix):
            return True

    # 뷰네임 제외
    try:
        match = request.resolver_match
        if match and match.view_name in getattr(settings, "PORTAL_INJECT_EXCLUDED_VIEWNAMES", []):
            return True
    except Exception:
        pass

    return False


class PortalInjectorMiddleware:
    """
    HTML 응답에 insurance_portal 번들을 '주입'하는 미들웨어.
    - </head> 직전: insurance_portal/_bundle_head.html
    - </body> 직전: insurance_portal/_bundle_body.html
    템플릿이 존재하지 않으면 조용히 스킵하여 기존 페이지를 깨뜨리지 않음.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if _should_skip(request, response):
            return response

        # 응답 본문(bytes) 취득
        try:
            charset = response.charset or "utf-8"
        except Exception:
            charset = "utf-8"

        content_bytes = response.content

        # 파셜 렌더 (없으면 빈 문자열)
        try:
            head_html = render_to_string("insurance_portal/_bundle_head.html", {})
        except Exception:
            head_html = ""
        try:
            body_html = render_to_string("insurance_portal/_bundle_body.html", {})
        except Exception:
            body_html = ""

        head_bytes = head_html.encode(charset) if head_html else b""
        body_bytes = body_html.encode(charset) if body_html else b""

        changed = False

        # </head> 앞에 주입
        if head_bytes:
            new_content, n = HEAD_CLOSE_RE.subn(head_bytes + b"\n</head>", content_bytes, count=1)
            if n > 0:
                content_bytes = new_content
                changed = True

        # </body> 앞에 주입
        if body_bytes:
            new_content, n = BODY_CLOSE_RE.subn(body_bytes + b"\n</body>", content_bytes, count=1)
            if n > 0:
                content_bytes = new_content
                changed = True

        if changed:
            response.content = content_bytes
            # 길이 갱신
            response["Content-Length"] = str(len(content_bytes))

        return response
