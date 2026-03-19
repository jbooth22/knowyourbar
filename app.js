/* ===================================================
   KYB App Logic
   =================================================== */

const CERT_MAP = {
  'Vegan':      'Vegan (Y/N)',
  'GF':         'Gluten Free (Y/N)',
  'Dairy Free': 'Dairy Free (Y/N)',
  'Soy Free':   'Soy Free (Y/N)',
  'Non-GMO':    'Non-GMO (Y/N)',
  'Nut Free':   'Nut Free (Y/N)',
  'Kosher':     'Kosher (Y/N)',
};

const CERT_FULL = {
  'GF': 'Gluten Free',
};

const SLIDERS_CFG = [
  { key: 'Protein (g)',       label: 'Min Protein',      min: 0,  max: 30,  step: 1,  dir: 'min', unit: 'g',   default: 0 },
  { key: 'Calories',          label: 'Max Calories',      min: 90, max: 410, step: 10, dir: 'max', unit: 'cal', default: 410 },
  { key: 'Sugars (g)',        label: 'Max Sugars',        min: 0,  max: 29,  step: 1,  dir: 'max', unit: 'g',   default: 29 },
  { key: 'Sugar Alcohol (g)', label: 'Max Sugar Alcohol', min: 0,  max: 20,  step: 1,  dir: 'max', unit: 'g',   default: 20 },
  { key: 'Dietary Fiber (g)', label: 'Min Fiber',         min: 0,  max: 17,  step: 1,  dir: 'min', unit: 'g',   default: 0 },
  { key: 'Sodium (mg)',       label: 'Max Sodium',        min: 0,  max: 760, step: 10, dir: 'max', unit: 'mg',  default: 760 },
];

// ─── State ───────────────────────────────────────────
let activeCerts   = {};
let sliderValues  = {};
let exclusions    = [];
let expandedRow   = null;
let currentFiltered = [];

// ─── Init ────────────────────────────────────────────
function init() {
  buildCertChips();
  buildSliders();
  bindSearch();
  bindSort();
  bindExclInput();
  document.getElementById('bar-count').textContent  = BARS.length;
  document.getElementById('footer-count').textContent = BARS.length;
  applyFilters();
}

function buildCertChips() {
  const grid = document.getElementById('cert-grid');
  Object.keys(CERT_MAP).forEach(label => {
    activeCerts[label] = false;
    const chip = document.createElement('button');
    chip.className = 'cert-chip';
    chip.id = 'cert-' + label;
    chip.textContent = label;
    chip.setAttribute('aria-pressed', 'false');
    chip.addEventListener('click', () => {
      activeCerts[label] = !activeCerts[label];
      chip.classList.toggle('active', activeCerts[label]);
      chip.setAttribute('aria-pressed', String(activeCerts[label]));
      applyFilters();
    });
    grid.appendChild(chip);
  });
}

function buildSliders() {
  const list = document.getElementById('sliders-list');
  SLIDERS_CFG.forEach(cfg => {
    sliderValues[cfg.key] = cfg.default;
    const row = document.createElement('div');
    row.className = 'slider-row';
    row.innerHTML = `
      <div class="slider-header">
        <span class="slider-name">${cfg.label}</span>
        <span class="slider-val" id="sv-${cfg.key}">${cfg.default}${cfg.unit}</span>
      </div>
      <input type="range" min="${cfg.min}" max="${cfg.max}" step="${cfg.step}"
             value="${cfg.default}" id="sl-${cfg.key}" aria-label="${cfg.label}">`;
    list.appendChild(row);
    row.querySelector('input').addEventListener('input', e => {
      const val = parseFloat(e.target.value);
      sliderValues[cfg.key] = val;
      document.getElementById('sv-' + cfg.key).textContent = val + cfg.unit;
      applyFilters();
    });
  });
}

function bindSearch() {
  document.getElementById('search-input').addEventListener('input', applyFilters);
}

function bindSort() {
  document.getElementById('sort-col').addEventListener('change', applyFilters);
  document.getElementById('sort-dir').addEventListener('change', applyFilters);
}

function bindExclInput() {
  document.getElementById('excl-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') addExclusion();
  });
}

// ─── Exclusions ──────────────────────────────────────
function addExclusion() {
  const inp = document.getElementById('excl-input');
  const raw = inp.value.trim();
  if (!raw) return;
  const term = raw.toLowerCase();
  if (!exclusions.includes(term)) {
    exclusions.push(term);
    renderExclTags();
    applyFilters();
  }
  inp.value = '';
}

function removeExclusion(term) {
  exclusions = exclusions.filter(x => x !== term);
  renderExclTags();
  applyFilters();
}

function renderExclTags() {
  const div = document.getElementById('excl-tags');
  div.innerHTML = '';
  exclusions.forEach(term => {
    const tag = document.createElement('span');
    tag.className = 'excl-tag';
    tag.innerHTML = `${term} <button aria-label="Remove ${term}" onclick="removeExclusion('${term}')">×</button>`;
    div.appendChild(tag);
  });
}

