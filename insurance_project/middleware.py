# insurance_project/middleware.py
# 우하단 3선 FAB/사이드패널을 주입하던 로직을 전면 중단한 버전

from __future__ import annotations
import time
from typing import Callable
from django.utils.deprecation import MiddlewareMixin


class InsurancePortalMiddleware(MiddlewareMixin):
    """
    이전: HTML 응답에 portal.css / portal.js / window.PORTAL_MENU 를 삽입해
         #ip-fab(3선 버튼)과 사이드 패널을 모든 페이지에 만들었음.
    현재: 어떤 HTML 삽입도 하지 않음 → 3선 FAB 완전 제거.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        # ✨ 더 이상 portal 스크립트/스타일/설정 주입 안 함
        try:
            dur_ms = int((time.time() - start) * 1000)
            response.headers["Server-Timing"] = f"app;dur={dur_ms}"
        except Exception:
            pass
        return response
