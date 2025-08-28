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

# ───────────────── insurance_portal 엔드포인트 포함 ─────────────────
# 0826-5/insurance_portal 앱이 INSTALLED_APPS에 있는 경우, 포털 API/페이지를 루트로 추가
try:
    urlpatterns += [
        path("", include(("insurance_portal.urls", "insurance_portal"), namespace="insurance_portal")),
    ]
except Exception:
    # 포털 앱이 없는 배포에서도 동작하도록 무시
    pass

# ───────────────── 정적/미디어 ─────────────────
# 일반 정적/미디어
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 개발 편의를 위한 포털 전용 정적 경로(아카이브/루트 모두 지원)
_portal_static_roots = [
    settings.BASE_DIR / "insurance_portal" / "static" / "insurance_portal",
    settings.BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
]
if settings.DEBUG:
    for root in _portal_static_roots:
        if root.exists():
            urlpatterns += [
                re_path(r"^static/insurance_portal/(?P<path>.*)$",
                        static_serve,
                        {"document_root": root}),
            ]
