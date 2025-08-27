# insurance_project/urls.py
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

# 비네임스페이스 별칭용 (기존 insurance_app 뷰)
from insurance_app import views as app_views

urlpatterns = [
    # ---- 메인(비네임스페이스 별칭) ----
    path("", app_views.home, name="home"),
    path("signup/", app_views.signup, name="signup"),
    path("login/", app_views.login_view, name="login"),
    path("logout/", app_views.logout_view, name="logout"),
    path("mypage/", app_views.mypage, name="mypage"),
    path("recommend/", app_views.recommend_insurance, name="recommend_insurance"),
    path("insurance-recommendation/", app_views.insurance_recommendation, name="insurance_recommendation"),
    path("glossary/", app_views.glossary, name="glossary"),
    path("api/glossary", app_views.glossary_api, name="glossary_api"),

    # ---- 네임스페이스 버전도 유지 ----
    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),

    # ---- 다른 앱 ----
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),
    path("admin/", admin.site.urls),
]

# 개발 편의: 업로드/미디어
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ★ 여기 추가: /documents/** 를 PROJECT_ROOT/documents/** 에서 서빙
#   예: /documents/삼성화재/삼성화재.pdf  →  <프로젝트루트>/documents/삼성화재/삼성화재.pdf
urlpatterns += [
    re_path(
        r"^documents/(?P<path>.*)$",
        static_serve,
        {"document_root": settings.DOCUMENTS_ROOT},
        name="documents_serve",
    ),
]
