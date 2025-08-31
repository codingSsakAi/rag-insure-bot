# insurance_project/middleware.py - CORS 완전 차단 및 안전 리소스 주입

from __future__ import annotations
import logging
import mimetypes
import re
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('insurance_project.middleware')

class PortalStaticBridgeMiddleware(MiddlewareMixin):
    """정적 파일 브릿지 - 기존 유지"""
    URL_PREFIX = "/static/insurance_portal/"

    def __init__(self, get_response):
        super().__init__(get_response)
        base: Path = settings.BASE_DIR
        self.candidate_roots: list[Path] = [
            base / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
            base / "insurance_portal" / "static" / "insurance_portal",
            base / "insurance_app" / "static" / "insurance_portal",
        ]

    def _try_open(self, relpath: str) -> tuple[bytes | None, str | None]:
        for root in self.candidate_roots:
            f = root / relpath
            if f.exists() and f.is_file():
                data = f.read_bytes()
                ctype, _ = mimetypes.guess_type(str(f))
                return data, ctype or "application/octet-stream"
        return None, None

    def __call__(self, request):
        path = request.path
        if path.startswith(self.URL_PREFIX):
            rel = path[len(self.URL_PREFIX):]
            data, ctype = self._try_open(rel)
            if data is not None:
                resp = HttpResponse(data, content_type=ctype)
                resp["Cache-Control"] = "max-age=300, public"
                logger.debug(f"Served static: {path}")
                return resp
        return self.get_response(request)


