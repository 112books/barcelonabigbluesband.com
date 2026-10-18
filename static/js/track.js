function track(event) {
  if (window.goatcounter) {
    window.goatcounter.count({
      path: event
    });
  }
}
document.addEventListener('click', function (e) {
  var el = e.target && e.target.closest ? e.target.closest('[data-track]') : null;
  if (el) track(el.getAttribute('data-track'));
});
