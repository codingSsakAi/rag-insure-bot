# insurance_project/settings.py - CORS/404 문제 완전 해결 버전
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

# ───────────────── 기본 설정 ─────────────────
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 0826-5 안의 앱/템플릿을 import 가능하도록 경로 추가
sys.path.append(str(BASE_DIR / "0826-5"))

print(f"🚀 Django starting - BASE_DIR: {BASE_DIR}")

# ───────────────── 보안/디버그(환경변수로 제어) ─────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
DEBUG = os.getenv("DEBUG", "0") == "1"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    ".cloudtype.app,localhost,127.0.0.1,*.sel5.cloudtype.app"
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://*.cloudtype.app,https://*.sel5.cloudtype.app,http://localhost,http://127.0.0.1"
).split(",")

# ───────────────── 로깅 설정 강화 ─────────────────
# 로그 디렉토리 생성
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django.log',
            'formatter': 'verbose',
        },
        'middleware_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler', 
            'filename': LOGS_DIR / 'middleware.log',
            'formatter': 'verbose',
        },
        'static_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'static.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'insurance_project.middleware': {
            'handlers': ['middleware_file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'static_serving': {
            'handlers': ['static_file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'insurance_portal': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# 500 원인 추적을 위해 콘솔로 스택 출력
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG

# ───────────────── 앱 구성 ─────────────────
INSTALLED_APPS = [
    "django.contrib.admin", 
    "django.contrib.auth", 
    "django.contrib.contenttypes",
    "django.contrib.sessions", 
    "django.contrib.messages", 
    "django.contrib.staticfiles",
    # 프로젝트 앱
    "insurance_app",
    "accident_project",
    # 서드파티
    "rest_framework",
]

# 아카이브(0826-5/insurance_portal) 또는 프로젝트 루트(insurance_portal) 중 존재하는 쪽만 앱으로 등록
portal_paths = [
    BASE_DIR / "insurance_portal",
    BASE_DIR / "0826-5" / "insurance_portal"
]

for portal_path in portal_paths:
    if portal_path.exists() and portal_path.is_dir():
        if (portal_path / "__init__.py").exists() or (portal_path / "apps.py").exists():
            INSTALLED_APPS.append("insurance_portal")
            print(f"✅ Added insurance_portal from: {portal_path}")
            break

AUTH_USER_MODEL = "insurance_app.CustomUser"

# ───────────────── 미들웨어 (순서 중요!) ─────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # 🔧 예외 로깅 (가장 먼저)
    "insurance_project.middleware.ExceptionLoggingMiddleware",
    # 🔧 정적 파일 브릿지 (라우팅 전에)
    "insurance_project.middleware.PortalStaticBridgeMiddleware",
    
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    # 🔧 HTML 응답 수정 (마지막 단계에서)
    "insurance_project.middleware.PortalAutoInjectMiddleware",
    # 🔧 템플릿 폴백 (최종 에러 처리)
    "insurance_project.middleware.TemplateFallbackMiddleware",
]

ROOT_URLCONF = "insurance_project.urls"
WSGI_APPLICATION = "insurance_project.wsgi.application"

# ───────────────── 템플릿 설정 ─────────────────
# 템플릿 디렉토리 우선순위 설정
TEMPLATE_DIRS = [
    BASE_DIR / "templates",
    BASE_DIR / "insurance_app" / "templates",
]

# insurance_portal 템플릿 경로 추가 (존재하는 것만)
portal_template_paths = [
    BASE_DIR / "0826-5" / "insurance_portal" / "templates",
    BASE_DIR / "insurance_portal" / "templates",
]

for template_path in portal_template_paths:
    if template_path.exists():
        TEMPLATE_DIRS.append(template_path)
        print(f"✅ Added template dir: {template_path}")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": TEMPLATE_DIRS,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # 커스텀 컨텍스트 프로세서
                "django.template.context_processors.static",
            ],
        },
    },
]

# ───────────────── 데이터베이스 ─────────────────
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "db.sqlite3"))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3", 
        "NAME": DB_PATH,
        "OPTIONS": {
            "timeout": 20,
        }
    }
}

# ───────────────── 정적 파일 설정 (핵심 수정!) ─────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# 정적 파일 디렉토리 탐색 및 설정
STATICFILES_DIRS = []

# 1) 기본 앱들의 정적 파일 디렉토리
basic_static_dirs = [
    BASE_DIR / "insurance_app" / "static",
    BASE_DIR / "accident_project" / "static",
]

for static_dir in basic_static_dirs:
    if static_dir.exists():
        STATICFILES_DIRS.append(static_dir)
        print(f"✅ Added basic static dir: {static_dir}")

# 2) insurance_portal 정적 파일 디렉토리 (우선순위 순)
portal_static_candidates = [
    # 아카이브 버전 (우선)
    BASE_DIR / "0826-5" / "insurance_portal" / "static",
    # 루트 버전
    BASE_DIR / "insurance_portal" / "static",
]

