/* Ivan Kovačević — navegació: header compacte i menú mòbil */

/* Botó "tornar" genèric (substitueix javascript:history.back()) */
document.addEventListener('click', function(e) {
  var el = e.target && e.target.closest ? e.target.closest('[data-back]') : null;
  if (el) { e.preventDefault(); history.back(); }
});

(function() {
  var header        = document.getElementById('site-header');
  var compact       = document.getElementById('nav-compact');
  var toggle        = document.getElementById('nav-toggle');
  var compactToggle = document.getElementById('nav-compact-toggle');
  var overlay       = document.getElementById('nav-overlay');
  var mainNav       = document.querySelector('.main-nav');
  if (!header || !compact || !mainNav) return;

  var menuOpen = false;
  var lastFocused = null;

  function updateNav() {
    var scrolled = window.scrollY > 80 && !menuOpen;
    compact.classList.toggle('is-visible', scrolled);
    compact.setAttribute('aria-hidden', scrolled ? 'false' : 'true');
    header.classList.toggle('is-hidden', scrolled);
  }

  window.addEventListener('scroll', updateNav, { passive: true });
  window.addEventListener('load', updateNav);

  function setExpanded(open) {
    if (toggle) toggle.setAttribute('aria-expanded', String(open));
    if (compactToggle) compactToggle.setAttribute('aria-expanded', String(open));
  }

  function closeMenu() {
    menuOpen = false;
    mainNav.classList.remove('is-open');
    if (overlay) { overlay.classList.remove('is-active'); overlay.setAttribute('aria-hidden', 'true'); }
    setExpanded(false);
    updateNav();
    if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
  }

  function openMenu(btn) {
    menuOpen = true;
    lastFocused = btn || document.activeElement;
    mainNav.classList.add('is-open');
    if (overlay) { overlay.classList.add('is-active'); overlay.setAttribute('aria-hidden', 'false'); }
    setExpanded(true);
    header.classList.remove('is-hidden');
    compact.classList.remove('is-visible');
    compact.setAttribute('aria-hidden', 'true');
    var first = mainNav.querySelector('a[href], button:not([disabled])');
    if (first) first.focus();
  }

  function toggleMenu(btn) {
    if (menuOpen) { closeMenu(); } else { openMenu(btn); }
  }

  if (toggle) toggle.addEventListener('click', function() { toggleMenu(toggle); });
  if (compactToggle) compactToggle.addEventListener('click', function() { toggleMenu(compactToggle); });
  if (overlay) overlay.addEventListener('click', closeMenu);

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && menuOpen) { closeMenu(); return; }
    if (e.key === 'Tab' && menuOpen) {
      var focusables = mainNav.querySelectorAll('a[href], button:not([disabled])');
      if (!focusables.length) return;
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
})();
