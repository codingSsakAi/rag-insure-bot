# insurance_project/middleware.py
# 목적: settings.py 에 등록되어 있는 PortalStaticBridgeMiddleware 를 제공만 한다.
#       특별한 동작은 하지 않고 그대로 패스스루한다.

from typing import Callable
from django.http import HttpRequest, HttpResponse

__all__ = ["PortalStaticBridgeMiddleware"]

class PortalStaticBridgeMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 필요 시 여기서 헤더 추가/경로 브리지 등을 넣을 수 있지만
        # 현재는 기존 동작 보존을 위해 no-op.
        response = self.get_response(request)
        return response
