from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),

    # 메인 앱
    path('', include('insurance_app.urls')),

    # ✅ accident_project 네임스페이스 등록
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
