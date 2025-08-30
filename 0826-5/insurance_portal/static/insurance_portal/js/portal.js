// 0826-5/insurance_portal/static/insurance_portal/loader_strict.js
(function () {
  function removeLegacyNodes() {
    ['ip-fab', 'ip-overlay', 'ip-panel', 'ip-fallback'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', removeLegacyNodes);
  } else {
    removeLegacyNodes();
  }
  window.addEventListener('load', removeLegacyNodes);

  window.IPORTAL = window.IPORTAL || {};
  ['mount', 'unmount', 'open', 'close'].forEach(function (k) {
    window.IPORTAL[k] = function () {};
  });
  window.__PORTAL_ENTRY__ = function () {};
})();
