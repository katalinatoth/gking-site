---
title: "Dataverse"
type: "dataverse"
---

Below is my Dataverse collection, which is comprised of data sets and replication data sets associated with my published articles and books. For information about the Dataverse project (which I created and run), see [this article](https://gking.harvard.edu/files/abs/dvn-abs.shtml) and the [Dataverse.org](https://dataverse.org/) project website.

<div id="dv-app">
  <div id="dv-header" style="background:#f5f5f5;border:1px solid #ddd;padding:12px 16px;display:flex;align-items:center;gap:8px;margin-bottom:0;">
    <a href="https://dataverse.harvard.edu/" target="_blank" rel="noopener" style="color:#337ab7;text-decoration:none;font-size:0.95rem;">Harvard Dataverse</a>
    <span style="color:#999;">&gt;</span>
    <input id="dv-search" type="text" placeholder="Search this dataverse..." style="flex:1;max-width:320px;padding:6px 10px;border:1px solid #ccc;border-radius:3px;font-size:0.9rem;">
    <button id="dv-search-btn" style="background:#337ab7;color:white;border:none;padding:6px 12px;border-radius:3px;cursor:pointer;font-size:0.9rem;">&#128269;</button>
    <a href="https://dataverse.harvard.edu/dataverse/king" target="_blank" rel="noopener" style="color:#337ab7;text-decoration:none;font-size:0.85rem;margin-left:8px;">Advanced Search</a>
  </div>

  <div style="display:flex;gap:0;border:1px solid #ddd;border-top:none;min-height:600px;">
    <!-- Left sidebar: facets -->
    <div id="dv-sidebar" style="width:240px;min-width:240px;background:#fff;border-right:1px solid #ddd;padding:0;font-size:0.85rem;">
      <div style="padding:10px 14px;border-bottom:1px solid #eee;">
        <label style="display:flex;align-items:center;gap:6px;margin:3px 0;color:#333;">
          <input type="checkbox" checked disabled> <span style="color:#337ab7;">&#128218;</span> Datasets (<span id="dv-count-badge">0</span>)
        </label>
      </div>
      <div style="padding:10px 14px;border-bottom:1px solid #eee;">
        <div style="font-weight:bold;margin-bottom:6px;color:#333;">Publication Year</div>
        <div id="dv-facet-year" style="max-height:160px;overflow-y:auto;"></div>
      </div>
      <div style="padding:10px 14px;border-bottom:1px solid #eee;">
        <div style="font-weight:bold;margin-bottom:6px;color:#333;">Subject</div>
        <div id="dv-facet-subject" style="max-height:160px;overflow-y:auto;"></div>
      </div>
      <div style="padding:10px 14px;">
        <div style="font-weight:bold;margin-bottom:6px;color:#333;">Author Name</div>
        <div id="dv-facet-author" style="max-height:200px;overflow-y:auto;"></div>
      </div>
    </div>

    <!-- Right: results -->
    <div style="flex:1;padding:16px 20px;background:#fff;">
      <div id="dv-status" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #eee;">
        <span id="dv-result-info" style="font-size:0.9rem;color:#555;"></span>
        <div style="display:flex;align-items:center;gap:6px;">
          <span style="font-size:0.85rem;color:#666;">Sort</span>
          <select id="dv-sort" style="padding:4px 8px;border:1px solid #ccc;border-radius:3px;font-size:0.85rem;">
            <option value="date:desc">Date (newest)</option>
            <option value="date:asc">Date (oldest)</option>
            <option value="name:asc">Name (A-Z)</option>
            <option value="name:desc">Name (Z-A)</option>
          </select>
        </div>
      </div>
      <div id="dv-results"></div>
      <div id="dv-pagination" style="display:flex;justify-content:center;gap:6px;margin-top:20px;padding-top:14px;border-top:1px solid #eee;"></div>
    </div>
  </div>

  <div style="text-align:center;margin-top:12px;font-size:0.8rem;color:#999;">
    Data loaded from <a href="https://dataverse.harvard.edu/dataverse/king" target="_blank" rel="noopener" style="color:#337ab7;">Harvard Dataverse</a> via the Search API
  </div>
</div>

<noscript>
<div style="margin:1.5rem 0;padding:1rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;text-align:center;">
  <p>This interactive Dataverse browser requires JavaScript. <a href="https://dataverse.harvard.edu/dataverse/king" target="_blank" rel="noopener">Browse the collection directly on Harvard Dataverse</a>.</p>
</div>
</noscript>

<style>
#dv-app { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
#dv-app a { color: #337ab7; }
#dv-app a:hover { color: #23527c; text-decoration: underline; }
.dv-item { padding: 14px 0; border-bottom: 1px solid #eee; }
.dv-item:last-child { border-bottom: none; }
.dv-item-title { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
.dv-item-title a { color: #337ab7; text-decoration: none; }
.dv-item-title a:hover { text-decoration: underline; }
.dv-item-date { font-size: 0.8rem; color: #888; margin-bottom: 3px; }
.dv-item-authors { font-size: 0.85rem; color: #555; margin-bottom: 4px; }
.dv-item-desc { font-size: 0.88rem; color: #444; line-height: 1.45; margin-bottom: 4px; }
.dv-item-meta { font-size: 0.8rem; color: #888; }
.dv-facet-item { display:flex; align-items:center; gap:4px; margin:2px 0; cursor:pointer; padding:2px 0; }
.dv-facet-item:hover { background:#f0f8ff; }
.dv-facet-item.active { font-weight:bold; color:#337ab7; }
.dv-facet-link { color: #337ab7; text-decoration: none; font-size: 0.85rem; }
.dv-facet-count { color: #999; font-size: 0.8rem; }
.dv-page-btn { padding: 5px 10px; border: 1px solid #ddd; background: #fff; color: #337ab7; cursor: pointer; border-radius: 3px; font-size: 0.85rem; }
.dv-page-btn:hover { background: #f0f8ff; }
.dv-page-btn.active { background: #337ab7; color: #fff; border-color: #337ab7; }
.dv-page-btn:disabled { color: #ccc; cursor: default; background: #f9f9f9; }
.dv-loading { text-align:center; padding:40px; color:#888; }
@media (max-width: 768px) {
  #dv-sidebar { display: none !important; }
  #dv-app > div:nth-child(2) { border: 1px solid #ddd; border-top: none; }
}
</style>

<script>
(function() {
  var API = 'https://dataverse.harvard.edu/api/search';
  var SUBTREE = 'king';
  var PER_PAGE = 10;
  var state = { q: '*', sort: 'date', order: 'desc', start: 0, facetYear: null, facetSubject: null, facetAuthor: null };
  var allItems = null;

  function fetchAll(callback) {
    var items = [];
    function fetchPage(start) {
      var url = API + '?q=' + encodeURIComponent(state.q === '' ? '*' : state.q) + '&subtree=' + SUBTREE + '&type=dataset&per_page=50&start=' + start + '&sort=' + state.sort + '&order=' + state.order;
      fetch(url)
        .then(function(r) { return r.json(); })
        .then(function(data) {
          items = items.concat(data.data.items);
          if (items.length < data.data.total_count && data.data.items.length > 0) {
            fetchPage(start + 50);
          } else {
            callback(items, data.data.total_count);
          }
        })
        .catch(function(err) {
          console.error('Dataverse API error:', err);
          document.getElementById('dv-results').innerHTML = '<div class="dv-loading">Failed to load datasets. <a href="https://dataverse.harvard.edu/dataverse/king" target="_blank">Browse on Harvard Dataverse</a>.</div>';
        });
    }
    fetchPage(0);
  }

  function buildFacets(items) {
    var years = {}, subjects = {}, authors = {};
    items.forEach(function(item) {
      var y = item.published_at ? item.published_at.substring(0, 4) : 'Unknown';
      years[y] = (years[y] || 0) + 1;
      (item.subjects || []).forEach(function(s) { subjects[s] = (subjects[s] || 0) + 1; });
      (item.authors || []).forEach(function(a) { authors[a] = (authors[a] || 0) + 1; });
    });

    renderFacet('dv-facet-year', years, 'facetYear', true);
    renderFacet('dv-facet-subject', subjects, 'facetSubject', false);
    var topAuthors = Object.entries(authors).sort(function(a,b) { return b[1] - a[1]; }).slice(0, 15);
    var authorObj = {};
    topAuthors.forEach(function(e) { authorObj[e[0]] = e[1]; });
    renderFacet('dv-facet-author', authorObj, 'facetAuthor', false);
  }

  function renderFacet(elId, data, stateKey, sortDesc) {
    var el = document.getElementById(elId);
    var entries = Object.entries(data);
    if (sortDesc) entries.sort(function(a,b) { return parseInt(b[0]) - parseInt(a[0]); });
    else entries.sort(function(a,b) { return b[1] - a[1]; });

    el.innerHTML = entries.map(function(e) {
      var isActive = state[stateKey] === e[0];
      return '<div class="dv-facet-item' + (isActive ? ' active' : '') + '" data-key="' + stateKey + '" data-val="' + e[0].replace(/"/g, '&quot;') + '">' +
        '<span class="dv-facet-link">' + e[0] + '</span> ' +
        '<span class="dv-facet-count">(' + e[1] + ')</span>' +
        '</div>';
    }).join('');

    el.querySelectorAll('.dv-facet-item').forEach(function(item) {
      item.addEventListener('click', function() {
        var key = this.dataset.key;
        var val = this.dataset.val;
        state[key] = state[key] === val ? null : val;
        state.start = 0;
        renderAll();
      });
    });
  }

  function filterItems(items) {
    return items.filter(function(item) {
      if (state.facetYear) {
        var y = item.published_at ? item.published_at.substring(0, 4) : 'Unknown';
        if (y !== state.facetYear) return false;
      }
      if (state.facetSubject) {
        if (!(item.subjects || []).includes(state.facetSubject)) return false;
      }
      if (state.facetAuthor) {
        if (!(item.authors || []).includes(state.facetAuthor)) return false;
      }
      return true;
    });
  }

  function sortItems(items) {
    var s = state.sort, o = state.order;
    return items.slice().sort(function(a, b) {
      if (s === 'date') {
        var da = a.published_at || '', db = b.published_at || '';
        return o === 'desc' ? db.localeCompare(da) : da.localeCompare(db);
      } else {
        var na = (a.name || '').toLowerCase(), nb = (b.name || '').toLowerCase();
        return o === 'asc' ? na.localeCompare(nb) : nb.localeCompare(na);
      }
    });
  }

  function renderResults(items) {
    var filtered = filterItems(items);
    var sorted = sortItems(filtered);
    var total = sorted.length;
    var start = state.start;
    var page = sorted.slice(start, start + PER_PAGE);

    document.getElementById('dv-count-badge').textContent = total;
    document.getElementById('dv-result-info').textContent = (start + 1) + ' to ' + Math.min(start + PER_PAGE, total) + ' of ' + total + ' Results';

    var html = '';
    page.forEach(function(item) {
      var date = item.published_at ? new Date(item.published_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '';
      var desc = item.description || '';
      if (desc.length > 300) desc = desc.substring(0, 300) + '...';
      var authors = (item.authors || []).join('; ');
      var kw = (item.keywords || []).join(' \u00b7 ');
      var meta = item.fileCount ? item.fileCount + ' file' + (item.fileCount > 1 ? 's' : '') : '';
      if (kw) meta += (meta ? ' \u00b7 ' : '') + kw;

      html += '<div class="dv-item">' +
        '<div class="dv-item-title"><a href="' + item.url + '" target="_blank" rel="noopener">' + item.name + '</a></div>' +
        '<div class="dv-item-date">' + date + (item.publisher ? ' - ' + item.publisher : '') + '</div>' +
        (authors ? '<div class="dv-item-authors">' + authors + '</div>' : '') +
        (desc ? '<div class="dv-item-desc">' + desc + '</div>' : '') +
        (meta ? '<div class="dv-item-meta">' + meta + '</div>' : '') +
        '</div>';
    });

    document.getElementById('dv-results').innerHTML = html || '<div class="dv-loading">No datasets found.</div>';

    // Pagination
    var totalPages = Math.ceil(total / PER_PAGE);
    var currentPage = Math.floor(start / PER_PAGE);
    var pag = document.getElementById('dv-pagination');
    if (totalPages <= 1) { pag.innerHTML = ''; return; }

    var pagHtml = '<button class="dv-page-btn" ' + (currentPage === 0 ? 'disabled' : '') + ' data-page="' + (currentPage - 1) + '">&laquo;</button>';
    var startP = Math.max(0, currentPage - 3);
    var endP = Math.min(totalPages, startP + 7);
    for (var i = startP; i < endP; i++) {
      pagHtml += '<button class="dv-page-btn' + (i === currentPage ? ' active' : '') + '" data-page="' + i + '">' + (i + 1) + '</button>';
    }
    pagHtml += '<button class="dv-page-btn" ' + (currentPage >= totalPages - 1 ? 'disabled' : '') + ' data-page="' + (currentPage + 1) + '">&raquo;</button>';
    pag.innerHTML = pagHtml;

    pag.querySelectorAll('.dv-page-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        if (this.disabled) return;
        state.start = parseInt(this.dataset.page) * PER_PAGE;
        renderResults(allItems);
        document.getElementById('dv-app').scrollIntoView({ behavior: 'smooth' });
      });
    });
  }

  function renderAll() {
    if (!allItems) return;
    buildFacets(allItems);
    renderResults(allItems);
  }

  function init() {
    document.getElementById('dv-results').innerHTML = '<div class="dv-loading">Loading datasets from Harvard Dataverse...</div>';

    fetchAll(function(items) {
      allItems = items;
      renderAll();
    });

    document.getElementById('dv-search-btn').addEventListener('click', doSearch);
    document.getElementById('dv-search').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') doSearch();
    });

    document.getElementById('dv-sort').addEventListener('change', function() {
      var v = this.value.split(':');
      state.sort = v[0];
      state.order = v[1];
      state.start = 0;
      if (allItems) {
        renderResults(allItems);
      }
    });
  }

  function doSearch() {
    var q = document.getElementById('dv-search').value.trim();
    state.q = q || '*';
    state.start = 0;
    state.facetYear = null;
    state.facetSubject = null;
    state.facetAuthor = null;
    document.getElementById('dv-results').innerHTML = '<div class="dv-loading">Searching...</div>';
    fetchAll(function(items) {
      allItems = items;
      renderAll();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
