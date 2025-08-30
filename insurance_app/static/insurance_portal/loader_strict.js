/* loader_strict.js — HARD KILL: do not load or mount anything, and remove legacy FABs. */
(function () {
  // 1) 혹시 남아있는 과거 ip-* 요소들 제거
  function nuke() {
    const ids = ["ip-fab", "ip-fallback", "ip-overlay", "ip-panel"];
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.parentNode) el.parentNode.removeChild(el);
    });
    // ip-* 계열 잔재가 DOM 어딘가에 들어간 경우까지 제거
    try {
      document.querySelectorAll('[id^="ip-"], .ip-item, .ip-sub').forEach(el => {
        if (el && el.parentNode) el.parentNode.removeChild(el);
      });
    } catch (_) {}
  }
  nuke();
  document.addEventListener("DOMContentLoaded", nuke);

  // 2) 옛 코드가 전역 IPORTAL.*을 호출하더라도 아무 것도 하지 않도록 스텁 정의
  //    (호출 자체는 성공처럼 끝나지만 화면 변화 없음)
  const stub = function () { return false; };
  window.IPORTAL = window.IPORTAL || {};
  window.IPORTAL.mount = stub;
  window.IPORTAL.unmount = stub;
  window.IPORTAL.open = stub;
  window.IPORTAL.close = stub;

  // 3) 진단용 플래그(선택): 이 파일이 로드됐다면 true
  window.__PORTAL_LOADER_STRICT__ = true;

  // 4) 절대로 다른 CSS/JS를 "탐색/로드/시도" 하지 않습니다.
  //    fallback 버튼도 생성하지 않습니다.
})();
