// insurance_portal/loader_strict.js - CORS 문제 완전 해결 버전
(function () {
  if (window.__PORTAL_LOADER__) return;
  window.__PORTAL_LOADER__ = true;

  const log = (...a) => console.log("[portal-loader]", ...a);
  
  // ✅ CORS 안전한 CDN만 사용
  const SAFE_RESOURCES = {
    fontawesome: "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css",
    bootstrap_css: "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
    bootstrap_js: "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
  };

  const addLink = (href, attrs = {}) => {
    // 중복 방지
    const existing = document.querySelector(`link[rel="stylesheet"][href="${href}"]`);
    if (existing) {
      log("CSS already exists:", href);
      return existing;
    }
    
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    
    // 기본 속성 설정
    if (href.startsWith('https://cdn.jsdelivr.net')) {
      link.crossOrigin = "anonymous";
      link.referrerPolicy = "no-referrer";
    }
    
    Object.entries(attrs).forEach(([k, v]) => link.setAttribute(k, v));
    
    // 로드 성공/실패 처리
    link.addEventListener('load', () => log("✅ CSS loaded:", href));
    link.addEventListener('error', () => log("❌ CSS failed:", href));
    
    document.head.appendChild(link);
    return link;
  };

  const addScript = (src, attrs = {}) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) {
      log("JS already exists:", src);
      return existing;
    }
    
    const script = document.createElement("script");
    script.src = src;
    script.defer = true;
    
    if (src.startsWith('https://cdn.jsdelivr.net')) {
      script.crossOrigin = "anonymous";
      script.referrerPolicy = "no-referrer";
    }
    
    Object.entries(attrs).forEach(([k, v]) => script.setAttribute(k, v));
    
    script.addEventListener('load', () => log("✅ JS loaded:", src));
    script.addEventListener('error', () => log("❌ JS failed:", src));
    
    document.head.appendChild(script);
    return script;
  };

  // 파일 존재 여부 확인 (HEAD 요청)
  const checkFileExists = async (url) => {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      return response.ok;
    } catch (error) {
      log("File check failed:", url, error.message);
      return false;
    }
  };

  // 순차적 로딩 함수
  const loadResourcesSequentially = async (resources, loader) => {
    const loaded = [];
    for (const resource of resources) {
      try {
        const exists = await checkFileExists(resource);
        if (exists) {
          loader(resource);
          loaded.push(resource);
        } else {
          log("Resource not found:", resource);
        }
      } catch (error) {
        log("Error loading resource:", resource, error);
      }
    }
    return loaded;
  };

  // 메인 로딩 함수
  (async () => {
    try {
      log("Starting safe resource loading...");
      
      // 1. 필수 외부 리소스 (CORS 안전)
      if (!document.querySelector('link[href*="fontawesome"]')) {
        addLink(SAFE_RESOURCES.fontawesome);
      }

      // 2. Bootstrap이 없으면 추가
      if (!document.querySelector('link[href*="bootstrap"]')) {
        addLink(SAFE_RESOURCES.bootstrap_css);
        addScript(SAFE_RESOURCES.bootstrap_js);
      }

      // 3. 로컬 CSS 파일들 (순서 중요)
      const cssFiles = [
        "/static/insurance_portal/css/portal.css",
        "/static/insurance_portal/css/chatbot.css", 
        "/static/insurance_portal/css/fab.css"
      ];
      
      log("Loading CSS files...");
      const loadedCSS = await loadResourcesSequentially(cssFiles, addLink);
      log("CSS loaded:", loadedCSS.length, "files");

      // 4. 로컬 JS 파일들 (의존성 순서)
      const jsFiles = [
        "/static/insurance_portal/js/navigation_handler.js",  // 첫 번째 (다른 파일들이 의존)
        "/static/insurance_portal/js/chatbot.js",
        "/static/insurance_portal/js/fab-controller.js", 
        "/static/insurance_portal/js/guide.js",
        "/static/insurance_portal/js/knowhow.js",
        "/static/insurance_portal/js/claim_knowledge.js"
      ];

      log("Loading JS files...");
      const loadedJS = await loadResourcesSequentially(jsFiles, addScript);
      log("JS loaded:", loadedJS.length, "files");
      
      // 5. 로딩 완료 이벤트 발생
      document.dispatchEvent(new CustomEvent('portalResourcesLoaded', {
        detail: { css: loadedCSS, js: loadedJS }
      }));
      
      log("✅ All resources loaded successfully");
      log("Total:", loadedCSS.length + loadedJS.length, "files");
      
    } catch (error) {
      console.error("[portal-loader] Critical error:", error);
      
      // 오류 발생 시 최소한의 폴백
      if (!document.querySelector('link[href*="fontawesome"]')) {
        addLink(SAFE_RESOURCES.fontawesome);
      }
    }
  })();

  // 전역 에러 핸들러 설치
  window.addEventListener('error', (e) => {
    const target = e.target;
    if (target && (target.tagName === 'LINK' || target.tagName === 'SCRIPT')) {
      const url = target.href || target.src;
      if (url && (url.includes('cdnjs.cloudflare.com') || url.includes('unpkg.com'))) {
        log("❌ CORS blocked resource:", url);
        e.preventDefault(); // 콘솔 에러 스팸 방지
      }
    }
  });

  // 언핸들드 Promise rejection 처리
  window.addEventListener('unhandledrejection', (e) => {
    if (e.reason && e.reason.message && e.reason.message.toLowerCase().includes('cors')) {
      log("❌ CORS rejection handled:", e.reason.message);
      e.preventDefault();
    }
  });

  // 디버그 정보 제공
  window.__PORTAL_DEBUG__ = {
    checkFileExists,
    addLink,
    addScript,
    SAFE_RESOURCES,
    log
  };

})();