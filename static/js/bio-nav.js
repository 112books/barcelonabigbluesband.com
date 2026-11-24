/* Índex de seccions per a les pàgines de biografia i contractació.
   Genera ids als <h2> i fa scroll suau als enllaços interns (CSP-safe: sense inline). */
(function () {
  var hs = document.querySelectorAll('.prose h2');
  hs.forEach(function (h, i) {
    if (!h.id) {
      var t = h.textContent || '';
      var id = t.toLowerCase().replace(/[^a-z0-9àèéíòóúüñ]+/gi, '-').replace(/^-+|-+$/g, '') || ('section-' + i);
      h.id = id;
    }
  });
  document.querySelectorAll('.bio-sections-nav a, .booking-nav a').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var href = a.getAttribute('href') || '';
      if (href.indexOf('#') !== 0) return;
      var el = document.querySelector(href);
      if (!el) return;
      e.preventDefault();
      var top = el.getBoundingClientRect().top + window.pageYOffset - 110;
      window.scrollTo({ top: top, behavior: 'smooth' });
      history.pushState(null, '', href);
    });
  });
})();
