from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
from pathlib import Path
import insurance_portal  # noqa: F401

# 레거시 직접 매핑 (템플릿 호환)
from insurance_app import views as app_views

urlpatterns = [
    # 레거시 직접 매핑(우선 순위 높게)
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

# insurance_portal 앱 라우트(있으면)
try:
    urlpatterns += [
        path("", include(("insurance_portal.urls", "insurance_portal"), namespace="insurance_portal")),
    ]
except Exception:
    pass

# 정적/미디어
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 개발 편의: 포털 정적 자원(아카이브/루트 모두 지원)
_portal_static_roots = [
    Path(settings.BASE_DIR) / "insurance_portal" / "static" / "insurance_portal",
    Path(settings.BASE_DIR) / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
]
if settings.DEBUG:
    for root in _portal_static_roots:
        if root.exists():
            urlpatterns += [
                re_path(
                    r"^static/insurance_portal/(?P<path>.*)$",
                    static_serve,
                    {"document_root": str(root)},
                ),
            ]
