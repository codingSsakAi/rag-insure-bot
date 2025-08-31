// insurance_app/static/insurance_portal/loader.js
// 목적: 초기화 실패시 3선 햄버거 버튼을 생성하던 fallback을 **전면 제거**
(function(){
  "use strict";
  try {
    console.log("[portal-loader] secondary loader present (fallback UI removed)");
    // 어떤 경우에도 버튼을 생성하거나 DOM을 주입하지 않는다.
  } catch(e) {}
})();
