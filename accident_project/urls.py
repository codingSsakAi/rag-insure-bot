from django.urls import path, RedirectView
from . import views

app_name = "accident_project"

urlpatterns = [
    path("", views.index, name="index"),

    # 신규 작성/출력
    path("agreements/new/", views.agreement_form, name="agreement_new"),
    path("agreements/<int:pk>/", views.agreement_print, name="agreement_print"),

    # 저장(신규) + 수정 저장
    path("agreements/submit/", views.agreement_submit, name="agreement_submit"),
    path("agreements/<int:pk>/update/", views.agreement_update, name="agreement_update"),

    # 미리보기
    path("agreements/preview/", views.agreement_preview, name="agreement_preview"),
    path("agreements/<int:pk>/preview/", views.agreement_preview_saved, name="agreement_preview_saved"),

    # 파일(Fallback)
    path("agreements/<int:pk>/pdf/",   views.agreement_pdf,   name="agreement_pdf"),
    path("agreements/<int:pk>/image/", views.agreement_image, name="agreement_image"),

    # 마이페이지
    path("mypage/", views.mypage, name="mypage"),
    path("mypage/agreements/", views.mypage_agreements, name="mypage_agreements"),
    path("agreements/<int:pk>/edit/",   views.agreement_edit,   name="agreement_edit"),
    path("agreements/<int:pk>/delete/", views.agreement_delete, name="agreement_delete"),

    # 레거시 호환
    path("agreement/preview/", RedirectView.as_view(url="/accident/agreements/new/", permanent=True)),
]
