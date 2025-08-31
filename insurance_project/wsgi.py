import os, sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
bad = str(BASE_DIR / "0826-5")
if bad in sys.path:
    sys.path.remove(bad)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "insurance_project.settings")
application = get_wsgi_application()
