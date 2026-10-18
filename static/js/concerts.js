/**
 * concerts.js — Ivan Kovačević v4
 * Llegeix /data/concerts.txt (fitxer local, sense CORS)
 * generat cada nit per GitHub Actions.
 * v4: afegit Schema.org MusicEvent dinàmic
 */

(function () {
  "use strict";

  const I18N = {
    ca: {
      months: ["Gener","Febrer","Març","Abril","Maig","Juny","Juliol","Agost","Setembre","Octubre","Novembre","Desembre"],
      shortMonths: ["gen","feb","mar","abr","mai","jun","jul","ago","set","oct","nov","des"],
      weekdays: ["Dl","Dt","Dc","Dj","Dv","Ds","Dg"],
      noUpcoming: "No hi ha propers concerts programats.",
      noUpcomingNewsletter: "Subscriu-te al newsletter per rebre novetats.",
      noPast: "Sense concerts recents.",
      tickets: "Entrades",
      addToCalendar: "Afegir al calendari",
      pastConcerts: "Concerts passats",
    },
    es: {
      months: ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"],
      shortMonths: ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"],
      weekdays: ["Lu","Ma","Mi","Ju","Vi","Sa","Do"],
      noUpcoming: "No hay próximos conciertos programados.",
      noUpcomingNewsletter: "Suscríbete al newsletter para recibir novedades.",
      noPast: "Sin conciertos recientes.",
      tickets: "Entradas",
      addToCalendar: "Añadir al calendario",
      pastConcerts: "Conciertos pasados",
    },
    sr: {
      months: ["Januar","Februar","Mart","April","Maj","Jun","Jul","Avgust","Septembar","Oktobar","Novembar","Decembar"],
      shortMonths: ["jan","feb","mar","apr","maj","jun","jul","avg","sep","okt","nov","dec"],
      weekdays: ["Po","Ut","Sr","Če","Pe","Su","Ne"],
      noUpcoming: "Trenutno nema zakazanih koncerata.",
      noUpcomingNewsletter: "Pretplati se na newsletter za novosti.",
      noPast: "Nema skorašnjih koncerata.",
      tickets: "Ulaznice",
      addToCalendar: "Dodaj u kalendar",
      pastConcerts: "Prošli koncerti",
    },
    en: {
      months: ["January","February","March","April","May","June","July","August","September","October","November","December"],
      shortMonths: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
      weekdays: ["Mo","Tu","We","Th","Fr","Sa","Su"],
      noUpcoming: "No upcoming concerts scheduled.",
      noUpcomingNewsletter: "Subscribe to our newsletter to stay updated.",
      noPast: "No recent concerts.",
      tickets: "Tickets",
      addToCalendar: "Add to calendar",
      pastConcerts: "Past concerts",
    },
  };

  const section = document.querySelector(".concerts-section");
  if (!section) return;

  const lang          = section.dataset.lang || "ca";
  const newsletterUrl = section.dataset.newsletter || "#newsletter";
  const t             = I18N[lang] || I18N.ca;

  // Injecta les etiquetes dels dies de la setmana des del JS (elimina hardcode del template)
  const gridHeader = document.querySelector(".cal-grid-header");
  if (gridHeader) {
    gridHeader.innerHTML = t.weekdays.map(d => `<span>${d}</span>`).join("");
  }

  // Injecta el títol "Concerts passats" des del JS
  const pastTitle = document.querySelector(".concerts-past-title");
  if (pastTitle) {
    pastTitle.textContent = t.pastConcerts;
  }

  let calDate   = new Date();
  let allEvents = [];

  fetch(section.dataset.ical)
    .then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.text();
    })
    .then((ical) => {
      allEvents = parseICal(ical);
      renderCalendar(calDate);
      renderUpcoming();
      renderPast();
    })
    .catch((err) => renderError(err.message));

  // ─── Parser iCal ─────────────────────────────────────────────────────────
  function unfoldICal(raw) {
    const lines = raw.split(/\r?\n/);
    const result = [];
    for (const line of lines) {
      if (/^[ \t]/.test(line) && result.length > 0) {
        result[result.length - 1] += line.slice(1);
      } else {
        result.push(line);
      }
    }
    return result.join("\n");
  }

  function parseICal(raw) {
    raw = unfoldICal(raw);
    const events = [];
    const blocks = raw.split("BEGIN:VEVENT");
    blocks.shift();
    blocks.forEach((block) => {
      const get = (key) => {
        const re = new RegExp(key + "(?:;[^:]*)?:([\\s\\S]*?)(?=\\r?\\n[A-Z])", "m");
        const m = block.match(re);
        return m ? m[1].trim() : "";
      };
      const dtRaw = get("DTSTART");
      if (!dtRaw) return;
      events.push({
        title:    unfold(get("SUMMARY")),
        start:    parseDate(dtRaw),
        end:      parseDate(get("DTEND")),
        location: unfold(get("LOCATION")),
        desc:     unfold(get("DESCRIPTION")),
        url:      get("URL"),
        performer: unfold(get("X-PERFORMER")),
      });
    });
    events.sort((a, b) => a.start - b.start);
    return events;
  }

  function parseDate(str) {
    if (!str) return null;
    const s = str.replace(/Z$/, "");
    if (s.length === 8)
      return new Date(+s.slice(0,4), +s.slice(4,6)-1, +s.slice(6,8));
    return new Date(+s.slice(0,4), +s.slice(4,6)-1, +s.slice(6,8), +s.slice(9,11)||0, +s.slice(11,13)||0);
  }

  function unfold(str) {
    return str.replace(/\\n/g,"\n").replace(/\\,/g,",").replace(/\\;/g,";").replace(/<[^>]+>/g,"").trim();
  }

  // Escapat HTML per a sortides via innerHTML (dades de l'iCal)
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
      .replace(/"/g,"&quot;").replace(/'/g,"&#39;");
  }
  function safeUrl(u) {
    return /^https?:\/\//i.test(u || "") ? esc(u) : "";
  }

  // ─── Calendari ───────────────────────────────────────────────────────────
  function renderCalendar(d) {
    const grid  = document.getElementById("cal-grid");
    const label = document.querySelector(".cal-month-label");
    if (!grid || !label) return;

    const year  = d.getFullYear();
    const month = d.getMonth();
    label.textContent = t.months[month] + " " + year;

    const startOffset = (new Date(year, month, 1).getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    const eventDays = new Set(
      allEvents
        .filter(e => e.start && e.start.getFullYear()===year && e.start.getMonth()===month)
        .map(e => e.start.getDate())
    );

    grid.innerHTML = "";
    for (let i = 0; i < startOffset; i++) {
      const c = document.createElement("div");
      c.className = "cal-cell cal-cell--empty";
      grid.appendChild(c);
    }
    for (let day = 1; day <= daysInMonth; day++) {
      const isEvent = eventDays.has(day);
      const c = document.createElement(isEvent ? "button" : "div");
      c.className = "cal-cell";
      c.textContent = day;
      if (isEvent) c.type = "button";
      if (today.getDate()===day && today.getMonth()===month && today.getFullYear()===year)
        c.classList.add("cal-cell--today");
      if (isEvent) {
        const dayEvents = eventsOnDay(year, month, day);
        c.classList.add("cal-cell--event");
        c.title = dayEvents.map(e => e.title).join(" · ");
        c.setAttribute("aria-label",
          shortDate(new Date(year, month, day)) + ": " + dayEvents.map(e => e.title).join(", "));
        c.addEventListener("click", () => {
          const idx = allEvents.findIndex(e =>
            e.start && e.start.getFullYear()===year && e.start.getMonth()===month && e.start.getDate()===day
          );
          if (idx >= 0) selectEvent(idx);
        });
      }
      grid.appendChild(c);
    }

    document.querySelector(".cal-prev").onclick = () => {
      calDate = new Date(calDate.getFullYear(), calDate.getMonth()-1, 1);
      renderCalendar(calDate);
    };
    document.querySelector(".cal-next").onclick = () => {
      calDate = new Date(calDate.getFullYear(), calDate.getMonth()+1, 1);
      renderCalendar(calDate);
    };
  }

  function eventsOnDay(year, month, day) {
    return allEvents.filter(e =>
      e.start && e.start.getFullYear()===year && e.start.getMonth()===month && e.start.getDate()===day
    );
  }

  // Fa operables amb teclat els elements de la llista de concerts
  function wireConcertList(ul) {
    ul.querySelectorAll(".concert-li").forEach(li => {
      li.addEventListener("click", () => selectEvent(+li.dataset.idx));
      li.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          selectEvent(+li.dataset.idx);
        }
      });
    });
  }

  // ─── Llista propers concerts ──────────────────────────────────────────────
  function renderUpcoming() {
    const now      = new Date();
    const upcoming = allEvents.map((e,i) => ({e,i})).filter(({e}) => e.start && e.start >= now);
    const ul = document.getElementById("concerts-upcoming");
    if (!ul) return;

    if (upcoming.length === 0) {
      ul.innerHTML = `
        <li class="concerts-empty-msg">
          ${t.noUpcoming}<br>
          <a href="${newsletterUrl}" class="concerts-newsletter-link">${t.noUpcomingNewsletter}</a>
        </li>`;
      return;
    }

    ul.innerHTML = upcoming.map(({e, i}) => `
      <li class="concert-li" data-idx="${i}" tabindex="0" role="button" aria-label="${e.performer ? esc(e.performer) + " — " : ""}${esc(e.title)} — ${shortDate(e.start)}">
        <div class="concert-li-date">${shortDate(e.start)}</div>
        <div>
          ${e.performer ? `<div class="concert-li-performer">${esc(e.performer)}</div>` : ""}
          <div class="concert-li-title">${esc(e.title)}</div>
          ${e.location ? `<div class="concert-li-location">${esc(e.location)}</div>` : ""}
        </div>
      </li>`).join("");

    wireConcertList(ul);

    selectEvent(upcoming[0].i);
  }

  // ─── Concerts passats ─────────────────────────────────────────────────────
  function renderPast() {
    const now  = new Date();
    const past = allEvents.map((e,i) => ({e,i})).filter(({e}) => e.start && e.start < now).slice(-5).reverse();
    const ul = document.getElementById("concerts-past");
    if (!ul) return;

    if (past.length === 0) {
      ul.innerHTML = `<li class="concerts-empty-msg">${t.noPast}</li>`;
      return;
    }

    ul.innerHTML = past.map(({e, i}) => `
      <li class="concert-li concert-li--past" data-idx="${i}" tabindex="0" role="button" aria-label="${e.performer ? esc(e.performer) + " — " : ""}${esc(e.title)} — ${shortDate(e.start)}">
        <div class="concert-li-date">${shortDate(e.start)}</div>
        <div>
          ${e.performer ? `<div class="concert-li-performer">${esc(e.performer)}</div>` : ""}
          <div class="concert-li-title">${esc(e.title)}</div>
          ${e.location ? `<div class="concert-li-location">${esc(e.location)}</div>` : ""}
        </div>
      </li>`).join("");

    wireConcertList(ul);
  }

  // ─── Detall ───────────────────────────────────────────────────────────────
  function selectEvent(idx) {
    const event = allEvents[idx];
    if (!event) return;

    document.querySelectorAll(".concert-li").forEach(li => {
      li.classList.toggle("is-active", +li.dataset.idx === idx);
    });

    document.querySelectorAll(".cal-cell--selected").forEach(c => c.classList.remove("cal-cell--selected"));
    if (event.start) {
      if (event.start.getMonth() !== calDate.getMonth() || event.start.getFullYear() !== calDate.getFullYear()) {
        calDate = new Date(event.start.getFullYear(), event.start.getMonth(), 1);
        renderCalendar(calDate);
      }
      const cells = document.querySelectorAll(".cal-cell");
      const startOffset = (new Date(calDate.getFullYear(), calDate.getMonth(), 1).getDay() + 6) % 7;
      const targetCell  = cells[startOffset + event.start.getDate() - 1];
      if (targetCell) targetCell.classList.add("cal-cell--selected");
    }

    const detail = document.getElementById("concert-detail");
    if (!detail) return;

    const dateStr = event.start
      ? event.start.toLocaleDateString(langLocale(), {weekday:"long", day:"numeric", month:"long", year:"numeric"}).toUpperCase()
      : "";
    const timeStr = event.start && event.start.getHours() > 0
      ? " · " + event.start.toLocaleTimeString(langLocale(), {hour:"2-digit", minute:"2-digit"})
      : "";

    const icalUrl = section.dataset.ical || "";

    detail.removeAttribute("hidden");
    detail.innerHTML = `
      <div class="concert-detail-date">${dateStr}${timeStr}</div>
      ${event.performer ? `<div class="concert-detail-performer">${esc(event.performer)}</div>` : ""}
      <h2 class="concert-detail-title">${esc(event.title)}</h2>
      ${event.location ? `<p class="concert-detail-location">📍 ${esc(event.location)}</p>` : ""}
      ${event.desc     ? `<p class="concert-detail-desc">${esc(event.desc)}</p>` : ""}
      ${safeUrl(event.url) ? `<a href="${safeUrl(event.url)}" class="concert-detail-link" target="_blank" rel="noopener">${t.tickets}</a>` : ""}
      ${icalUrl ? `
      <div class="concert-detail-cal">
        <a href="${icalUrl}" download="ivan-kovacevic-gigs.ics" class="cal-subscribe__btn">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          ${t.addToCalendar}
        </a>
      </div>` : ""}
    `;

    if (window.innerWidth < 769) {
      detail.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  // ─── Helpers ─────────────────────────────────────────────────────────────
  function shortDate(d) {
    if (!d) return "";
    return d.getDate() + " " + t.shortMonths[d.getMonth()];
  }

  function langLocale() {
    return {ca:"ca-ES", es:"es-ES", en:"en-GB"}[lang] || "ca-ES";
  }

  function renderError(msg) {
    const ul = document.getElementById("concerts-upcoming");
    if (ul) ul.innerHTML = `<li class="concerts-error">⚠️ ${msg}</li>`;
  }

})();