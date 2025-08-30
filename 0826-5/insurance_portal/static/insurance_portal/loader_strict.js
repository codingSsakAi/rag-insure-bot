// static/insurance_portal/loader_strict.js
// ──────────────────────────────────────────────────────────────────────────────
// 레거시 포털 로더를 완전히 비활성화합니다.
// - 외부 CSS/JS 로딩 안 함
// - 자동 탐지/마운트 안 함
// - fallbackButton(≡) 생성 절대 안 함
// - 혹시 남아 있는 잔여 노드(ip-*)는 로드 시 즉시 제거
// - 호환을 위해 IPORTAL API만 no-op으로 노출
// ──────────────────────────────────────────────────────────────────────────────
(function () {
  function removeLegacyNodes() {
    ['ip-fab', 'ip-overlay', 'ip-panel', 'ip-fallback'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
  }

  // 페이지 수명주기 언제 들어와도 깨끗하게
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', removeLegacyNodes);
  } else {
    removeLegacyNodes();
  }
  window.addEventListener('load', removeLegacyNodes);

  // 다른 스크립트가 IPORTAL을 기대해도 에러 안 나게 no-op 제공
  window.IPORTAL = window.IPORTAL || {};
  ['mount', 'unmount', 'open', 'close'].forEach(function (k) {
    window.IPORTAL[k] = function () {};
  });

  // 과거 커스텀 엔트리를 기대하더라도 아무 것도 하지 않는 no-op 제공
  window.__PORTAL_ENTRY__ = function () {};
})();