portal_static_added = False
for static_dir in portal_static_candidates:
    if static_dir.exists() and not portal_static_added:
        STATICFILES_DIRS.append(static_dir)
        portal_static_added = True
        print(f"✅ Added portal static dir: {static_dir}")
        
        # insurance_portal 내부 구조 확인
        insurance_portal_dir = static_dir / "insurance_portal"
        if insurance_portal_dir.exists():
            print(f"   └── Found insurance_portal subdir with files:")
            for file_type in ['css', 'js', 'json', 'img']:
                type_dir = insurance_portal_dir / file_type
                if type_dir.exists():
                    file_count = len(list(type_dir.glob("*")))
                    print(f"       {file_type}/: {file_count} files")

# 3) 템플릿에서 'insurance_portal/...' 프리픽스 요청 대응용 매핑
insurance_portal_root = None
for candidate in [
    BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
    BASE_DIR / "insurance_portal" / "static" / "insurance_portal",
    BASE_DIR / "insurance_app" / "static" / "insurance_portal",
]:
    if candidate.exists():
        STATICFILES_DIRS.append(("insurance_portal", candidate))
        insurance_portal_root = candidate
        print(f"✅ Added prefix mapping: insurance_portal -> {candidate}")
        break

# 정적 파일 파인더 설정
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# 개발/프로덕션 환경별 정적 파일 처리
if DEBUG:
    # 개발 환경: 기본 저장소 사용
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    # 프로덕션 환경: 매니페스트 저장소 사용 (캐시 무력화)
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# ───────────────── 캐싱 설정 ─────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5분
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# 세션 설정
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24시간

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

# ───────────────── 보안 설정 ─────────────────
# 개발/프로덕션 환경별 보안 설정
if DEBUG:
    # 개발 환경
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    # 프로덕션 환경
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1년
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True

# X-Frame-Options 설정
X_FRAME_OPTIONS = "SAMEORIGIN"

# CORS 설정 (필요시)
CORS_ALLOWED_ORIGINS = [
    "https://cdn.jsdelivr.net",  # 안전한 CDN만 허용
]
CORS_ALLOW_ALL_ORIGINS = False

# ───────────────── 미디어 파일 ─────────────────
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 문서 파일 경로
DOCUMENTS_URL = "/documents/"
DOCUMENTS_ROOT = BASE_DIR / "insurance_app" / "documents"

# ───────────────── REST Framework 설정 ─────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    }
}

# ───────────────── 커스텀 설정 ─────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_MOCK_API = True
LOGIN_URL = "/login/"

# 포털 관련 설정
PORTAL_ENABLED = True
PORTAL_DEBUG = DEBUG

# JavaScript/CSS 버전 관리 (캐시 무력화용)
STATIC_VERSION = "2.0"

# ───────────────── 환경별 추가 설정 ─────────────────
if DEBUG:
    print("🐛 Development mode settings:")
    print(f"   STATICFILES_DIRS: {len(STATICFILES_DIRS)} directories")
    print(f"   TEMPLATE_DIRS: {len(TEMPLATE_DIRS)} directories") 
    print(f"   LOGS_DIR: {LOGS_DIR}")
    print(f"   INSURANCE_PORTAL: {'✅ Found' if portal_static_added else '❌ Not found'}")
    
    # 개발용 추가 미들웨어 (Django Debug Toolbar 등)
    if 'debug_toolbar' in sys.modules:
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
        
else:
    print("🚀 Production mode settings applied")

# ───────────────── 설정 검증 ─────────────────
def validate_settings():
    """중요한 설정들이 올바르게 구성되었는지 검증"""
    issues = []
    
    # 1. 정적 파일 디렉토리 존재 여부
    if not STATICFILES_DIRS:
        issues.append("No STATICFILES_DIRS configured")
    
    # 2. insurance_portal 정적 파일 존재 여부
    if not portal_static_added:
        issues.append("insurance_portal static files not found")
    
    # 3. 로그 디렉토리 쓰기 권한
    try:
        test_file = LOGS_DIR / "test.log"
        test_file.touch()
        test_file.unlink()
    except Exception:
        issues.append("Logs directory not writable")
    
    # 4. 필수 미들웨어 존재 여부
    required_middleware = [
        'insurance_project.middleware.PortalStaticBridgeMiddleware',
        'insurance_project.middleware.PortalAutoInjectMiddleware',
    ]
    
    for middleware in required_middleware:
        if middleware not in MIDDLEWARE:
            issues.append(f"Missing middleware: {middleware}")
    
    if issues:
        print("⚠️  Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ All settings validated successfully")

# 설정 검증 실행
validate_settings()

print(f"🎯 Settings loaded successfully - Total static dirs: {len(STATICFILES_DIRS)}")