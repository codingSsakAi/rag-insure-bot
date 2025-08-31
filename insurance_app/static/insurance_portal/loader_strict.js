// insurance_app/static/insurance_portal/loader.js
// 목적: 과거 보조 로더의 fallback UI 생성/자산 탐색을 전면 차단.
(function () {
  "use strict";
  try {
    console.log("[portal-loader] secondary disabled (no asset probing, no fallback)");
  } catch (_) {}
  // 아무 것도 하지 않음.
})();
