/* Línia temporal de discografia: revelat d'entrades + traçat de la línia amb l'scroll */
(function () {
  'use strict';

  var tl = document.querySelector('[data-timeline]');
  if (!tl) return;

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fill = tl.querySelector('.timeline__rail-fill');
  var items = tl.querySelectorAll('.timeline__item');

  if (reduce) {
    if (fill) fill.style.height = '100%';
    return;
  }

  tl.classList.add('is-ready');

  var ticking = false;

  function update() {
    ticking = false;
    var vh = window.innerHeight || document.documentElement.clientHeight;

    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      if (el.classList.contains('is-in')) continue;
      if (el.getBoundingClientRect().top < vh * 0.88) el.classList.add('is-in');
    }

    if (fill) {
      var rect = tl.getBoundingClientRect();
      var progress = ((vh * 0.5) - rect.top) / rect.height;
      if (progress < 0) progress = 0;
      else if (progress > 1) progress = 1;
      fill.style.height = (progress * 100).toFixed(2) + '%';
    }
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  window.addEventListener('load', update);
  update();
})();
