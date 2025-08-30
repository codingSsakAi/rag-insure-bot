// 0826-5/insurance_portal/static/insurance_portal/js/portal.js
// 레거시 사이드 패널/3선 토글 비활성화(No-Op). (static 경로 버전)

(function () {
  try {
    var ids = ['ip-overlay', 'ip-panel', 'ip-fab', 'portal-panel-overlay'];
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
    var legacyFab = document.querySelector('.portal-fab, .portal-panel');
    if (legacyFab && legacyFab.parentNode) legacyFab.parentNode.removeChild(legacyFab);
  } catch (e) {}

  window.__PORTAL_DISABLED__ = true;
  window.PORTAL_MENU = window.PORTAL_MENU || {};
})();
