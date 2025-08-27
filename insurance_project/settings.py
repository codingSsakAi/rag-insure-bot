from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ───────────────── 보안/디버그 ─────────────────
SECRET_KEY = "django-insecure-^=1vv+pprwz$1uft-f*mx157fvf(n9v#nnb%ygm$np!o&%wb_s"
DEBUG = True
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1", "port-0-rag-insure-bot-meqs6bbd2d833e7b.sel5.cloudtype.app",]

# ───────────────── 앱 구성 ─────────────────
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    # 프로젝트 앱
    "insurance_app",
    "accident_project",
    # 서드파티
    "rest_framework",
]
# 주의: insurance_portal 은 정적자산만 쓰므로 INSTALLED_APPS 에 추가하지 않습니다.

AUTH_USER_MODEL = "insurance_app.CustomUser"

# ───────────────── 환경 변수 ─────────────────
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ───────────────── 미들웨어 ─────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "insurance_project.urls"
WSGI_APPLICATION = "insurance_project.wsgi.application"

# ───────────────── 템플릿 ─────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "insurance_app" / "templates",
        ],
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

# ───────────────── 데이터베이스 ─────────────────
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

# ───────────────── 인증/국제화 ─────────────────
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

# ───────────────── 정적/미디어 ─────────────────
STATIC_URL = "/static/"

# 각 위치에 실제로 존재하는 폴더만 자동 추가
_static_candidates = [
    BASE_DIR / "insurance_app" / "static",
    BASE_DIR / "accident_project" / "static",
    # 기존 팀원 자산(언더스코어 버전)
    BASE_DIR / "0826-5" / "insurance_portal" / "static",
    # 기존 팀원 자산(하이픈 버전) ← ★ 로그 상 여기가 실제 존재
    BASE_DIR / "0826-5" / "insurance-portal" / "static",
]
STATICFILES_DIRS = [p for p in _static_candidates if p.exists()]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 문서(약관 PDF) 루트
DOCUMENTS_URL = "/documents/"
DOCUMENTS_ROOT = BASE_DIR / "documents"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ───────────────── 기타 ─────────────────
USE_MOCK_API = True
LOGIN_URL = "/login/"

# iframe(동일 출처) 허용: 협의서 미리보기/iframe용
X_FRAME_OPTIONS = "SAMEORIGIN"
