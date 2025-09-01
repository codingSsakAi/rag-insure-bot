from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# ????????????????? 湲곕낯 ?ㅼ젙 ?????????????????
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 0826-5 ?덉쓽 ???쒗뵆由우쓣 import 媛?ν븯?꾨줉 寃쎈줈 異붽?
sys.path.append(str(BASE_DIR / "0826-5"))

# ????????????????? 蹂댁븞/?붾쾭洹??섍꼍蹂?섎줈 ?쒖뼱) ?????????????????
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

# 500 ?먯씤 異붿쟻???꾪빐 肄섏넄濡??ㅽ깮 異쒕젰 (?묐떟?뺥깭??洹몃?濡??좎?)
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

# ????????????????? ??援ъ꽦 ?????????????????
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    # ?꾨줈?앺듃 ??
    "insurance_app",
    "accident_project",
    # ?쒕뱶?뚰떚
    "rest_framework",
]

# ?꾩뭅?대툕(0826-5/insurance_portal) ?먮뒗 ?꾨줈?앺듃 猷⑦듃(insurance_portal) 以?議댁옱?섎뒗 履쎈쭔 ?깆쑝濡??깅줉
if (BASE_DIR / "insurance_portal").exists() or (BASE_DIR / "0826-5" / "insurance_portal").exists():
    INSTALLED_APPS.append("insurance_portal")

AUTH_USER_MODEL = "insurance_app.CustomUser"

# ????????????????? 誘몃뱾?⑥뼱 ?????????????????
# >>> ?쇱슦?낆뿉 ?곹뼢 二쇰뒗 ?좉퇋 ?대갚/媛濡쒖콈湲?誘몃뱾?⑥뼱???ｌ? ?딆뒿?덈떎. <<<
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ?뺤쟻 釉뚮┸吏: /static/insurance_portal/** 瑜??먮낯?먯꽌 吏곸젒 ?쒕튃
    "insurance_project.middleware.PortalStaticBridgeMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # ?깃났??HTML?먮쭔 ?먮낯 ?좉? CSS/JS 二쇱엯 (200 ?묐떟?먮쭔 ?숈옉)
]

ROOT_URLCONF = "insurance_project.urls"
WSGI_APPLICATION = "insurance_project.wsgi.application"

# ????????????????? ?쒗뵆由??????????????????
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # ??湲곗〈 ?쒗뵆由??곗꽑 ?먯깋 寃쎈줈
            BASE_DIR / "templates",
            BASE_DIR / "insurance_app" / "templates",
            # ???꾩뭅?대툕/猷⑦듃 ?ы꽭 ?쒗뵆由??덉쓣 ?뚮쭔)
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

# ????????????????? ?곗씠?곕쿋?댁뒪 ?????????????????
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "db.sqlite3"))
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": DB_PATH}
}

# ????????????????? ?몄쬆/援?젣???????????????????
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

# ????????????????? ?뺤쟻/誘몃뵒???????????????????
STATIC_URL = "/static/"

# ?뺤쟻 ?먯썝 ?꾨낫(?ㅼ젣 議댁옱???뚮쭔 異붽?)
_root_static = BASE_DIR / "insurance_portal" / "static" / "insurance_portal"      # 猷⑦듃????몄쓣 ??
_arch_static = BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal"  # ?꾩뭅?대툕 ?대뜑 ??
_app_static  = BASE_DIR / "insurance_app" / "static" / "insurance_portal"

STATICFILES_DIRS = []

# 1) ?쇰컲 ?뺤쟻 ?대뜑??
for p in [
    BASE_DIR / "insurance_app" / "static",
    BASE_DIR / "accident_project" / "static",
    BASE_DIR / "insurance_portal" / "static",
    BASE_DIR / "0826-5" / "insurance_portal" / "static",
]:
    if p.exists():
        STATICFILES_DIRS.append(p)

# 2) ?쒗뵆由우뿉??'insurance_portal/...' ?꾨━?쎌뒪濡??붿껌?섎뒗 寃쎌슦??prefix 留ㅽ븨
for p in [_root_static, _arch_static, _app_static]:
    if p.exists():
        STATICFILES_DIRS.append(("insurance_portal", p))

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ????????????????? 湲고? ?????????????????
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_MOCK_API = True
LOGIN_URL = "/login/"
X_FRAME_OPTIONS = "SAMEORIGIN"

# ?쎄? PDF 臾몄꽌 寃쎈줈 (?? insurance_app/documents/?뚯궗/?뚯궗.pdf)
DOCUMENTS_URL = "/documents/"
DOCUMENTS_ROOT = BASE_DIR / "insurance_app" / "documents"

