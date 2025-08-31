// insurance_portal/static/insurance_portal/loader_strict.js
(() => {
  const DEBUG = true;
  const log  = (...a) => { if (DEBUG) console.log('[portal-loader]', ...a); };
  const warn = (...a) => console.warn('[portal-loader]', ...a);

  function addCss(href, id) {
    return new Promise((resolve, reject) => {
      const el = document.createElement('link');
      el.rel = 'stylesheet';
      el.href = href;
      el.crossOrigin = 'anonymous'; // 폰트 CORS 대응
      if (id) el.id = id;
      el.onload = () => resolve({ ok: true, href });
      el.onerror = () => reject(new Error('css load failed: ' + href));
      document.head.appendChild(el);
    });
  }

  function addJs(src) {
    return new Promise((resolve, reject) => {
      const el = document.createElement('script');
      el.src = src;
      el.defer = true;
      el.onload = () => resolve({ ok: true, src });
      el.onerror = () => reject(new Error('js load failed: ' + src));
      document.head.appendChild(el);
    });
  }

  // 동기 HEAD(동일 오리진만)로 존재 확인 → 404 폭주 방지
  function existsLocal(path) {
    try {
      const xhr = new XMLHttpRequest();
      xhr.open('HEAD', path, false);
      xhr.send(null);
      return xhr.status >= 200 && xhr.status < 400;
    } catch (e) {
      return false;
    }
  }

  // ✅ 실제 아카이브 구조에 맞춘 후보
  const CSS_CANDIDATES = [
    '/static/insurance_portal/css/portal.bundle.css',
    '/static/insurance_portal/css/portal.css',
    '/static/insurance_portal/portal.css',
  ];
  const JS_CANDIDATES = [
    '/static/insurance_portal/js/portal.bundle.js',
    '/static/insurance_portal/js/portal.js',
    '/static/insurance_portal/portal.js',
  ];

  // Font Awesome
  const FA_LOCAL = '/static/insurance_portal/vendor/fontawesome/css/all.min.css';
  const FA_CDN_FALLBACKS = [
    'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@5.15.4/css/all.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',
  ];

  function hasFontAwesomeLink() {
    return Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
      .some(l => /fontawesome|font-awesome|all\.min\.css/i.test(l.href));
  }

  async function ensurePortalAssets() {
    const needCss = !document.querySelector(
      'link[href*="portal.bundle.css"],link[href$="/portal.css"],link#portal-css'
    );
    const needJs = !document.querySelector(
      'script[src*="portal.bundle.js"],script[src$="/portal.js"]'
    );

    if (needCss) {
      for (const href of CSS_CANDIDATES) {
        if (href.startsWith('/static/') && existsLocal(href)) {
          try { await addCss(href, 'portal-css'); log('css loaded', href); break; }
          catch (e) { warn('css failed', href, e); }
        }
      }
    }
    if (needJs) {
      for (const src of JS_CANDIDATES) {
        if (src.startsWith('/static/') && existsLocal(src)) {
          try { await addJs(src); log('js loaded', src); break; }
          catch (e) { warn('js failed', src, e); }
        }
      }
    }
  }

  async function ensureFontAwesome() {
    // 기존 CDN 링크가 있으면 그대로 둔다(더 이상 제거하지 않음)
    if (hasFontAwesomeLink()) return;

    // 1) 로컬 벤더가 있으면 우선
    if (existsLocal(FA_LOCAL)) {
      try { await addCss(FA_LOCAL, 'fa-css'); log('Font Awesome (local) loaded'); return; }
      catch (e) { warn('local FA failed', e); }
    }
    // 2) CDN 후보 주입 (HEAD 프리플라이트 없이 바로 주입)
    for (const cdn of FA_CDN_FALLBACKS) {
      try { await addCss(cdn, 'fa-css'); log('Font Awesome (CDN) loaded', cdn); return; }
      catch (e) { warn('CDN FA failed', cdn, e); }
    }
    warn('Font Awesome could not be loaded from any source');
  }

  (async function bootstrap() {
    try {
      await ensurePortalAssets();
      await ensureFontAwesome();
    } catch (e) {
      warn('bootstrap error', e);
    }
  })();
})();
