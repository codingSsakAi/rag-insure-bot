from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve

# 정적 fallback/파비콘 헬퍼
try:
    from .static_fallback import serve_static_fallback, serve_favicon
except Exception:
    serve_static_fallback = None
    serve_favicon = None

urlpatterns = [
    path('admin/', admin.site.urls),

    # 메인 앱
    path('', include('insurance_app.urls')),

    # ✅ accident_project 네임스페이스 등록 (템플릿의 `{% url 'accident_project:...' %}` 대응)
    path(
        'accident/',
        include(('accident_project.urls', 'accident_project'), namespace='accident_project')
    ),
]

# ✅ 약관 PDF 서빙: /documents/<path> → settings.DOCUMENTS_ROOT
urlpatterns += [
    re_path(
        r'^documents/(?P<path>.*)$',
        static_serve,
        {'document_root': str(settings.DOCUMENTS_ROOT)},
        name='documents_serve',
    ),
]

# (선택) 파비콘
if serve_favicon:
    urlpatterns += [
        re_path(r'^favicon\.ico$', serve_favicon, name='favicon'),
    ]

# ✅ 정적 자산 fallback: /static/<path> 요청을 여러 후보 루트에서 탐색 서빙
if serve_static_fallback:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve_static_fallback, name='static_fallback'),
    ]