// ─── Reset ───────────────────────────────────────────
function resetAll() {
  document.getElementById('search-input').value = '';
  Object.keys(activeCerts).forEach(k => {
    activeCerts[k] = false;
    const chip = document.getElementById('cert-' + k);
    if (chip) { chip.classList.remove('active'); chip.setAttribute('aria-pressed', 'false'); }
  });
  SLIDERS_CFG.forEach(cfg => {
    sliderValues[cfg.key] = cfg.default;
    const sl = document.getElementById('sl-' + cfg.key);
    const sv = document.getElementById('sv-' + cfg.key);
    if (sl) sl.value = cfg.default;
    if (sv) sv.textContent = cfg.default + cfg.unit;
  });
  exclusions = [];
  renderExclTags();
  applyFilters();
}

// ─── Core filter + render ────────────────────────────
function applyFilters() {
  const q        = document.getElementById('search-input').value.toLowerCase();
  const sortCol  = document.getElementById('sort-col').value;
  const sortDir  = document.getElementById('sort-dir').value;

  // Filter
  let filtered = BARS.filter(bar => {
    // Text search
    if (q) {
      const haystack = ((bar['Brand Name'] || '') + ' ' + (bar['Flavor Name'] || '')).toLowerCase();
      if (!haystack.includes(q)) return false;
    }

    // Certs — must have ALL active certs
    for (const [label, col] of Object.entries(CERT_MAP)) {
      if (!activeCerts[label]) continue;
      const v = bar[col];
      if (!v || v.trim().toLowerCase() !== 'yes') return false;
    }

    // Sliders
    for (const cfg of SLIDERS_CFG) {
      const v = bar[cfg.key];
      if (v === null || v === undefined) continue;
      if (cfg.dir === 'max' && v > sliderValues[cfg.key]) return false;
      if (cfg.dir === 'min' && v < sliderValues[cfg.key]) return false;
    }

    // Ingredient exclusions
    if (exclusions.length > 0) {
      const ingr = (bar['Ingredients'] || '').toLowerCase();
      for (const term of exclusions) {
        if (ingr.includes(term)) return false;
      }
    }

    return true;
  });

  // Sort
  filtered.sort((a, b) => {
    let av, bv;
    if (sortCol === 'brand') {
      av = (a['Brand Name'] || '').toLowerCase();
      bv = (b['Brand Name'] || '').toLowerCase();
    } else {
      av = a[sortCol] ?? -Infinity;
      bv = b[sortCol] ?? -Infinity;
    }
    if (av < bv) return sortDir === 'asc' ? -1 : 1;
    if (av > bv) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  currentFiltered = filtered;

  // Update counts
  const countEl = document.getElementById('result-count');
  if (countEl) countEl.textContent = filtered.length + ' bar' + (filtered.length !== 1 ? 's' : '');

  const infoEl = document.getElementById('toolbar-info');
  if (infoEl) infoEl.textContent = `Showing ${Math.min(filtered.length, 150)} of ${filtered.length} results`;

  // Render
  renderTable(filtered);
}

// ─── Table render ────────────────────────────────────
function renderTable(bars) {
  const tbody   = document.getElementById('results-body');
  const noRes   = document.getElementById('no-results');
  const truncEl = document.getElementById('truncation-note');

  // Close any open expand row
  closeExpand();

  tbody.innerHTML = '';

  if (bars.length === 0) {
    noRes.classList.remove('hidden');
    truncEl.classList.add('hidden');
    return;
  }

  noRes.classList.add('hidden');

  const limit   = 150;
  const display = bars.slice(0, limit);

  display.forEach(bar => {
    const row = document.createElement('tr');
    row.dataset.key = bar['Brand Name'] + '|' + bar['Flavor Name'];

    // Cert badges (short labels)
    const certBadges = [];
    if (bar['Vegan (Y/N)']?.trim().toLowerCase() === 'yes')       certBadges.push('Vegan');
    if (bar['Gluten Free (Y/N)']?.trim().toLowerCase() === 'yes') certBadges.push('GF');
    if (bar['Dairy Free (Y/N)']?.trim().toLowerCase() === 'yes')  certBadges.push('DF');
    if (bar['Soy Free (Y/N)']?.trim().toLowerCase() === 'yes')    certBadges.push('SF');
    if (bar['Non-GMO (Y/N)']?.trim().toLowerCase() === 'yes')     certBadges.push('GMO');
    if (bar['Nut Free (Y/N)']?.trim().toLowerCase() === 'yes')    certBadges.push('NF');
    if (bar['Kosher (Y/N)']?.trim().toLowerCase() === 'yes')      certBadges.push('Ko');

    const badgeHTML = '<div class="cert-badges">' + certBadges.map(b => `<span class="cert-badge">${b}</span>`).join('') + '</div>';
    const linkHTML  = bar['Website'] ? `<a href="${bar['Website']}" target="_blank" rel="noopener" class="ext-link" onclick="event.stopPropagation()" aria-label="Visit ${bar['Brand Name']} website">↗</a>` : '';

    row.innerHTML = `
      <td class="col-bar">
        <div class="bar-brand">${bar['Brand Name'] || ''}</div>
        <div class="bar-flavor">${bar['Flavor Name'] || ''}</div>
      </td>
      <td class="col-num">${fmt(bar['Protein (g)'])}</td>
      <td class="col-num">${fmt(bar['Calories'])}</td>
      <td class="col-num">${fmt(bar['Sugars (g)'])}</td>
      <td class="col-num">${fmt(bar['Sugar Alcohol (g)'])}</td>
      <td class="col-num">${fmt(bar['Dietary Fiber (g)'])}</td>
      <td class="col-num">${fmt(bar['Total Fat (g)'])}</td>
      <td class="col-num">${fmt(bar['Sodium (mg)'])}</td>
      <td class="col-size">${bar['Size'] || ''}</td>
      <td class="col-certs">${badgeHTML}</td>
      <td class="col-link">${linkHTML}</td>`;

    row.addEventListener('click', () => toggleExpand(bar, row));
    tbody.appendChild(row);
  });

  if (bars.length > limit) {
    truncEl.classList.remove('hidden');
    truncEl.textContent = `Showing first ${limit} of ${bars.length} results. Use filters to narrow down.`;
  } else {
    truncEl.classList.add('hidden');
  }
}

function fmt(v) {
  if (v === null || v === undefined) return '<span style="color:#bbb">—</span>';
  return v;
}

// ─── Expand row ──────────────────────────────────────
function closeExpand() {
  const existing = document.querySelector('.expand-detail');
  if (existing) existing.remove();
  if (expandedRow) {
    expandedRow.classList.remove('expanded');
    expandedRow = null;
  }
}

function toggleExpand(bar, row) {
  const isOpen = row.classList.contains('expanded');
  closeExpand();
  if (isOpen) return;

  row.classList.add('expanded');
  expandedRow = row;

  // Full cert list
  const certFull = [];
  const certMap2 = [
    ['Vegan',      'Vegan (Y/N)'],
    ['Gluten Free','Gluten Free (Y/N)'],
    ['Dairy Free', 'Dairy Free (Y/N)'],
    ['Soy Free',   'Soy Free (Y/N)'],
    ['Non-GMO',    'Non-GMO (Y/N)'],
    ['Nut Free',   'Nut Free (Y/N)'],
    ['Kosher',     'Kosher (Y/N)'],
  ];
  certMap2.forEach(([label, col]) => {
    if (bar[col]?.trim().toLowerCase() === 'yes') certFull.push(label);
  });

  // Macro pills
  const macros = [
    ['Protein',       bar['Protein (g)'],       'g'],
    ['Calories',      bar['Calories'],           ''],
    ['Total Fat',     bar['Total Fat (g)'],      'g'],
    ['Sat Fat',       bar['Saturated Fat (g)'],  'g'],
    ['Carbs',         bar['Total Carbohydrates (g)'], 'g'],
    ['Fiber',         bar['Dietary Fiber (g)'],  'g'],
    ['Sugars',        bar['Sugars (g)'],         'g'],
    ['Sugar Alcohol', bar['Sugar Alcohol (g)'],  'g'],
    ['Sodium',        bar['Sodium (mg)'],        'mg'],
    ['Cholesterol',   bar['Cholesterol (mg)'],   'mg'],
    ['Potassium',     bar['Potassium (mg)'],     'mg'],
    ['Caffeine',      bar['Caffeine (mg)'],      'mg'],
  ].filter(([, v]) => v !== null && v !== undefined);

  const highlightKeys = new Set(['Protein', 'Calories', 'Sugars', 'Sugar Alcohol', 'Fiber']);

  const macroPills = macros.map(([k, v, u]) => {
    const cls = highlightKeys.has(k) ? 'macro-pill highlight' : 'macro-pill';
    return `<span class="${cls}">${k}: ${v}${u}</span>`;
  }).join('');

  const certPills = certFull.map(c => `<span class="cert-pill">${c}</span>`).join('');

  const ingrSection = bar['Ingredients']
    ? `<div class="ingr-label">Ingredients</div><div class="ingr-text">${bar['Ingredients']}</div>`
    : `<div class="ingr-missing">Ingredient list not available for this bar.</div>`;

  const sizeServing = [bar['Size'], bar['Type'], bar['Serving Size (g)'] ? bar['Serving Size (g)'] + 'g serving' : null]
    .filter(Boolean).join(' · ');

  const expandRow = document.createElement('tr');
  expandRow.className = 'expand-detail';
  expandRow.innerHTML = `<td colspan="11">
    <div class="expand-content">
      <div style="font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-bottom:10px;letter-spacing:0.05em;">${sizeServing}</div>
      <div class="macro-strip">${macroPills}</div>
      ${certPills ? `<div class="cert-strip">${certPills}</div>` : ''}
      ${ingrSection}
    </div>
  </td>`;

  row.after(expandRow);
}

// ─── Bootstrap ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
