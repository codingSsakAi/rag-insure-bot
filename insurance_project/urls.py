from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

# 레거시 템플릿에서 쓰는 전역 name('home', 'signup' 등) 보존용 직접 매핑
from insurance_app import views as app_views

urlpatterns = [
    # ── 레거시 전역 name 라우트 (템플릿의 {% url 'home' %}, {% url 'signup' %} 등 해결)
    path("", app_views.home, name="home"),
    path("signup/", app_views.signup, name="signup"),
    path("login/", app_views.login_view, name="login"),
    path("logout/", app_views.logout_view, name="logout"),
    path("mypage/", app_views.mypage, name="mypage"),
    path("recommend/", app_views.recommend_insurance, name="recommend_insurance"),
    path("insurance-recommendation/", app_views.insurance_recommendation, name="insurance_recommendation"),
    path("glossary/", app_views.glossary, name="glossary"),
    path("api/glossary", app_views.glossary_api, name="glossary_api"),

    # ── 앱 URL 포함 (namespaced 접근: insurance_app:signup 등)
    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),

    # ── 관리자
    path("admin/", admin.site.urls),
]

# ── 선택: insurance_portal 앱이 있으면 그 URL도 포함 (없어도 무시)
try:
    urlpatterns += [
        path("", include(("insurance_portal.urls", "insurance_portal"), namespace="insurance_portal")),
    ]
except Exception:
    pass

# ── 일반 정적/미디어
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ── 개발 편의용: 포털 정적 파일 2원화 경로 대응
# /static/insurance_portal/...  (현재 루트)
# /0826-5/insurance_portal/static/insurance_portal/...  (아카이브 루트)
if settings.DEBUG:
    normal_root = settings.BASE_DIR / "insurance_portal" / "static" / "insurance_portal"
    archive_root = settings.BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal"

    if normal_root.exists():
        urlpatterns += [
            re_path(r"^static/insurance_portal/(?P<path>.*)$",
                    static_serve, {"document_root": normal_root}),
        ]
    if archive_root.exists():
        urlpatterns += [
            re_path(r"^0826-5/insurance_portal/static/insurance_portal/(?P<path>.*)$",
                    static_serve, {"document_root": archive_root}),
        ]
