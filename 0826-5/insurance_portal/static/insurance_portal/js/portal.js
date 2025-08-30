// insurance_portal/portal.js
// (전체 교체본) — 우하단 3선 토글(≡)과 사이드 패널 DOM 생성 로직을 완전히 제거.
// 다른 코드가 IPORTAL API를 호출하더라도 에러가 나지 않도록 no-op 스텁만 노출합니다.

(function () {
  // 과거 버전에서 만들어졌을 수도 있는 요소는 안전하게 제거
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

  // 호환성 유지를 위한 no-op API
  var api = window.IPORTAL || {};
  api.open = function(){ /* no-op */ };
  api.close = function(){ /* no-op */ };
  api.mount = function(){ /* no-op */ };
  api.unmount = function(){ /* no-op */ };
  window.IPORTAL = api;

  // ✅ 의도적으로 아무것도 생성하지 않습니다.
  //    (오른쪽 ‘+’ 사이드 토글은 다른 코드라서 그대로 유지됩니다)
})();
