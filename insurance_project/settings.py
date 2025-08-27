from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-^=1vv+pprwz$1uft-f*mx157fvf(n9v#nnb%ygm$np!o&%wb_s"
DEBUG = True
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1", "port-0-rag-insure-bot-meqs6bbd2d833e7b.sel5.cloudtype.app",
]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "insurance_app",
    "accident_project",
    "rest_framework",
    # insurance_portal 앱이 존재할 때만(없어도 구동 가능)
    *(["insurance_portal"] if (BASE_DIR / "0826-5" / "insurance_portal").exists() or (BASE_DIR / "insurance_portal").exists() else []),
]

AUTH_USER_MODEL = "insurance_app.CustomUser"

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ★ 정적 브릿지를 먼저 두어 /static/insurance_portal/** 를 가로챌 수 있게 함
    "insurance_project.middleware.PortalStaticBridgeMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # ★ HTML 자동 주입(맨 끝쪽)
    "insurance_project.middleware.PortalAutoInjectMiddleware",
]

ROOT_URLCONF = "insurance_project.urls"
WSGI_APPLICATION = "insurance_project.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates", BASE_DIR / "insurance_app" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
# (선택) 기존 STATICFILES_DIRS 유지 가능 — 없어도 미들웨어가 다리 역할을 해줍니다.
_static_candidates = [
    BASE_DIR / "0826-5" / "insurance_portal" / "static",
    BASE_DIR / "insurance_portal" / "static",
    BASE_DIR / "insurance_app" / "static",
    BASE_DIR / "accident_project" / "static",
]
STATICFILES_DIRS = [p for p in _static_candidates if p.exists()]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_MOCK_API = True
LOGIN_URL = "/login/"

# 미리보기 iframe 허용
X_FRAME_OPTIONS = "SAMEORIGIN"

# 문서(약관 PDF) 서빙 설정
DOCUMENTS_URL = "/documents/"
DOCUMENTS_ROOT = BASE_DIR / "documents"
