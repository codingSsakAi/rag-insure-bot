# insurance_project/urls.py
from pathlib import Path
import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve as static_serve

# app_views 미정의 오류 해결
from insurance_app import views as app_views

# BASE_DIR 계산
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

    # 앱 URL 포함
    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),

    # 관리자
    path("admin/", admin.site.urls),

    # ─────────────────────────────────────────────────────────────────────
    # [중요] 아카이브 실제 위치:
    #   /0826-5/insurance_portal/static/insurance_portal/{js,css,img}/...
    # 템플릿은 /0826-5/insurance_portal/{js,css,img}/... 로 요청함 → alias 필요
    #
    # 1) JS 별칭: /0826-5/insurance_portal/js/*  →  /0826-5/insurance_portal/static/insurance_portal/js/*
    re_path(
        r"^0826-5/insurance_portal/js/(?P<path>.*)$",
        static_serve,
        {
            "document_root": os.path.join(
                BASE_DIR, "0826-5", "insurance_portal", "static", "insurance_portal", "js"
            ),
            "show_indexes": False,
        },
        name="legacy_0826_5_js",
    ),

    # 2) CSS 별칭
    re_path(
        r"^0826-5/insurance_portal/css/(?P<path>.*)$",
        static_serve,
        {
            "document_root": os.path.join(
                BASE_DIR, "0826-5", "insurance_portal", "static", "insurance_portal", "css"
            ),
            "show_indexes": False,
        },
        name="legacy_0826_5_css",
    ),

    # 3) IMG 별칭 (있는 경우)
    re_path(
        r"^0826-5/insurance_portal/img/(?P<path>.*)$",
        static_serve,
        {
            "document_root": os.path.join(
                BASE_DIR, "0826-5", "insurance_portal", "static", "insurance_portal", "img"
            ),
            "show_indexes": False,
        },
        name="legacy_0826_5_img",
    ),

    # 4) 그 외 /0826-5/** 는 루트 매핑 (아카이브 구조 그대로)
    re_path(
        r"^0826-5/(?P<path>.*)$",
        static_serve,
        {"document_root": os.path.join(BASE_DIR, "0826-5"), "show_indexes": False},
        name="legacy_0826_5_assets",
    ),
    # ─────────────────────────────────────────────────────────────────────
]
