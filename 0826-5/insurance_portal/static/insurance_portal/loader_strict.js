// 0826-5/insurance_portal/static/insurance_portal/loader_strict.js
// CORS 완전 차단 및 안전 리소스만 로드

(function () {
  if (window.__PORTAL_LOADER__) return;
  window.__PORTAL_LOADER__ = true;

  const log = (...args) => console.log("[portal-loader]", ...args);
  
  // ✅ CORS 안전한 리소스만 정의
  const SAFE_RESOURCES = {
    // Font Awesome (미들웨어에서도 주입하지만 중복 방지)
    fontawesome: "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css",
    // Bootstrap (필요시)
    bootstrap: "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
  };

  // ❌ 절대 로드하지 않을 위험한 도메인들
  const BLOCKED_DOMAINS = [
    'cdnjs.cloudflare.com',
    'unpkg.com', 
    'maxcdn.bootstrapcdn.com',
    'stackpath.bootstrapcdn.com'
  ];

  // 안전한 리소스 로드 함수
  const loadSafeResource = (url, type = 'css') => {
    // 차단된 도메인 체크
    if (BLOCKED_DOMAINS.some(domain => url.includes(domain))) {
      log(`🚫 Blocked unsafe domain: ${url}`);
      return null;
    }

    if (type === 'css') {
      // CSS 중복 로드 방지
      if (document.querySelector(`link[href="${url}"]`)) {
        log(`⏭️ Already loaded: ${url}`);
        return null;
      }

      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = url;
      
      if (url.includes('cdn.jsdelivr.net')) {
        link.crossOrigin = 'anonymous';
        link.referrerPolicy = 'no-referrer';
      }

      link.onload = () => log(`✅ CSS loaded: ${url}`);
      link.onerror = () => log(`❌ CSS failed: ${url}`);
      
      document.head.appendChild(link);
      return link;
      
    } else if (type === 'js') {
      // JS 중복 로드 방지
      if (document.querySelector(`script[src="${url}"]`)) {
        log(`⏭️ Already loaded: ${url}`);
        return null;
      }

      const script = document.createElement('script');
      script.src = url;
      script.defer = true;
      
      if (url.includes('cdn.jsdelivr.net')) {
        script.crossOrigin = 'anonymous';
        script.referrerPolicy = 'no-referrer';
      }

      script.onload = () => log(`✅ JS loaded: ${url}`);
      script.onerror = () => log(`❌ JS failed: ${url}`);
      
      document.head.appendChild(script);
      return script;
    }
  };

  // 로컬 파일 존재 확인 (HEAD 요청)
  const checkLocalFile = async (url) => {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      return response.ok;
    } catch {
      return false;
    }
  };

  // 메인 로더 함수
  const initPortalLoader = async () => {
    log("🚀 Starting safe portal loader...");

    try {
      // 1. 필수 외부 리소스 (안전한 CDN만)
      if (!document.querySelector('link[href*="fontawesome"]')) {
        loadSafeResource(SAFE_RESOURCES.fontawesome, 'css');
      }

      // 2. 로컬 CSS 파일들 (순서대로)
      const cssFiles = [
        "/static/insurance_portal/css/portal.css",
        "/static/insurance_portal/css/chatbot.css", 
        "/static/insurance_portal/css/fab.css"
      ];

      let loadedCSS = 0;
      for (const cssFile of cssFiles) {
        const exists = await checkLocalFile(cssFile);
        if (exists) {
          loadSafeResource(cssFile, 'css');
          loadedCSS++;
        } else {
          log(`⚠️ CSS not found: ${cssFile}`);
        }
      }

      // 3. 로컬 JS 파일들 (의존성 순서)
      const jsFiles = [
        "/static/insurance_portal/js/navigation_handler.js",
        "/static/insurance_portal/js/chatbot.js",
        "/static/insurance_portal/js/fab-controller.js",
        "/static/insurance_portal/js/guide.js",
        "/static/insurance_portal/js/knowhow.js",
        "/static/insurance_portal/js/claim_knowledge.js"
      ];

      let loadedJS = 0;
      for (const jsFile of jsFiles) {
        const exists = await checkLocalFile(jsFile);
        if (exists) {
          loadSafeResource(jsFile, 'js');
          loadedJS++;
        } else {
          log(`⚠️ JS not found: ${jsFile}`);
        }
      }

      log(`✅ Loader completed - CSS: ${loadedCSS}/${cssFiles.length}, JS: ${loadedJS}/${jsFiles.length}`);
      
      // 로딩 완료 이벤트 발생
      document.dispatchEvent(new CustomEvent('portalLoaderReady', {
        detail: { cssCount: loadedCSS, jsCount: loadedJS }
      }));

    } catch (error) {
      log(`❌ Loader error:`, error);
    }
  };

  // CORS 에러 전역 핸들러 설치
  const installCORSHandler = () => {
    let blockedCount = 0;

    // 리소스 로드 실패 처리
    window.addEventListener('error', (e) => {
      const target = e.target;
      if (target && (target.tagName === 'LINK' || target.tagName === 'SCRIPT')) {
        const url = target.href || target.src;
        if (url && BLOCKED_DOMAINS.some(domain => url.includes(domain))) {
          blockedCount++;
          log(`🚫 Blocked unsafe resource #${blockedCount}: ${url}`);
          e.preventDefault();
          e.stopPropagation();
          return false;
        }
      }
    }, true);

    // Promise rejection 처리
    window.addEventListener('unhandledrejection', (e) => {
      if (e.reason && String(e.reason).toLowerCase().includes('cors')) {
        log('🚫 CORS rejection blocked');
        e.preventDefault();
      }
    });

    // 주기적 차단 리포트
    setInterval(() => {
      if (blockedCount > 0) {
        log(`🛡️ Total blocked resources: ${blockedCount}`);
      }
    }, 30000); // 30초마다
  };

  // 페이지 로드 시 초기화
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      installCORSHandler();
      setTimeout(initPortalLoader, 100);
    });
  } else {
    installCORSHandler();
    initPortalLoader();
  }

  // 디버그 API 제공
  window.__PORTAL_DEBUG__ = {
    loadSafeResource,
    checkLocalFile,
    SAFE_RESOURCES,
    BLOCKED_DOMAINS,
    log
  };

  log("🛡️ CORS-safe portal loader initialized");

})();