/* Ivan Kovačević — llistat i reproductor de vídeos (dades de data/videos.json) */
(function() {
  'use strict';

  var layout = document.getElementById('videos-layout');
  if (!layout) return;

  var dataUrl   = layout.getAttribute('data-videos-url');
  var ytChannel = 'https://www.youtube.com/channel/UCG-CSJzP_90xHVhaDQj6PvA';
  var lang      = document.documentElement.lang || 'ca';

  var I18N = {
    ca: { play: 'Reproduir vídeo', watch: 'Veure a YouTube', error: "No s'han pogut carregar els vídeos.", channel: 'Veure al canal de YouTube' },
    es: { play: 'Reproducir vídeo', watch: 'Ver en YouTube', error: 'No se han podido cargar los vídeos.', channel: 'Ver en el canal de YouTube' },
    en: { play: 'Play video', watch: 'Watch on YouTube', error: 'Videos could not be loaded.', channel: 'Watch on YouTube channel' },
    sr: { play: 'Pusti video', watch: 'Pogledaj na YouTube-u', error: 'Nije moguće učitati videozapise.', channel: 'Pogledaj kanal na YouTube-u' }
  };
  var t = I18N[lang] || I18N.ca;

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  var activeIdx = 0;
  var allVideos = [];

  fetch(dataUrl)
    .then(function(r) { return r.json(); })
    .then(function(videos) {
      if (!videos.length) return showError();
      allVideos = videos.slice().sort(function(a, b) {
        var da = a.published || '', db = b.published || '';
        if (da === db) return 0;
        if (!da) return 1;
        if (!db) return -1;
        return da < db ? 1 : -1;
      });
      renderFacade(allVideos[0]);
      renderList(allVideos);
    })
    .catch(showError);

  function renderFacade(v) {
    var facade = document.getElementById('videos-facade');
    var info   = document.getElementById('videos-player-info');
    if (!facade) return;

    var thumb = v.thumb.replace('hqdefault', 'maxresdefault');

    facade.innerHTML =
      '<div class="videos-facade__wrap" data-id="' + esc(v.id) + '" data-url="' + esc(v.url) + '">' +
        '<img class="videos-facade__thumb" src="' + esc(thumb) + '" alt="' + esc(v.title) + '" loading="lazy">' +
        '<button type="button" class="videos-facade__btn" aria-label="' + t.play + '">' +
          '<svg viewBox="0 0 68 48" width="68" height="48" aria-hidden="true">' +
            '<path class="ytp-large-play-button-bg" d="M66.52,7.74c-0.78-2.93-2.49-5.41-5.42-6.19C55.79,.13,34,0,34,0S12.21,.13,6.9,1.55 C3.97,2.33,2.27,4.81,1.48,7.74C0.06,13.05,0,24,0,24s0.06,10.95,1.48,16.26c0.78,2.93,2.49,5.41,5.42,6.19 C12.21,47.87,34,48,34,48s21.79-0.13,27.1-1.55c2.93-0.78,4.64-3.26,5.42-6.19C67.94,34.95,68,24,68,24S67.94,13.05,66.52,7.74z" fill="#f00"/>' +
            '<path d="M 45,24 27,14 27,34" fill="#fff"/>' +
          '</svg>' +
        '</button>' +
        '<a class="videos-facade__yt" href="' + esc(v.url) + '" target="_blank" rel="noopener" aria-label="' + t.watch + '">' + t.watch + '</a>' +
      '</div>';

    var img = facade.querySelector('.videos-facade__thumb');
    if (img) img.addEventListener('error', function() { this.src = v.thumb; }, { once: true });

    var btn = facade.querySelector('.videos-facade__btn');
    if (btn) btn.addEventListener('click', function() { loadIframe(v); });

    if (info) {
      info.innerHTML =
        '<h2 class="videos-player__title">' + esc(v.title) + '</h2>' +
        '<p class="videos-player__date">' + esc(v.published) + '</p>';
    }
  }

  function loadIframe(v) {
    var facade = document.getElementById('videos-facade');
    if (!facade) return;
    facade.innerHTML =
      '<div class="videos-player__embed">' +
        '<iframe src="' + esc(v.embed) + '&autoplay=1" title="' + esc(v.title) + '" frameborder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" allowfullscreen></iframe>' +
      '</div>';
  }

  function renderList(videos) {
    var ul = document.getElementById('videos-list');
    if (!ul) return;

    ul.innerHTML = videos.map(function(v, i) {
      return '<li class="videos-item' + (i === 0 ? ' is-active' : '') + '" data-idx="' + i + '" tabindex="0" role="button" aria-label="' + esc(v.title) + '">' +
        '<div class="videos-item__thumb">' +
          '<img src="' + esc(v.thumb) + '" alt="' + esc(v.title) + '" loading="lazy">' +
          '<span class="videos-item__play" aria-hidden="true">▶</span>' +
        '</div>' +
        '<div class="videos-item__info">' +
          '<p class="videos-item__title">' + esc(v.title) + '</p>' +
          '<p class="videos-item__date">' + esc(v.published) + '</p>' +
        '</div>' +
      '</li>';
    }).join('');

    ul.querySelectorAll('.videos-item').forEach(function(li) {
      var activate = function() {
        var idx = +li.dataset.idx;
        activeIdx = idx;
        ul.querySelectorAll('.videos-item').forEach(function(el) { el.classList.remove('is-active'); });
        li.classList.add('is-active');
        renderFacade(videos[idx]);
        if (window.innerWidth < 900) {
          document.getElementById('videos-layout').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      };
      li.addEventListener('click', activate);
      li.addEventListener('keydown', function(ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); activate(); }
      });
    });
  }

  function showError() {
    var facade = document.getElementById('videos-facade');
    if (facade) facade.innerHTML =
      '<div class="videos-facade__error">' +
        '<p>' + t.error + '</p>' +
        '<a href="' + ytChannel + '" target="_blank" rel="noopener" class="videos-cta__link" style="margin-top:1rem">' + t.channel + '</a>' +
      '</div>';
  }
})();
