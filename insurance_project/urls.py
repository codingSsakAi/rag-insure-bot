# insurance_project/urls.py
from pathlib import Path
import os

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve as static_serve

# app_views 미정의 오류 방지
from insurance_app import views as app_views

BASE_DIR = Path(__file__).resolve().parent.parent

urlpatterns = [
    # ── 메인 라우팅(그대로 유지) ─────────────────────────────────────────
    path("", app_views.home, name="home"),
    path("signup/", app_views.signup, name="signup"),
    path("login/", app_views.login_view, name="login"),
    path("logout/", app_views.logout_view, name="logout"),
    path("mypage/", app_views.mypage, name="mypage"),
    path("recommend/", app_views.recommend_insurance, name="recommend_insurance"),
    path("insurance-recommendation/", app_views.insurance_recommendation, name="insurance_recommendation"),
    path("glossary/", app_views.glossary, name="glossary"),
    path("api/glossary", app_views.glossary_api, name="glossary_api"),

    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),

    path("admin/", admin.site.urls),

    # ── 0826-5 별칭(요청 URL은 그대로: /0826-5/insurance_portal/js/*.js) ──
    # 요청: /0826-5/insurance_portal/js/*  → 실제 파일: /0826-5/insurance_portal/static/insurance_portal/js/*
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

    # 요청: /0826-5/insurance_portal/css/* → 실제 파일: /0826-5/insurance_portal/static/insurance_portal/css/*
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

    # 요청: /0826-5/insurance_portal/img/* → 실제 파일: /0826-5/insurance_portal/static/insurance_portal/img/*
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

    # 나머지 /0826-5/**는 그대로 디스크 매핑(순서: alias들보다 아래에 둬야 함)
    re_path(
        r"^0826-5/(?P<path>.*)$",
        static_serve,
        {"document_root": os.path.join(BASE_DIR, "0826-5"), "show_indexes": False},
        name="legacy_0826_5_assets",
    ),
]
