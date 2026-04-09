
(() => {
  const pageUrl = document.body.dataset.pageUrl || "index.html";
  const sidebar = document.getElementById("site-sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  const searchInput = document.getElementById("docs-search");
  const searchResults = document.getElementById("search-results");
  const searchIndex = Array.isArray(window.NOVA_SYNESIS_SEARCH_INDEX) ? window.NOVA_SYNESIS_SEARCH_INDEX : [];

  if (toggle && sidebar) {
    toggle.addEventListener("click", () => {
      const open = sidebar.classList.toggle("site-sidebar--open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement !== searchInput) {
      event.preventDefault();
      searchInput?.focus();
      searchInput?.select();
    }
    if (event.key === "Escape") {
      searchResults?.setAttribute("hidden", "");
      if (document.activeElement === searchInput) {
        searchInput.blur();
      }
      sidebar?.classList.remove("site-sidebar--open");
      toggle?.setAttribute("aria-expanded", "false");
    }
  });

  function tokenize(query) {
    return query.toLowerCase().split(/\s+/).map((token) => token.trim()).filter(Boolean);
  }

  function toRelativeUrl(targetUrl) {
    const fromParts = pageUrl.split("/").slice(0, -1);
    const toParts = String(targetUrl).split("/");

    while (fromParts.length && toParts.length && fromParts[0] === toParts[0]) {
      fromParts.shift();
      toParts.shift();
    }

    const prefix = fromParts.map(() => "..");
    const joined = [...prefix, ...toParts].join("/");
    return joined || "index.html";
  }

  function scoreEntry(entry, tokens, rawQuery) {
    const title = String(entry.title || "").toLowerCase();
    const description = String(entry.description || "").toLowerCase();
    const headings = Array.isArray(entry.headings) ? entry.headings.join(" ").toLowerCase() : "";
    const body = String(entry.body || "").toLowerCase();
    let score = 0;

    for (const token of tokens) {
      if (title.includes(token)) score += 60;
      else if (headings.includes(token)) score += 28;
      else if (description.includes(token)) score += 18;
      else if (body.includes(token)) score += 8;
      else return 0;
    }

    if (title.includes(rawQuery)) score += 40;
    if (entry.url === pageUrl) score += 4;
    return score;
  }

  function buildExcerpt(entry, query) {
    const haystack = `${entry.description || ""} ${entry.body || ""}`.replace(/\s+/g, " ").trim();
    if (!haystack) return "";
    const lower = haystack.toLowerCase();
    const index = lower.indexOf(query);
    if (index === -1) return haystack.slice(0, 160);
    const start = Math.max(0, index - 50);
    const end = Math.min(haystack.length, index + 110);
    const prefix = start > 0 ? "…" : "";
    const suffix = end < haystack.length ? "…" : "";
    return `${prefix}${haystack.slice(start, end)}${suffix}`;
  }

  function renderResults(results, rawQuery) {
    if (!searchResults) return;
    if (!rawQuery) {
      searchResults.innerHTML = "";
      searchResults.setAttribute("hidden", "");
      return;
    }

    if (!results.length) {
      searchResults.innerHTML = `<div class="search-results__item"><div class="search-results__title">No results</div><div class="search-results__excerpt">No documentation page matches "${rawQuery}".</div></div>`;
      searchResults.removeAttribute("hidden");
      return;
    }

    searchResults.innerHTML = results.map((entry) => `
      <a class="search-results__item" href="${toRelativeUrl(entry.url)}">
        <span class="search-results__path">${entry.group || "Docs"}</span>
        <span class="search-results__title">${entry.title}</span>
        <span class="search-results__excerpt">${buildExcerpt(entry, rawQuery.toLowerCase())}</span>
      </a>
    `).join("");
    searchResults.removeAttribute("hidden");
  }

  searchInput?.addEventListener("input", (event) => {
    const rawQuery = String(event.target.value || "").trim();
    const tokens = tokenize(rawQuery);
    if (!tokens.length) {
      renderResults([], "");
      return;
    }

    const results = searchIndex
      .map((entry) => ({ ...entry, _score: scoreEntry(entry, tokens, rawQuery.toLowerCase()) }))
      .filter((entry) => entry._score > 0)
      .sort((left, right) => right._score - left._score)
      .slice(0, 12);

    renderResults(results, rawQuery);
  });

  document.addEventListener("click", (event) => {
    if (!searchResults || !searchInput) return;
    const target = event.target;
    if (target instanceof Node && (searchResults.contains(target) || searchInput.contains(target))) return;
    searchResults.setAttribute("hidden", "");
  });
})();
