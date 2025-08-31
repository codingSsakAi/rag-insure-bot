// 0826-5/insurance_portal/static/insurance_portal/loader_strict.js
// 목적: 자산 탐색/주입 및 3선 햄버거 fallback UI 생성 로직을 전면 차단.
//       어떤 CSS/JS도 로드 시도하지 않고, 버튼 DOM도 절대 만들지 않는다.
(function () {
  "use strict";
  try {
    console.log("[portal-loader] disabled (no asset probing, no fallback)");
  } catch (_) {}
  // 아무 것도 하지 않음.
})();
