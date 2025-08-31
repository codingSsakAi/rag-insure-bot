/* eslint-disable no-console */
(function () {
  const LOG_PREFIX = "[portal-loader]";
  const quiet = false; // 필요시 true로 바꿔 콘솔 출력 최소화

  const log = (...args) => !quiet && console.log(LOG_PREFIX, ...args);
  const warn = (...args) => !quiet && console.warn(LOG_PREFIX, ...args);
  const err = (...args) => !quiet && console.error(LOG_PREFIX, ...args);

  // ─────────────────────────────────────────────────────────
  // 설정: 최소한의 후보만 사용 (불필요한 404 소음 제거)
  // ─────────────────────────────────────────────────────────
  const PORTAL_CSS_CANDIDATES = [
    "/static/insurance_portal/css/portal.css",
    "/static/insurance_portal/portal.css",
  ];

  const PORTAL_JS_CANDIDATES = [
    "/static/insurance_portal/js/portal.js",
    "/static/insurance_portal/portal.js",
  ];

  // Font Awesome 로컬 경로 (아카이브에 포함되어 있어야 함)
  const LOCAL_FA_CSS = "/static/insurance_portal/vendor/fontawesome/css/all.min.css";

  // cdnjs/jsdelivr 경로(깨지는 링크) 감지용
  const CDN_FA_REGEX = /https?:\/\/(?:cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net)[^"']*(?:font-?awesome|\/all(?:\.min)?\.css)/i;

  // ─────────────────────────────────────────────────────────
  // util: HEAD로 존재 확인 (동일 오리진만)
  // ─────────────────────────────────────────────────────────
  async function probe(url) {
    try {
      const res = await fetch(url, { method: "HEAD", cache: "no-store" });
      return res.ok;
    } catch {
      return false;
    }
  }

  function injectLink(href) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `${href}?v=1`;
    document.head.appendChild(link);
    return link;
  }

  function injectScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = `${src}?v=1`;
      s.defer = true;
      s.onload = resolve;
      s.onerror = () => reject(new Error(`Fail ${src}`));
      document.head.appendChild(s);
    });
  }

  // ─────────────────────────────────────────────────────────
  // 1) 깨진 CDN Font Awesome <link> 제거
  // ─────────────────────────────────────────────────────────
  function stripBrokenCDNFA() {
    const links = Array.from(document.querySelectorAll('link[rel="stylesheet"][href]'));
    let removed = 0;
    for (const el of links) {
      const href = el.getAttribute("href") || "";
      if (CDN_FA_REGEX.test(href)) {
        el.parentNode && el.parentNode.removeChild(el);
        removed++;
        warn("removed external Font Awesome link:", href);
      }
    }
    return removed;
  }

  // 이미 Font Awesome가 있는지 대략 체크
  function hasLocalFA() {
    const links = Array.from(document.querySelectorAll('link[rel="stylesheet"][href]'));
    return links.some((el) => (el.getAttribute("href") || "").includes("vendor/fontawesome"));
  }

  // ─────────────────────────────────────────────────────────
  // 2) 최소한의 CSS/JS만 로드(존재하는 것만)
  // ─────────────────────────────────────────────────────────
  async function smartLoad() {
    // Font Awesome CDN 링크 제거 → 없으면 로컬 주입
    const removed = stripBrokenCDNFA();
    if (!hasLocalFA()) {
      const ok = await probe(LOCAL_FA_CSS);
      if (ok) {
        injectLink(LOCAL_FA_CSS);
        log("local FA injected:", LOCAL_FA_CSS);
      } else if (removed) {
        warn("local FA missing:", LOCAL_FA_CSS);
      }
    }

    // Portal CSS
    for (const u of PORTAL_CSS_CANDIDATES) {
      if (await probe(u)) {
        injectLink(u);
        log("CSS", u);
        break; // 첫 성공만
      }
    }

    // Portal JS
    for (const u of PORTAL_JS_CANDIDATES) {
      if (await probe(u)) {
        try {
          await injectScript(u);
          log("JS", u);
          break; // 첫 성공만
        } catch (e) {
          err("JS load failed:", u, e);
        }
      }
    }
  }

  // ─────────────────────────────────────────────────────────
  // Bootstrap
  // ─────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    log("bootstrap");
    smartLoad().catch((e) => err("bootstrap failed:", e));
  });
})();