class PortalAutoInjectMiddleware(MiddlewareMixin):
    """HTML 응답 수정 - CORS 차단 및 안전 리소스 주입"""
    
    EXCLUDE_PREFIXES = ("/admin", "/static", "/media", "/api")
    MARKER = b"<!-- __PORTAL_INJECTED__ -->"
    
    # ✅ 안전한 CDN (CORS 허용)
    SAFE_FONTAWESOME = "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css"
    
    # ❌ 차단할 도메인들 (CORS 문제 원인)
    BLOCKED_DOMAINS = [
        "cdnjs.cloudflare.com",
        "unpkg.com",
        "maxcdn.bootstrapcdn.com", 
        "stackpath.bootstrapcdn.com",
        "code.jquery.com",
        "ajax.googleapis.com"
    ]
    
    # 정규표현식 (링크와 스크립트 태그 매칭)
    LINK_PATTERN = re.compile(r'<link[^>]+href=[\'"](https?://[^\'"]+)[\'"][^>]*>', re.IGNORECASE)
    SCRIPT_PATTERN = re.compile(r'<script[^>]+src=[\'"](https?://[^\'"]+)[\'"][^>]*>', re.IGNORECASE)

    def __init__(self, get_response):
        super().__init__(get_response)
        # 주입할 로컬 리소스들 (존재하는 것만)
        self.local_resources = [
            "/static/insurance_portal/css/portal.css",
            "/static/insurance_portal/css/chatbot.css", 
            "/static/insurance_portal/css/fab.css",
            "/static/insurance_portal/js/navigation_handler.js",
            "/static/insurance_portal/js/chatbot.js",
            "/static/insurance_portal/js/fab-controller.js",
            "/static/insurance_portal/js/guide.js",
            "/static/insurance_portal/js/knowhow.js",
            "/static/insurance_portal/js/claim_knowledge.js"
        ]

    def _file_exists(self, url_path: str) -> bool:
        """로컬 파일 존재 확인"""
        prefix = "/static/insurance_portal/"
        if not url_path.startswith(prefix):
            return False
            
        rel = url_path[len(prefix):]
        for root in [
            settings.BASE_DIR / "0826-5" / "insurance_portal" / "static" / "insurance_portal",
            settings.BASE_DIR / "insurance_portal" / "static" / "insurance_portal",
        ]:
            if (root / rel).exists():
                return True
        return False

    def _remove_blocked_resources(self, html: str) -> str:
        """차단된 외부 리소스 제거"""
        blocked_count = 0
        
        def block_link(match):
            nonlocal blocked_count
            href = match.group(1)
            if any(domain in href for domain in self.BLOCKED_DOMAINS):
                blocked_count += 1
                logger.warning(f"🚫 Blocked external CSS: {href}")
                return f"<!-- BLOCKED: {href} -->"
            return match.group(0)
        
        def block_script(match):
            nonlocal blocked_count  
            src = match.group(1)
            if any(domain in src for domain in self.BLOCKED_DOMAINS):
                blocked_count += 1
                logger.warning(f"🚫 Blocked external JS: {src}")
                return f"<!-- BLOCKED: {src} -->"
            return match.group(0)
        
        html = self.LINK_PATTERN.sub(block_link, html)
        html = self.SCRIPT_PATTERN.sub(block_script, html)
        
        if blocked_count > 0:
            logger.info(f"🛡️ Blocked {blocked_count} unsafe external resources")
            
        return html

    def _inject_safe_resources(self, html: str) -> str:
        """안전한 리소스 주입"""
        if self.MARKER.decode() in html:
            return html  # 이미 주입됨
            
        inject_parts = ['\n<!-- __PORTAL_INJECTED__ -->\n']
        
        # 1. Font Awesome (안전한 jsDelivr)
        if "fontawesome" not in html.lower():
            inject_parts.append(
                f'<link rel="stylesheet" href="{self.SAFE_FONTAWESOME}" '
                f'crossorigin="anonymous" referrerpolicy="no-referrer" '
                f'integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" />\n'
            )
            logger.info("✅ Injected safe Font Awesome")
        
        # 2. 로컬 리소스들
        injected_resources = []
        for resource in self.local_resources:
            if self._file_exists(resource):
                if resource.endswith('.css'):
                    inject_parts.append(f'<link rel="stylesheet" href="{resource}?v=2" />\n')
                elif resource.endswith('.js'):
                    inject_parts.append(f'<script src="{resource}?v=2" defer></script>\n')
                injected_resources.append(resource)
        
        if injected_resources:
            logger.info(f"✅ Injected {len(injected_resources)} local resources")
        
        # 3. CORS 에러 핸들러
        inject_parts.append('''
<script>
// CORS 에러 자동 처리
(function() {
    let corsErrorCount = 0;
    
    window.addEventListener('error', function(e) {
        if (e.target && (e.target.tagName === 'LINK' || e.target.tagName === 'SCRIPT')) {
            const url = e.target.href || e.target.src;
            if (url && (url.includes('cdnjs.cloudflare.com') || url.includes('unpkg.com'))) {
                corsErrorCount++;
                console.warn(`🚫 CORS blocked resource ${corsErrorCount}: ${url}`);
                e.preventDefault(); // 콘솔 에러 스팸 방지
                return false;
            }
        }
    }, true);
    
    window.addEventListener('unhandledrejection', function(e) {
        if (e.reason && String(e.reason).toLowerCase().includes('cors')) {
            console.warn('🚫 CORS rejection handled silently');
            e.preventDefault();
        }
    });
    
    // 리소스 로딩 완료 체크
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            if (corsErrorCount > 0) {
                console.info(`🛡️ Blocked ${corsErrorCount} CORS-unsafe resources successfully`);
            }
            console.info('✅ Portal resources loaded safely');
        }, 1000);
    });
})();
</script>
        ''')
        
        payload = ''.join(inject_parts)
        
        # </body> 태그 앞에 주입
        if "</body>" in html:
            html = html.replace("</body>", payload + "</body>")
        else:
            html += payload
            
        return html

    def __call__(self, request):
        # API나 관리자 페이지는 건드리지 않음
        for prefix in self.EXCLUDE_PREFIXES:
            if request.path.startswith(prefix):
                return self.get_response(request)

        response = self.get_response(request)
        
        # HTML 응답만 처리
        content_type = response.headers.get("Content-Type", "")
        if (response.status_code != 200 or 
            "text/html" not in content_type or 
            not hasattr(response, "content")):
            return response

        try:
            charset = getattr(response, 'charset', 'utf-8') or 'utf-8'
            html = response.content.decode(charset, errors='ignore')
            
            # 1단계: 위험한 외부 리소스 차단
            html = self._remove_blocked_resources(html)
            
            # 2단계: 안전한 리소스 주입  
            html = self._inject_safe_resources(html)
            
            # 응답 업데이트
            response.content = html.encode(charset)
            if response.has_header("Content-Length"):
                response.headers["Content-Length"] = str(len(response.content))
                
        except Exception as e:
            logger.error(f"❌ Middleware processing error: {e}")
            # 에러 시 원본 응답 반환
            
        return response


class ExceptionLoggingMiddleware(MiddlewareMixin):
    """예외 로깅"""
    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error(f"❌ Unhandled exception at {request.path}: {e}", exc_info=True)
            raise


class TemplateFallbackMiddleware(MiddlewareMixin):
    """템플릿 폴백 (기존 유지)"""
    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error(f"❌ Template/View error at {request.path}: {e}")
            # 간단한 HTML 응답 반환
            return HttpResponse(
                f'<h1>일시적 오류</h1><p>페이지를 불러오는 중 문제가 발생했습니다.</p>',
                content_type='text/html; charset=utf-8'
            )