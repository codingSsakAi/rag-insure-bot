# insurance_project/urls.py - 임시 수정
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def temp_home(request):
    return HttpResponse("<h1>서버 정상 작동!</h1><p>무한 리다이렉트 해결됨</p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', temp_home, name='home'),  # 임시 홈
    # path('', include('insurance_portal.urls')),  # 주석 처리
]