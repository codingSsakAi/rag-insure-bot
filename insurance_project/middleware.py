# insurance_project/middleware.py
from django.utils.deprecation import MiddlewareMixin

class PortalAutoInjectMiddleware(MiddlewareMixin):
    """과거 자동 인젝션 미들웨어의 더미 버전: 아무 것도 하지 않음"""
    def __init__(self, get_response=None):
        self.get_response = get_response
    def __call__(self, request):
        return self.get_response(request)

class PortalStaticBridgeMiddleware(MiddlewareMixin):
    """과거 정적 브릿지 미들웨어의 더미 버전: 아무 것도 하지 않음"""
    def __init__(self, get_response=None):
        self.get_response = get_response
    def __call__(self, request):
        return self.get_response(request)
