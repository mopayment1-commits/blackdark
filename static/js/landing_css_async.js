/** Non-blocking landing stylesheets without inline onload handlers (CSP / Lighthouse). */
(function () {
  var sheets = ["/static/css/trust-os.css", "/static/css/landing.css"];
  for (var i = 0; i < sheets.length; i++) {
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = sheets[i];
    document.head.appendChild(link);
  }
})();
