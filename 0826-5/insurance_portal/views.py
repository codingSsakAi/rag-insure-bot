"""
Feature: 보험 상식
Purpose: 파일 용도 주석 추가
Notes: 해당 파일은 보험 상식 기능에 사용됩니다.
"""
from django.shortcuts import render
from django.http import JsonResponse
# Create your views here.
def portal_home(request):
    # 전역 번들 주입 미들웨어가 자동으로 _bundle_head/_bundle_body를 삽입
    return render(request, "insurance_portal/portal_home.html")

def claim_knowledge(request):
    # 이후 실제 지식뷰어 JS가 mount되도록 템플릿만 준비
    return render(request, "insurance_portal/claim_knowledge.html")

def healthz(request):
    return JsonResponse({"status": "ok", "app": "insurance_portal"})