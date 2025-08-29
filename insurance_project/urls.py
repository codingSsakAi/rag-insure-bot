from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve

# 문서(PDF)와 정적 파일 fallback 서빙용 뷰
from .static_fallback import serve_static_fallback, serve_favicon

urlpatterns = [
    path('admin/', admin.site.urls),

    # 앱 라우팅 (기존 insurance_app.urls 유지)
    path('', include('insurance_app.urls')),
]

# 약관 PDF 서빙: /documents/<path> → settings.DOCUMENTS_ROOT
urlpatterns += [
    re_path(
        r'^documents/(?P<path>.*)$',
        static_serve,
        {'document_root': str(settings.DOCUMENTS_ROOT)},
        name='documents_serve',
    ),
]

# favicon (있으면 서빙)
urlpatterns += [
    re_path(r'^favicon\.ico$', serve_favicon, name='favicon'),
]

# ✅ 정적 자산 fallback:
# /static/<path> 요청을 여러 후보 루트에서 순차 탐색하여 존재 파일을 서빙
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve_static_fallback, name='static_fallback'),
]
