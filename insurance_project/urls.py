# insurance_project/urls.py
from pathlib import Path
import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve as static_serve

# 핵심: app_views 임포트 (미정의 에러 해결)
from insurance_app import views as app_views

# BASE_DIR 계산 (settings.py와 동일 방식)
BASE_DIR = Path(__file__).resolve().parent.parent

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

    # 앱 URL 포함 (메인앱 유지)
    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),

    # 관리자
    path("admin/", admin.site.urls),

    # ─────────────────────────────────────────────────────────────────────
    # 아카이브 구조 그대로: /0826-5/** 를 디스크의 BASE_DIR/0826-5 에 매핑
    # 템플릿/STATIC 수정 없이 404 & MIME 오류만 해결
    re_path(
        r"^0826-5/(?P<path>.*)$",
        static_serve,
        {"document_root": os.path.join(BASE_DIR, "0826-5"), "show_indexes": False},
        name="legacy_0826_5_assets",
    ),
    # ─────────────────────────────────────────────────────────────────────
]
