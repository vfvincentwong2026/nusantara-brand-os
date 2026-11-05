/* Resolve a path stored in web/*.json against this site's root.

   Asset values are site-root-relative and have no leading slash
   ("assets/radar/ID-01.jpg"). On GitHub project pages the root is
   /nusantara-brand-os/; a local server and an apex custom domain serve web/
   at the host root. Absolute URLs (the container site) pass through.
*/
(function (global) {
  var MARKER = "/nusantara-brand-os/";

  function siteRoot() {
    var url = new URL(document.baseURI);
    var i = url.pathname.indexOf(MARKER);
    if (i >= 0) return url.origin + url.pathname.slice(0, i + MARKER.length);
    return url.origin + "/";
  }

  function nboSiteUrl(path) {
    if (path == null || path === "") return path;
    var s = String(path);
    if (/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(s)) return s;
    return new URL(s.replace(/^\/+/, ""), siteRoot()).href;
  }

  global.nboSiteUrl = nboSiteUrl;
})(window);
