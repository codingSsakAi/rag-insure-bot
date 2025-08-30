/* decommissioned loader_strict.js
   - 후보 스캔/자원 프로빙/폴백 FAB(≡) 생성 기능 제거
   - 남아있는 IPORTAL 호출은 전부 no-op으로 흡수
*/
(function () {
  // 더미 IPORTAL – mount/open/close/unmount 호출해도 아무 일도 안 함
  window.IPORTAL = window.IPORTAL || {};
  ['mount','unmount','open','close'].forEach(function (k) {
    if (typeof window.IPORTAL[k] !== 'function') {
      window.IPORTAL[k] = function () { /* no-op */ };
    }
  });

  // 혹시 이전 빌드가 만든 폴백 FAB가 있다면 즉시 제거
  try {
    var kill = function () {
      var b = document.getElementById('ip-fallback');
      if (b && b.parentNode) b.parentNode.removeChild(b);
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', kill, { once:true });
    } else {
      kill();
    }
    new MutationObserver(kill).observe(document.documentElement || document.body, { childList:true, subtree:true });
  } catch (_) {}
})();
