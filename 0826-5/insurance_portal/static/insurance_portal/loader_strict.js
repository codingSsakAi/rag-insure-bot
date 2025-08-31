/* insurance_portal/loader_strict.js
 * 목적: 깨진 Font Awesome CDN 링크 교체 + 안전한 동적 주입 + 폴백
 * 원인: 기존 href가 cdnjs 경로에서 "/ajax/libs/" 대신 "/ajax/l..." 형태로 잘려 404 발생.
 * 증상: 콘솔에 "blocked by CORS" + 404, 아이콘 미표시.
 */

(function () {
  const LOG_PREFIX = "[LOADER-STRICT]";
  const HEAD = document.head || document.getElementsByTagName("head")[0];

  // 이미 실행/주입했는지 가드
  if (window.__INS_PORTAL_LOADER_STRICT__) {
    console.info(LOG_PREFIX, "already initialized, skipping.");
    return;
  }
  window.__INS_PORTAL_LOADER_STRICT__ = true;

  // ===== 1) 깨진 FA 링크 제거 =====
  // '/ajax/l' 같은 비정상 경로를 선제적으로 제거
  try {
    const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
    links.forEach((lnk) => {
      const href = (lnk.getAttribute("href") || "").trim();
      if (!href) return;

      // cdnjs인데 '/ajax/l' 로 시작하거나, 'fontawesome'인데 확실히 깨진 패턴들
      const looksBroken =
        href.includes("cdnjs.cloudflare.com/ajax/l") ||
        href.includes("cloudflare.com/ajax/l") ||
        (href.includes("fontawesome") && !href.includes("/css/")) ||
        (/ajax\/l[^i]/.test(href)); // 'libs' 전개가 아닌 경우 대충 걸러냄

      if (looksBroken) {
        console.warn(LOG_PREFIX, "Removing broken FA stylesheet:", href);
        lnk.parentNode && lnk.parentNode.removeChild(lnk);
      }
    });
  } catch (e) {
    console.warn(LOG_PREFIX, "broken-link cleanup failed:", e);
  }

  // ===== 2) FA 로딩 상태 체크 =====
  function hasFAClassDefined() {
    // 폰트어썸이 올라오면 .fa, .fas 중 하나라도 스타일이 잡힌다.
    const testEl = document.createElement("i");
    testEl.className = "fas fa-image";
    testEl.style.position = "absolute";
    testEl.style.left = "-9999px";
    document.body.appendChild(testEl);

    // 계산된 스타일로 폰트 패밀리/가상 컨텐츠를 간접 확인
    const styles = window.getComputedStyle(testEl);
    const fontFamily = styles.getPropertyValue("font-family") || "";
    const beforeContent = window.getComputedStyle(testEl, ":before").getPropertyValue("content") || "";

    document.body.removeChild(testEl);
    // v5 기준으로 font-family에 'Font Awesome'이 들어오거나, :before content가 비어있지 않으면 로드된 걸로 간주
    return /Font Awesome/i.test(fontFamily) || (beforeContent && beforeContent !== "none" && beforeContent !== "\"\"");
  }

  if (hasFAClassDefined()) {
    console.info(LOG_PREFIX, "Font Awesome already present.");
    return;
  }

  // ===== 3) 동적 주입 + 폴백 체인 =====
  const CANDIDATES = [
  "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css",
  "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css",
  "https://unpkg.com/@fortawesome/fontawesome-free@6.5.2/css/all.min.css"
    ];

  function injectStylesheet(href, onload, onerror) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    // SRI/crossorigin은 환경에 따라 차단 요인이 될 수 있어 제거(간단/확실 우선)
    link.onload = onload;
    link.onerror = onerror;
    HEAD.appendChild(link);
    return link;
  }

  let tried = 0;
  function tryNext() {
    if (tried >= CANDIDATES.length) {
      console.error(LOG_PREFIX, "All Font Awesome CDN fallbacks failed. Icons may not render.");
      return;
    }
    const href = CANDIDATES[tried++];
    console.info(LOG_PREFIX, "Loading Font Awesome:", href);

    injectStylesheet(
      href,
      function () {
        // 약간의 렌더 지연 후 확인
        setTimeout(function () {
          if (hasFAClassDefined()) {
            console.info(LOG_PREFIX, "Font Awesome loaded successfully from:", href);
          } else {
            console.warn(LOG_PREFIX, "Loaded but not detected, trying next fallback…");
            tryNext();
          }
        }, 60);
      },
      function () {
        console.warn(LOG_PREFIX, "Failed to load:", href, " → trying fallback…");
        tryNext();
      }
    );
  }

  // DOM 준비 시점에 주입 (이미 DOMContentLoaded가 끝났다면 즉시 실행)
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tryNext);
  } else {
    tryNext();
  }
})();
