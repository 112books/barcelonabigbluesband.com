/* Ivan Kovačević — Admin analytics (GoatCounter, dades públiques).
   Pestanyes: Resum (per dia/setmana/mes/trimestre/any + idiomes),
   Pàgines i seccions, Navegadors i dispositius. */
(function () {
  'use strict';
  var el = document.getElementById('analytics-data-url');
  if (!el) return;
  var DATA_URL = el.getAttribute('data-url');
  var SINCE = el.getAttribute('data-since') || '';

  var DATA = null, TAB = 'resum', GROUP = 'month';

  var GROUPS = [['day','Dia'],['week','Setmana'],['month','Mes'],['quarter','Trimestre'],['year','Any']];
  var LANG_NAMES = { ca:'Català', es:'Castellà', en:'Anglès', sr:'Serbi', other:'Altres' };
  var SECTION_NAMES = { home:'Inici', gigs:'Concerts', concerts:'Concerts', conciertos:'Concerts',
    projects:'Projectes', projectes:'Projectes', projekti:'Projectes',
    discography:'Discografia', discografia:'Discografia', diskografija:'Discografia',
    videos:'Vídeos', video:'Vídeos', photos:'Fotografies', fotografies:'Fotografies',
    fotografias:'Fotografies', fotografije:'Fotografies',
    press:'Premsa', premsa:'Premsa', stampa:'Premsa',
    contact:'Contacte', contacte:'Contacte', contacto:'Contacte', kontakt:'Contacte',
    biography:'Biografia', biografia:'Biografia', biografija:'Biografia',
    search:'Cerca', cerca:'Cerca', buscar:'Cerca', pretraga:'Cerca',
    legal:'Legal', admin:'Admin', cms:'CMS' };
  var SIZE_LABELS = { phone:'Mòbil', tablet:'Tauleta', desktop:'Escriptori', desktophd:'Escriptori HD', larger:'Pantalla gran' };
  var BROWSER_ICONS = {
    'Safari':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="22"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z"/><line x1="2" y1="12" x2="22" y2="12"/></svg>',
    'Chrome':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="21.17" y1="8" x2="12" y2="8"/><line x1="3.95" y1="6.06" x2="8.54" y2="14"/><line x1="10.88" y1="21.94" x2="15.46" y2="14"/></svg>',
    'Firefox':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0z"/></svg>',
    'Edge':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c1.9 0 3.7-.5 5.2-1.5"/><path d="M22 12c0-2.5-1-4.8-2.7-6.5C17.7 4 15.5 3 13 3"/></svg>'
  };
  var SYSTEM_ICONS = {
    'macOS':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    'iOS':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="7" y="2" width="10" height="20" rx="2"/><circle cx="12" cy="18" r="1"/></svg>',
    'Windows':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 5l8-1v8H3z"/><path d="M13 4l8-1v9h-8z"/><path d="M3 13h8v8l-8-1z"/><path d="M13 13h8v9l-8-1z"/></svg>',
    'Android':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M5 16a7 7 0 0 1 14 0"/><line x1="12" y1="16" x2="12" y2="22"/><line x1="9" y1="22" x2="15" y2="22"/><line x1="4" y1="8" x2="4" y2="14"/><line x1="20" y1="8" x2="20" y2="14"/></svg>'
  };
  var SIZE_ICONS = {
    'phone':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="7" y="2" width="10" height="20" rx="2"/><circle cx="12" cy="18" r="1"/></svg>',
    'tablet':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2"/><circle cx="12" cy="18" r="1"/></svg>',
    'desktop':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    'desktophd':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>',
    'larger':'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="3" width="22" height="14" rx="2"/><line x1="7" y1="21" x2="17" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'
  };

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }
  function parseDay(s) { return new Date(s + 'T00:00:00'); }
  function fmtDate(s) {
    if (!s) return '';
    var d = parseDay(s);
    if (isNaN(d.getTime())) return s;
    return d.toLocaleDateString('ca-ES', { day:'numeric', month:'long', year:'numeric' });
  }
  function isoWeek(d) {
    var t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    var dn = (t.getUTCDay() + 6) % 7;
    t.setUTCDate(t.getUTCDate() - dn + 3);
    var ft = t.getTime();
    t.setUTCMonth(0, 1);
    if (t.getUTCDay() !== 4) t.setUTCMonth(0, 1 + ((4 - t.getUTCDay()) + 7) % 7);
    return t.getUTCFullYear() + '-S' + String(1 + Math.ceil((ft - t.getTime()) / 604800000)).padStart(2,'0');
  }
  function groupKey(day) {
    var d = parseDay(day);
    if (GROUP === 'day') return day;
    if (GROUP === 'week') return isoWeek(d);
    if (GROUP === 'month') return day.slice(0,7);
    if (GROUP === 'quarter') return d.getFullYear() + ' T' + (Math.floor(d.getMonth()/3)+1);
    return day.slice(0,4);
  }
  function buildSeries() {
    var map = {};
    (DATA.hits || []).forEach(function (h) {
      (h.stats || []).forEach(function (s) {
        if (!s.day) return;
        var k = groupKey(s.day);
        map[k] = (map[k] || 0) + (s.daily || 0);
      });
    });
    return Object.keys(map).sort().map(function (k) { return { key:k, count:map[k] }; });
  }
  function bar(value, max, cls, pct) {
    var w = max > 0 ? Math.round((value / max) * 100) : 0;
    var p = pct !== undefined ? pct : w;
    return '<div class="chart-bar-wrap"><div class="chart-bar ' + cls + '" data-width="' + w + '" style="width:0%">' +
      (w > 8 ? '<span class="chart-pct">' + p + '%</span>' : '') + '</div></div>';
  }
  function rows(items, max, total, cls) {
    return items.map(function (item) {
      var pct = total > 0 ? Math.round(item.count / total * 100) : 0;
      return '<div class="chart-row"><div class="chart-label">' + esc(item.name) + '</div>' +
        bar(item.count, max, cls, pct) + '<div class="chart-value">' + item.count + '</div></div>';
    }).join('');
  }
  function iconRowVisual(items, icons, cls) {
    if (!items || !items.length) return '';
    var total = items.reduce(function (s,i) { return s + i.count; }, 0);
    var maxCount = Math.max.apply(null, items.map(function (i) { return i.count; }));
    var MAX = 64, MIN = 18, html = '<div class="icon-row">';
    items.forEach(function (item) {
      var pct = total > 0 ? Math.round(item.count / total * 100) : 0;
      var size = Math.max(MIN, Math.round((item.count / maxCount) * MAX));
      var icon = icons[item.id] || icons[item.name] || '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/></svg>';
      html += '<div class="icon-item"><div style="width:' + MAX + 'px;display:flex;align-items:flex-end;justify-content:center">' +
        '<span style="width:' + size + 'px;height:' + size + 'px;display:block">' + icon + '</span></div>' +
        '<div class="icon-item__pct">' + pct + '%</div>' +
        '<div class="icon-item__name">' + esc(SIZE_LABELS[item.id] || item.name) + '</div>' +
        '<div class="icon-item__count">' + item.count + '</div></div>';
    });
    return html + '</div>';
  }
  function statSection(title, items, cls, icons) {
    if (!items || !items.length) return '';
    var max = Math.max.apply(null, items.map(function (i) { return i.count; }));
    var total = items.reduce(function (s,i) { return s + i.count; }, 0) || 1;
    var vis = icons ? iconRowVisual(items, icons, cls.replace('chart-bar--','')) : '';
    return '<div class="section-title">' + title + '</div>' + vis + '<div class="chart">' + rows(items, max, total, cls) + '</div>';
  }

  function renderResum() {
    var s = buildSeries();
    var max = Math.max.apply(null, s.map(function (x) { return x.count; }).concat([1]));
    var total = s.reduce(function (a,x) { return a + x.count; }, 0);
    var bars = s.map(function (x) {
      var h = max > 0 ? Math.round((x.count / max) * 100) : 0;
      return '<div class="series-col" title="' + esc(x.key) + ': ' + x.count + '">' +
        '<div class="series-bar" style="height:' + Math.max(h, 1) + '%"></div></div>';
    }).join('');
    var first = s.length ? s[0].key : '';
    var last  = s.length ? s[s.length-1].key : '';
    var groupBtns = GROUPS.map(function (g) {
      return '<button type="button" class="period-btn' + (g[0] === GROUP ? ' active' : '') + '" data-group="' + g[0] + '">' + g[1] + '</button>';
    }).join('');
    var lang = DATA.by_lang || {};
    var langItems = Object.keys(lang).sort(function (a,b) { return lang[b]-lang[a]; })
      .map(function (k) { return { id:k, name:LANG_NAMES[k] || k, count:lang[k] }; });
    var langMax = Math.max.apply(null, langItems.map(function (i) { return i.count; }).concat([1]));
    var langTotal = langItems.reduce(function (a,i) { return a + i.count; }, 0) || 1;

    return '<div class="period-wrap"><span class="period-label">Agrupa per</span>' +
      '<div id="group-selector">' + groupBtns + '</div></div>' +
      '<div class="stats-total">visites totals <strong>' + total.toLocaleString('ca-ES') + '</strong></div>' +
      '<div class="series"><div class="series-inner">' + (bars || '<span class="loading">Sense dades</span>') + '</div>' +
      (s.length ? '<div class="series-axis"><span>' + esc(first) + '</span><span>' + esc(last) + '</span></div>' : '') + '</div>' +
      '<div class="section-title">visites per idioma</div>' +
      '<div class="chart">' + rows(langItems, langMax, langTotal, 'chart-bar--section') + '</div>';
  }

  function renderPagines() {
    var hits = (DATA.hits || []).slice().sort(function (a,b) { return b.count - a.count; });
    var max = Math.max.apply(null, hits.map(function (h) { return h.count; }).concat([1]));
    var total = hits.reduce(function (a,h) { return a + h.count; }, 0) || 1;
    var pageRows = hits.map(function (h) {
      var name = h.title || h.path;
      var pct = Math.round(h.count / total * 100);
      return '<div class="chart-row"><div class="chart-label" title="' + esc(h.path) + '">' + esc(name) + '</div>' +
        bar(h.count, max, 'chart-bar--section', pct) + '<div class="chart-value">' + h.count + '</div></div>';
    }).join('');
    var sec = DATA.by_section || {};
    var secItems = Object.keys(sec).sort(function (a,b) { return sec[b]-sec[a]; })
      .map(function (k) { return { id:k, name:SECTION_NAMES[k] || k, count:sec[k] }; });
    var secMax = Math.max.apply(null, secItems.map(function (i) { return i.count; }).concat([1]));
    var secTotal = secItems.reduce(function (a,i) { return a + i.count; }, 0) || 1;
    return '<div class="section-title">pàgines més visitades</div><div class="chart">' + (pageRows || '<span class="loading">Sense dades</span>') + '</div>' +
      '<div class="section-title">seccions</div><div class="chart">' + rows(secItems, secMax, secTotal, 'chart-bar--section') + '</div>';
  }

  function renderTecnologia() {
    return statSection('navegadors', DATA.browsers || [], 'chart-bar--browser', BROWSER_ICONS) +
      statSection('sistemes operatius', DATA.systems || [], 'chart-bar--system', SYSTEM_ICONS) +
      statSection('tipus de dispositiu', DATA.sizes || [], 'chart-bar--size', SIZE_ICONS) +
      statSection('ubicacions', DATA.locations || [], 'chart-bar--location', null);
  }

  function render() {
    var content = document.getElementById('dash-content');
    if (!content) return;
    if (TAB === 'pagines') content.innerHTML = renderPagines();
    else if (TAB === 'tecnologia') content.innerHTML = renderTecnologia();
    else content.innerHTML = renderResum();
    setTimeout(function () {
      document.querySelectorAll('.chart-bar').forEach(function (b) {
        var w = b.getAttribute('data-width');
        b.classList.add('animate');
        setTimeout(function () { b.style.width = w + '%'; }, 40);
      });
    }, 60);
  }

  function load() {
    var content = document.getElementById('dash-content');
    if (content) content.innerHTML = '<div class="loading">Carregant dades...</div>';
    fetch(DATA_URL + '?t=' + Date.now())
      .then(function (r) { if (!r.ok) throw new Error('No es pot carregar analytics.json'); return r.json(); })
      .then(function (data) {
        DATA = data;
        var sinceEl = document.getElementById('admin-since');
        if (sinceEl) sinceEl.textContent = fmtDate(SINCE);
        render();
      })
      .catch(function (err) {
        if (content) content.innerHTML = '<div style="color:var(--c-red)">ERROR: ' + esc(err.message) + '</div>';
      });
  }

  document.addEventListener('click', function (e) {
    var tab = e.target.closest && e.target.closest('.admin-tab');
    if (tab) {
      TAB = tab.getAttribute('data-tab');
      document.querySelectorAll('.admin-tab').forEach(function (t) { t.classList.toggle('is-active', t === tab); });
      render();
      return;
    }
    var g = e.target.closest && e.target.closest('[data-group]');
    if (g) { GROUP = g.getAttribute('data-group'); render(); }
  });

  window.addEventListener('DOMContentLoaded', load);
})();
