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
    path(
        "insurance-recommendation/",
        app_views.insurance_recommendation,
        name="insurance_recommendation",
    ),
    path("glossary/", app_views.glossary, name="glossary"),
    path("api/glossary", app_views.glossary_api, name="glossary_api"),

    # 앱 URL 포함
    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),

    # 관리자
    path("admin/", admin.site.urls),
]

# ───────────────── insurance_portal 엔드포인트 포함 ─────────────────
# 포털 앱이 INSTALLED_APPS에 있는 경우, 포털 API/페이지를 루트로 추가
try:
    urlpatterns += [
        path("", include(("insurance_portal.urls", "insurance_portal"), namespace="insurance_portal")),
    ]
except Exception:
    # 포털 앱이 없는 배포에서도 동작하도록 무시
    pass

# ───────────────── 개발 편의용: 정적 파일(포털) 서빙 ─────────────────
_portal_static_roots = [
    settings.BASE_DIR / "insurance_portal" / "static" / "insurance_portal",
    settings.BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
]
if settings.DEBUG:
    for root in _portal_static_roots:
        if root.exists():
            urlpatterns += [
                re_path(
                    r"^static/insurance_portal/(?P<path>.*)$",
                    static_serve,
                    {"document_root": root},
                ),
            ]

# ───────────────── 정적 이미지(협의서 도면) Fallback ─────────────────
# DEBUG가 꺼져 있어도 협의서 이미지가 보이도록 /static/images/* 를 직접 서빙
_accident_images_root = settings.BASE_DIR / "accident_project" / "static" / "images"
if _accident_images_root.exists():
    urlpatterns += [
        re_path(
            r"^static/images/(?P<path>.*)$",
            static_serve,
            {"document_root": _accident_images_root},
        ),
    ]
