(function() {
  'use strict';

  const lang = document.documentElement.lang || 'ca';

  const I18N = {
    ca: {
      searching: 'Cercant...',
      results: (n) => n === 1 ? '1 resultat' : `${n} resultats`,
      noResults: (q) => `Cap resultat per a "${q}"`,
      empty: 'Introdueix un terme per cercar.',
      excerpt: 'Extracte',
    },
    es: {
      searching: 'Buscando...',
      results: (n) => n === 1 ? '1 resultado' : `${n} resultados`,
      noResults: (q) => `Sin resultados para "${q}"`,
      empty: 'Introduce un término para buscar.',
      excerpt: 'Extracto',
    },
    en: {
      searching: 'Searching...',
      results: (n) => n === 1 ? '1 result' : `${n} results`,
      noResults: (q) => `No results for "${q}"`,
      empty: 'Enter a term to search.',
      excerpt: 'Excerpt',
    },
    sr: {
      searching: 'Pretraga...',
      results: (n) => n === 1 ? '1 rezultat' : `${n} rezultata`,
      noResults: (q) => `Nema rezultata za "${q}"`,
      empty: 'Unesi pojam za pretragu.',
      excerpt: 'Izvod',
    },
  };

  const t = I18N[lang] || I18N.ca;

  // Escapat per a sortides via innerHTML (dades de Pagefind)
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }
  // Pagefind marca les coincidencies amb <mark>; permetem nomes aquesta etiqueta
  function safeExcerpt(html) {
    return String(html == null ? '' : html)
      .replace(/<mark>/g, '\u0000MO\u0000').replace(/<\/mark>/g, '\u0000MC\u0000')
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
      .replace(/\u0000MO\u0000/g, '<mark>').replace(/\u0000MC\u0000/g, '</mark>');
  }
  const input   = document.getElementById('search-input');
  const status  = document.getElementById('search-status');
  const results = document.getElementById('search-results');
  const clearBtn = document.getElementById('search-clear');

  let pagefind = null;
  let debounceTimer = null;

  // Ruta del bundle de Pagefind, relativa al baseURL (funciona sota subpath).
  const pagefindUrl =
    document.querySelector('.search-container')?.dataset.pagefindScript ||
    '/pagefind/pagefind.js';

  // Carrega Pagefind de forma lazy
  async function loadPagefind() {
    if (pagefind) return pagefind;
    try {
      pagefind = await import(pagefindUrl);
      await pagefind.options({ excerptLength: 20 });
      return pagefind;
    } catch(e) {
      console.error('Pagefind no disponible:', e);
      return null;
    }
  }

  // Cerca amb debounce
  function debounce(fn, ms) {
    return function(...args) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => fn.apply(this, args), ms);
    };
  }

  async function doSearch(query) {
    query = query.trim();

    clearBtn.hidden = !query;

    if (!query) {
      status.textContent = t.empty;
      results.innerHTML = '';
      return;
    }

    status.textContent = t.searching;
    results.innerHTML = '';

    const pf = await loadPagefind();
    if (!pf) {
      status.textContent = 'Error carregant el cercador.';
      return;
    }

    let search, data;
    try {
      search = await pf.search(query);
      data   = await Promise.all(search.results.slice(0, 10).map(r => r.data()));
    } catch(e) {
      console.error('Error en la cerca:', e);
      status.textContent = 'Error en la cerca. Torna-ho a intentar.';
      return;
    }

    if (data.length === 0) {
      status.textContent = t.noResults(query);
      return;
    }

    status.textContent = t.results(data.length);

    results.innerHTML = data.map(r => {
      const image = r.meta?.image
        ? `<img class="search-result__img" src="${esc(r.meta.image)}" alt="" loading="lazy">`
        : `<div class="search-result__img search-result__img--placeholder">
             <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
               <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
             </svg>
           </div>`;

      const section = r.meta?.section || '';
      const excerpt = r.excerpt || '';

      return `
        <article class="search-result" role="listitem">
          <a href="${esc(r.url)}" class="search-result__link">
            ${image}
            <div class="search-result__body">
              ${section ? `<span class="search-result__section">${esc(section)}</span>` : ''}
              <h2 class="search-result__title">${esc(r.meta?.title) || esc(r.url)}</h2>
              ${excerpt ? `<p class="search-result__excerpt">${safeExcerpt(excerpt)}</p>` : ''}
            </div>
          </a>
        </article>`;
    }).join('');
  }

  const debouncedSearch = debounce(doSearch, 250);

  input.addEventListener('input', () => debouncedSearch(input.value));

  clearBtn.addEventListener('click', () => {
    input.value = '';
    clearBtn.hidden = true;
    status.textContent = t.empty;
    results.innerHTML = '';
    input.focus();
  });

  // Cerca per paràmetre URL (?q=...)
  const params = new URLSearchParams(window.location.search);
  const q = params.get('q');
  if (q) {
    input.value = q;
    doSearch(q);
  } else {
    status.textContent = t.empty;
  }

})();
