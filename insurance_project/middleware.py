# insurance_project/middleware.py
# ─────────────────────────────────────────────────────────────────────────────
# 목적
# - settings.MIDDLEWARE에서 기대하는 PortalAutoInjectMiddleware를 복구(호환)
# - "아무 작업도 하지 않는(no-op)" 미들웨어로 3선 FAB를 유발하는 스크립트 주입 X
# - 혹시 과거 템플릿에 ip-* 요소가 서버사이드로 들어간 경우도 렌더 전 단계에서 제거/은닉
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations
from django.utils.deprecation import MiddlewareMixin

def _try_sanitize_html(response):
    """안전 범위에서 과거 ip-* 잔재를 숨김. 실패해도 조용히 무시."""
    try:
        ctype = response.get("Content-Type", "")
        if "text/html" not in ctype:
            return response
        if not hasattr(response, "content"):
            return response

        html = response.content.decode(response.charset)

        # 최후 안전망: 혹시 템플릿에 남아 있던 과거 포털 DOM/버튼을 보이지 않게 처리
        # (client JS에서 이미 제거하므로, 여기선 가벼운 은닉만)
        hide_ids = ("ip-fab", "ip-overlay", "ip-panel", "ip-fallback")
        for _id in hide_ids:
            html = html.replace(f'id="{_id}"', f'id="{_id}" style="display:none!important"')

        response.content = html.encode(response.charset)
        response["Content-Length"] = str(len(response.content))
    except Exception:
        # 어떤 예외도 사용자에게 노출하지 않음
        pass
    return response


class PortalAutoInjectMiddleware(MiddlewareMixin):
    """
    과거 '포털 자동 주입' 미들웨어의 호환용 껍데기입니다.
    - 아무 것도 주입하지 않습니다. (3선 FAB 생성 원천 차단)
    - HTML 응답에서 ip-* 잔재가 보이면 가볍게 숨깁니다.
    """

    def process_response(self, request, response):
        return _try_sanitize_html(response)


# (선택) 추가 보안 헤더용 껍데기 — 기존 settings에 없다면 무시됨.
class SecurityHeadersMiddleware(MiddlewareMixin):
    """프로젝트에서 사용 중이었다면 유지, 아니라면 영향 없음 (등록되지 않으면 실행되지 않음)."""
    def process_response(self, request, response):
        # 필요하면 보안 헤더를 여기에 추가하세요. (현재는 no-op)
        return response
