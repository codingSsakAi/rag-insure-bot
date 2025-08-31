// insurance_portal/loader_strict.js
(function () {
  if (window.__PORTAL_LOADER__) return;
  window.__PORTAL_LOADER__ = true;

  const log = (...a) => console.log("[portal-loader]", ...a);

  const q = (sel) => document.querySelector(sel);

  const addLink = (href, attrs = {}) => {
    if (q(`link[rel="stylesheet"][href="${href}"]`)) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    Object.entries(attrs).forEach(([k, v]) => link.setAttribute(k, v));
    document.head.appendChild(link);
  };

  const addScript = (src, attrs = {}) => {
    if (q(`script[src="${src}"]`)) return;
    const s = document.createElement("script");
    s.src = src;
    s.defer = true;
    Object.entries(attrs).forEach(([k, v]) => s.setAttribute(k, v));
    document.head.appendChild(s);
  };

  const headOK = (url) =>
    fetch(url, { method: "HEAD" })
      .then((r) => r.ok)
      .catch(() => false);

  const ensureLocal = async (candidates, adder) => {
    for (const url of candidates) {
      if (!url.startsWith("/static/")) continue; // 외부는 HEAD 금지 (CORS)
      if (await headOK(url)) {
        adder(url);
        return url;
      }
    }
    return null;
  };

  (async () => {
    // 1) Font Awesome — cdnjs 금지, jsDelivr만
    addLink(
      "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css",
      { crossorigin: "anonymous", referrerpolicy: "no-referrer" }
    );

    // 2) Portal CSS (있는 것만 조용히 로드)
    await ensureLocal(
      [
        "/static/insurance_portal/css/portal.bundle.css",
        "/static/insurance_portal/css/portal.css",
      ],
      (href) => addLink(href)
    );

    // 보조 CSS (있으면 붙임)
    await ensureLocal(
      ["/static/insurance_portal/css/chatbot.css"],
      (href) => addLink(href)
    );
    await ensureLocal(
      ["/static/insurance_portal/css/fab.css"],
      (href) => addLink(href)
    );

    // 3) JS 번들 (bundle 우선, 없으면 portal.js)
    const picked = await ensureLocal(
      [
        "/static/insurance_portal/js/portal.bundle.js",
        "/static/insurance_portal/js/portal.js",
      ],
      (src) => addScript(src)
    );

    log("ready", { js: picked || "none" });
  })();
})();
