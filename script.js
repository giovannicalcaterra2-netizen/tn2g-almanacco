const CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSzOoXRGax2NR3sUI-2ai-fI2nKi_Hq2zkxBGGxDMpTqjxOYYn1JK9YJt6J4uEngoVX7N0BZaigLkz4/pub?gid=0&single=true&output=csv";
const GOOGLE_CALENDAR_SUBSCRIBE_URL = "https://calendar.google.com/calendar/u/0?cid=NDA3NTJiYjgzZGZjNDcyOTRkM2Y2ODAyYTE5M2E2ZmVlZGIxOGYyNjRkN2MzMzEyYWZkNDk5MDM3ZDFjYzdiMEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t";

let events = [];
let currentDate = new Date();

document.addEventListener("DOMContentLoaded", async () => {
  document.getElementById("googleCalendarButton").href = GOOGLE_CALENDAR_SUBSCRIBE_URL;

  document.getElementById("prevMonth").addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderAll();
  });

  document.getElementById("nextMonth").addEventListener("click", () => {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderAll();
  });

  events = await loadEvents();
  renderAll();
});

async function loadEvents() {
  const response = await fetch(CSV_URL);
  const text = await response.text();
  const rows = parseCSV(text);

  const headers = rows[0].map(h => h.trim());

  return rows.slice(1)
    .map(row => {
      const item = {};
      headers.forEach((header, index) => {
        item[header] = row[index] ? row[index].trim() : "";
      });
      return item;
    })
    .filter(item => {
      const pubblica = normalize(item.pubblica);
      return pubblica === "si" || pubblica === "sì" || pubblica === "yes";
    })
    .map(item => ({
      id: item.id,
      tipo: item.tipo,
      titolo: item.titolo || buildFallbackTitle(item),
      nome: item.nome,
      data: item.data,
      ora_inizio: item.ora_inizio,
      ora_fine: item.ora_fine,
      categoria: item.categoria,
      luogo: item.luogo,
      segno: item.segno,
      oroscopo: item.oroscopo,
      descrizione: item.descrizione,
      link: item.link,
      ricorrente: item.ricorrente
    }));
}

function renderAll() {
  renderToday();
  renderUpcoming();
  renderBirthdays();
  renderCalendar();
}

function renderToday() {
  const container = document.getElementById("todayEvents");
  const todayKey = toDateKey(new Date());

  const todayEvents = events.filter(event => {
    return getEventDateKeyForCurrentYear(event) === todayKey;
  });

  renderCards(container, todayEvents, "Oggi nessun evento in programma.");
}

function renderUpcoming() {
  const container = document.getElementById("upcomingEvents");
  const today = startOfDay(new Date());

  const upcoming = events
    .map(event => ({
      ...event,
      effectiveDate: getEffectiveDate(event, today)
    }))
    .filter(event => event.effectiveDate >= today)
    .sort((a, b) => a.effectiveDate - b.effectiveDate)
    .slice(0, 6);

  renderCards(container, upcoming, "Nessun evento futuro trovato.");
}

function renderBirthdays() {
  const container = document.getElementById("birthdayEvents");
  const month = currentDate.getMonth();

  const birthdays = events
    .filter(event => normalize(event.tipo) === "compleanno")
    .filter(event => {
      const d = parseDate(event.data);
      return d && d.getMonth() === month;
    })
    .sort((a, b) => parseDate(a.data).getDate() - parseDate(b.data).getDate());

  renderCards(container, birthdays, "Nessun compleanno questo mese.");
}

function renderCalendar() {
  const title = document.getElementById("calendarTitle");
  const grid = document.getElementById("calendarGrid");

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  title.textContent = currentDate.toLocaleDateString("it-IT", {
    month: "long",
    year: "numeric"
  });

  grid.innerHTML = "";

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  let startOffset = firstDay.getDay() - 1;
  if (startOffset < 0) startOffset = 6;

  for (let i = 0; i < startOffset; i++) {
    const empty = document.createElement("div");
    empty.className = "day empty";
    grid.appendChild(empty);
  }

  for (let day = 1; day <= lastDay.getDate(); day++) {
    const date = new Date(year, month, day);
    const dateKey = toDateKey(date);
    const todayKey = toDateKey(new Date());

    const dayEvents = events.filter(event => {
      return getEventDateKeyInYear(event, year) === dateKey;
    });

    const cell = document.createElement("div");
    cell.className = "day";

    if (dateKey === todayKey) {
      cell.classList.add("today");
    }

    const number = document.createElement("div");
    number.className = "day-number";
    number.textContent = day;
    cell.appendChild(number);

    dayEvents.forEach(event => {
      const eventEl = document.createElement("div");
      eventEl.className = "day-event";
      eventEl.textContent = getIcon(event) + " " + event.titolo;
      cell.appendChild(eventEl);
    });

    grid.appendChild(cell);
  }
}

