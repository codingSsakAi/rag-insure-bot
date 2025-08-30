// static/insurance_portal/portal.js
// 3선 FAB/사이드패널을 만들던 레거시 코드를 완전히 무력화(no-op) 합니다.

(function () {
  function nuke() {
    ['ip-fab', 'ip-overlay', 'ip-panel', 'ip-fallback'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', nuke);
  } else {
    nuke();
  }
  window.addEventListener('load', nuke);

  // 호환용 no-op
  window.IPORTAL = window.IPORTAL || {};
  ['open', 'close', 'mount', 'unmount'].forEach(function (k) {
    window.IPORTAL[k] = function () {};
  });

  // ✅ 의도적으로 아무 것도 생성하지 않음
})();
