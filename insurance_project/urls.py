# insurance_project/urls.py - 정적 파일 서빙 강화

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.http import HttpResponse, Http404
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('insurance_portal.urls')),
]

# ============================================================================
# 개발 환경에서 정적 파일 서빙
# ============================================================================

if settings.DEBUG:
    # 기본 정적 파일 서빙
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # STATICFILES_DIRS의 각 디렉토리에서 파일 서빙
    for i, directory in enumerate(settings.STATICFILES_DIRS):
        urlpatterns += static(
            f'/staticfiles_{i}/', 
            document_root=directory
        )
    
    # 특별히 insurance_portal static 파일들 서빙
    insurance_static_dirs = [
        settings.BASE_DIR / "0826-5" / "insurance_portal" / "static",
        settings.BASE_DIR / "insurance_portal" / "static",
    ]
    
    for directory in insurance_static_dirs:
        if directory.exists():
            urlpatterns += static('/static/', document_root=directory)

# ============================================================================
# 커스텀 정적 파일 서빙 (폴백)
# ============================================================================

def serve_static_fallback(request, path):
    """정적 파일 폴백 서빙"""
    # insurance_portal 정적 파일 우선 검색
    static_dirs = [
        settings.BASE_DIR / "0826-5" / "insurance_portal" / "static",
        settings.BASE_DIR / "insurance_portal" / "static",
    ]
    
    for static_dir in static_dirs:
        full_path = static_dir / path
        if full_path.exists() and full_path.is_file():
            return serve(request, str(full_path.relative_to(static_dir)), document_root=static_dir)
    
    # 기본 STATIC_ROOT에서 검색
    if settings.STATIC_ROOT and (settings.STATIC_ROOT / path).exists():
        return serve(request, path, document_root=settings.STATIC_ROOT)
    
    raise Http404("Static file not found")

# 정적 파일 폴백 URL 패턴 추가
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve_static_fallback),
]

# ============================================================================
# 헬스체크 및 디버그 엔드포인트
# ============================================================================

def health_check(request):
    """헬스체크 엔드포인트"""
    return HttpResponse("OK", content_type="text/plain")

def static_debug(request):
    """정적 파일 디버그 정보"""
    if not settings.DEBUG:
        raise Http404()
    
    info = {
        "STATIC_URL": settings.STATIC_URL,
        "STATIC_ROOT": str(settings.STATIC_ROOT) if settings.STATIC_ROOT else None,
        "STATICFILES_DIRS": [str(d) for d in settings.STATICFILES_DIRS],
        "existing_dirs": [],
    }
    
    # 실제 존재하는 디렉토리 체크
    for directory in settings.STATICFILES_DIRS:
        if directory.exists():
            info["existing_dirs"].append({
                "path": str(directory),
                "files_count": len(list(directory.rglob("*"))) if directory.is_dir() else 0
            })
    
    import json
    return HttpResponse(
        json.dumps(info, indent=2), 
        content_type="application/json"
    )

urlpatterns += [
    path('health/', health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += [
        path('debug/static/', static_debug, name='static_debug'),
    ]

# ============================================================================
# 에러 페이지 핸들러
# ============================================================================

handler404 = 'insurance_portal.views.custom_404'
handler500 = 'insurance_portal.views.custom_500'

print(f"✅ URLs configured - {len(urlpatterns)} patterns")
print(f"✅ Debug mode: {settings.DEBUG}")
if settings.DEBUG:
    print(f"✅ Static file serving enabled for {len(settings.STATICFILES_DIRS)} directories")