function renderCards(container, items, emptyMessage) {
  container.innerHTML = "";

  if (!items.length) {
    const empty = document.createElement("p");
    empty.textContent = emptyMessage;
    container.appendChild(empty);
    return;
  }

  items.forEach(event => {
    const card = document.createElement("article");
    card.className = "card";

    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = getIcon(event) + " " + (event.categoria || event.tipo || "TN2G");
    card.appendChild(badge);

    const title = document.createElement("p");
    title.className = "card-title";
    title.textContent = event.titolo;
    card.appendChild(title);

    const meta = document.createElement("p");
    meta.className = "card-meta";
    meta.textContent = buildMeta(event);
    card.appendChild(meta);

    if (event.oroscopo) {
      const astro = document.createElement("p");
      astro.className = "card-description";
      astro.textContent = "✨ " + event.oroscopo;
      card.appendChild(astro);
    } else if (event.descrizione) {
      const description = document.createElement("p");
      description.className = "card-description";
      description.textContent = event.descrizione;
      card.appendChild(description);
    }

    container.appendChild(card);
  });
}

function buildFallbackTitle(item) {
  if (normalize(item.tipo) === "compleanno" && item.nome) {
    return "Compleanno di " + item.nome + " 🎂";
  }

  return "Evento TN2G";
}

function buildMeta(event) {
  const parts = [];

  const d = parseDate(event.data);
  if (d) {
    parts.push(d.toLocaleDateString("it-IT", {
      day: "numeric",
      month: "long",
      year: "numeric"
    }));
  }

  if (event.ora_inizio) {
    parts.push(event.ora_inizio);
  }

  if (event.luogo) {
    parts.push(event.luogo);
  }

  if (event.segno) {
    parts.push("♈︎ " + event.segno);
  }

  return parts.join(" · ");
}

function getIcon(event) {
  const category = normalize(event.categoria || event.tipo);

  const icons = {
    compleanno: "🎂",
    aperitivo: "🍻",
    outdoor: "🥾",
    nerd: "🎲",
    cinema: "🎬",
    salotto: "📚",
    musica: "🎧",
    sport: "⚽",
    evento: "🔱"
  };

  return icons[category] || "🔱";
}

function parseDate(value) {
  if (!value) return null;

  const parts = value.split("-");
  if (parts.length !== 3) return null;

  return new Date(
    Number(parts[0]),
    Number(parts[1]) - 1,
    Number(parts[2])
  );
}

function getEffectiveDate(event, today) {
  const d = parseDate(event.data);
  if (!d) return new Date(9999, 0, 1);

  if (normalize(event.tipo) === "compleanno" || normalize(event.ricorrente) === "annuale") {
    let next = new Date(today.getFullYear(), d.getMonth(), d.getDate());

    if (next < today) {
      next = new Date(today.getFullYear() + 1, d.getMonth(), d.getDate());
    }

    return next;
  }

  return d;
}

function getEventDateKeyForCurrentYear(event) {
  const now = new Date();
  return getEventDateKeyInYear(event, now.getFullYear());
}

function getEventDateKeyInYear(event, year) {
  const d = parseDate(event.data);
  if (!d) return "";

  if (normalize(event.tipo) === "compleanno" || normalize(event.ricorrente) === "annuale") {
    return toDateKey(new Date(year, d.getMonth(), d.getDate()));
  }

  return toDateKey(d);
}

function toDateKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function normalize(value) {
  return String(value || "").toLowerCase().trim();
}

function parseCSV(text) {
  const rows = [];
  let currentRow = [];
  let currentValue = "";
  let insideQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const nextChar = text[i + 1];

    if (char === '"' && insideQuotes && nextChar === '"') {
      currentValue += '"';
      i++;
    } else if (char === '"') {
      insideQuotes = !insideQuotes;
    } else if (char === "," && !insideQuotes) {
      currentRow.push(currentValue);
      currentValue = "";
    } else if ((char === "\n" || char === "\r") && !insideQuotes) {
      if (currentValue || currentRow.length) {
        currentRow.push(currentValue);
        rows.push(currentRow);
        currentRow = [];
        currentValue = "";
      }

      if (char === "\r" && nextChar === "\n") {
        i++;
      }
    } else {
      currentValue += char;
    }
  }

  if (currentValue || currentRow.length) {
    currentRow.push(currentValue);
    rows.push(currentRow);
  }

  return rows;
}
