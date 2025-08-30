// static/insurance_portal/portal.js
// 3선 FAB과 사이드 패널을 생성하던 코드를 전부 제거한 no-op 버전.
// 다른 코드가 window.IPORTAL.* 를 호출해도 에러가 없도록 스텁만 제공.

(function () {
  function nukeLegacy() {
    ['ip-fab', 'ip-overlay', 'ip-panel'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', nukeLegacy);
  } else {
    nukeLegacy();
  }
  window.addEventListener('load', nukeLegacy);

  // no-op API (호환용)
  var api = window.IPORTAL || {};
  api.open = function(){};
  api.close = function(){};
  api.mount = function(){};
  api.unmount = function(){};
  window.IPORTAL = api;

  // ✅ 의도적으로 아무것도 생성하지 않음.
})();
