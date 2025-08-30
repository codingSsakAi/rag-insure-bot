// static/insurance_portal/loader_strict.js
// 레거시 포털 로더를 '존재만 하는' no-op으로 대체하고,
// 혹시 이전 스크립트가 뒤늦게 요소를 만들더라도 10초간 주기적으로 제거합니다.

(function () {
  function nukeLegacy() {
    ['ip-fab', 'ip-overlay', 'ip-panel', 'ip-fallback'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
  }

  // 로더가 기대하는 엔트리 존재만 충족 (아무 것도 만들지 않음)
  window.__PORTAL_ENTRY__ = function () {
    nukeLegacy();
    var tries = 0;
    var timer = setInterval(function () {
      nukeLegacy();
      if (++tries > 50) clearInterval(timer); // 50 * 200ms = 10초
    }, 200);
  };

  // 안전하게 우리가 호출
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window.__PORTAL_ENTRY__);
  } else {
    window.__PORTAL_ENTRY__();
  }

  // 호환용 no-op API
  window.IPORTAL = window.IPORTAL || {};
  ['open', 'close', 'mount', 'unmount'].forEach(function (k) {
    window.IPORTAL[k] = function () {};
  });
})();
