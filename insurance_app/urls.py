from django.urls import path
from . import views

app_name = "insurance_app"

urlpatterns = [
    path("", views.home, name="home"),

    # 정식 라우트(하이픈)
    path("insurance-recommendation/", views.insurance_recommendation, name="insurance_recommendation"),

    # 기존 라우트들
    path("recommend/", views.recommend_insurance, name="recommend_insurance"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("mypage/", views.mypage, name="mypage"),
    path("glossary/", views.glossary, name="glossary"),
    path("api/glossary", views.glossary_api, name="glossary_api"),
]
