// 0826-5/insurance_portal/static/insurance_portal/js/portal.js
// 레거시 사이드 패널/우하단 3선 토글을 완전히 비활성화(No-Op)한다.
// 미들웨어가 이 파일을 주입해도 UI를 만들지 않도록 처리.

(function () {
  try {
    // 과거 요소가 남아 있다면 정리
    ['ip-overlay', 'ip-panel', 'ip-fab', 'portal-panel-overlay'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
    var legacyEl = document.querySelector('.portal-fab, .portal-panel');
    if (legacyEl && legacyEl.parentNode) legacyEl.parentNode.removeChild(legacyEl);
  } catch (e) {}

  // 레거시 코드 호환용 전역 표식
  window.__PORTAL_DISABLED__ = true;
  window.PORTAL_MENU = window.PORTAL_MENU || {};
})();
