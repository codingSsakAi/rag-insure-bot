#!/usr/bin/env python
# root/manage.py
import os
import sys
from pathlib import Path

def main():
    BASE_DIR = Path(__file__).resolve().parent  # root/

    # 1) 메인 프로젝트(root)가 sys.path의 최상단에 오도록 보정
    if str(BASE_DIR) in sys.path:
        # 이미 있으면 맨 앞으로 재배치
        sys.path.remove(str(BASE_DIR))
    sys.path.insert(0, str(BASE_DIR))

    # 2) 팀원 코드(0826-5)는 맨 **뒤**에 붙여 portal만 추가로 찾도록
    extra = BASE_DIR / "0826-5"
    if extra.exists() and str(extra) not in sys.path:
        sys.path.append(str(extra))  # ← append가 포인트 (insert(0, ...) 금지)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insurance_project.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django import 실패: 가상환경/설치 확인") from exc

    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
