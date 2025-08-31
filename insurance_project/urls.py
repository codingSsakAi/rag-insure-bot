from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("insurance_app.urls")),  # 메인앱 라우팅
]
