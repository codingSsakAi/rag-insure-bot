# insurance_project/wsgi.py
import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent

# 1) 루트를 항상 최우선
if str(BASE_DIR) in sys.path:
    sys.path.remove(str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR))

# 2) 0826-5는 임포트 우선순위에서 제외(필요 없으면 아예 경로에 넣지 않음)
EXTRA = BASE_DIR / "0826-5"
extra_str = str(EXTRA)
if extra_str in sys.path:
    sys.path.remove(extra_str)
# 필요할 때만 '참고용'으로 끝에 붙이고 싶다면 아래 주석 해제 (기본은 비활성)
# if EXTRA.exists() and extra_str not in sys.path:
#     sys.path.append(extra_str)  # ← 맨 뒤

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insurance_project.settings")
application = get_wsgi_application()
