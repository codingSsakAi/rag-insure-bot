from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# ───────────────── 기본 설정 ─────────────────
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 0826-5 안의 앱/템플릿을 import 가능하도록 경로 추가
sys.path.append(str(BASE_DIR / "0826-5"))

# ───────────────── 보안/디버그(환경변수로 제어) ─────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    ".cloudtype.app,localhost,127.0.0.1"
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://*.cloudtype.app,http://localhost,http://127.0.0.1"
).split(",")

# 500 원인 추적을 위해 콘솔로 스택 출력 (응답형태는 그대로 유지)
DEBUG_PROPAGATE_EXCEPTIONS = True
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR"},
        "django": {"handlers": ["console"], "level": "ERROR"},
    },
}

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

# 아카이브(0826-5/insurance_portal) 또는 프로젝트 루트(insurance_portal) 중 존재하는 쪽만 앱으로 등록
if (BASE_DIR / "insurance_portal").exists() or (BASE_DIR / "0826-5" / "insurance_portal").exists():
    INSTALLED_APPS.append("insurance_portal")

AUTH_USER_MODEL = "insurance_app.CustomUser"

# ───────────────── 미들웨어 ─────────────────
# >>> 라우팅에 영향 주는 신규 폴백/가로채기 미들웨어는 넣지 않습니다. <<<
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # 정적 브릿지: /static/insurance_portal/** 를 원본에서 직접 서빙
    "insurance_project.middleware.PortalStaticBridgeMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 성공한 HTML에만 원본 토글 CSS/JS 주입 (200 응답에만 동작)
    "insurance_project.middleware.PortalAutoInjectMiddleware",
]

ROOT_URLCONF = "insurance_project.urls"
WSGI_APPLICATION = "insurance_project.wsgi.application"

# ───────────────── 템플릿 ─────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # ✅ 기존 템플릿 우선 탐색 경로
            BASE_DIR / "templates",
            BASE_DIR / "insurance_app" / "templates",
            # ✅ 아카이브/루트 포털 템플릿(있을 때만)
            BASE_DIR / "0826-5" / "insurance_portal" / "templates",
            BASE_DIR / "insurance_portal" / "templates",
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
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "db.sqlite3"))
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DB_PATH}
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

# 정적 자원 후보(실제 존재할 때만 추가)
_root_static = BASE_DIR / "insurance_portal" / "static" / "insurance_portal"      # 루트에 풀렸을 때
_arch_static = BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal"  # 아카이브 폴더 내
_app_static  = BASE_DIR / "insurance_app" / "static" / "insurance_portal"

STATICFILES_DIRS = []

# 1) 일반 정적 폴더들
for p in [
    BASE_DIR / "insurance_app" / "static",
    BASE_DIR / "accident_project" / "static",
    BASE_DIR / "insurance_portal" / "static",
    BASE_DIR / "0826-5" / "insurance_portal" / "static",
]:
    if p.exists():
        STATICFILES_DIRS.append(p)

# 2) 템플릿에서 'insurance_portal/...' 프리픽스로 요청하는 경우용 prefix 매핑
for p in [_root_static, _arch_static, _app_static]:
    if p.exists():
        STATICFILES_DIRS.append(("insurance_portal", p))

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ───────────────── 기타 ─────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_MOCK_API = True
LOGIN_URL = "/login/"
X_FRAME_OPTIONS = "SAMEORIGIN"

# 약관 PDF 문서 경로 (예: insurance_app/documents/회사/회사.pdf)
DOCUMENTS_URL = "/documents/"
DOCUMENTS_ROOT = BASE_DIR / "insurance_app" / "documents"
