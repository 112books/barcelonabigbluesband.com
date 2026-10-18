/* Ivan Kovačević — 404: idioma segons el navegador */
(function () {
  var lang = (navigator.language || 'ca').substring(0, 2).toLowerCase();
  if (lang !== 'ca' && lang !== 'es' && lang !== 'en') lang = 'ca';
  document.documentElement.lang = lang;
  ['ca', 'es', 'en'].forEach(function (l) {
    var el = document.getElementById('msg-' + l);
    if (el) el.style.display = (l === lang) ? 'block' : 'none';
  });
})();
