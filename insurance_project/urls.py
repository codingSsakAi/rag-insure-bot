from pathlib import Path
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
import insurance_portal  # noqa: F401

# 기존 insurance_app 뷰 직접 연결 (과거 템플릿 호환용)
from insurance_app import views as app_views

urlpatterns = [
    # 레거시 직접 매핑 (유지)
    path("", app_views.home, name="home"),
    path("signup/", app_views.signup, name="signup"),
    path("login/", app_views.login_view, name="login"),
    path("logout/", app_views.logout_view, name="logout"),
    path("mypage/", app_views.mypage, name="mypage"),
    path("recommend/", app_views.recommend_insurance, name="recommend_insurance"),
    path("insurance-recommendation/", app_views.insurance_recommendation, name="insurance_recommendation"),
    path("glossary/", app_views.glossary, name="glossary"),
    path("api/glossary", app_views.glossary_api, name="glossary_api"),

    # 앱 URL 포함
    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),

    # 관리자
    path("admin/", admin.site.urls),
]

# 개발 서버에서만 약관 PDF 공개 서빙
# 실제 파일: <BASE_DIR>/insurance_app/documents/<회사명>/<회사명>.pdf
if getattr(settings, 'DEBUG', False):
    documents_root = (Path(settings.BASE_DIR) / 'insurance_app' / 'documents').resolve()
    urlpatterns += [
        re_path(r'^documents/(?P<path>.*)$',
                static_serve, {'document_root': str(documents_root)}),
    ]
