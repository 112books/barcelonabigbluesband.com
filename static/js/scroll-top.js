(function () {
  var btn = document.getElementById('scroll-to-top');
  if (!btn) return;
  window.addEventListener('scroll', function () {
    if (window.scrollY > 400) btn.classList.add('is-visible');
    else btn.classList.remove('is-visible');
  }, { passive: true });
  btn.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();
