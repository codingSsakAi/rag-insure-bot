from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # 메인: insurance_app (홈)
    path("", include(("insurance_app.urls", "insurance_app"), namespace="insurance_app")),

    # 사고/협의서
    path("accident/", include(("accident_project.urls", "accident_project"), namespace="accident_project")),
]

# 팀원 포털(URLConf가 있으면 /portal/로 연결)
try:
    import importlib
    importlib.import_module("insurance_portal.urls")
    urlpatterns.append(
        path("portal/", include(("insurance_portal.urls", "insurance_portal"), namespace="insurance_portal"))
    )
except Exception:
    # 포털이 없으면 조용히 패스
    pass
