(function () {
  var intro = document.getElementById('hero-logo-intro');
  if (!intro) return;

  // Respecta prefers-reduced-motion
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    intro.style.display = 'none';
    return;
  }

  if (sessionStorage.getItem('ivk-intro-done')) {
    intro.style.display = 'none';
    return;
  }

  var fired = false;
  function runIntro() {
    if (fired) return;
    fired = true;
    sessionStorage.setItem('ivk-intro-done', '1');
    intro.classList.add('hero-logo-intro--done');
    setTimeout(function () { intro.style.display = 'none'; }, 2000); // era 700
  }

  document.addEventListener('mousemove', runIntro, { once: true });
  document.addEventListener('touchstart', runIntro, { once: true, passive: true });
  document.addEventListener('scroll', runIntro, { once: true, passive: true });

  setTimeout(runIntro, 4000); // era 2500 — fallback més tard
})();