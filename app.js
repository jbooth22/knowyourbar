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
  { key: 'Protein (g)',                label: 'Min Protein',      min: 0,  max: 30,  step: 1,  dir: 'min', unit: 'g',   default: 0 },
  { key: 'Calories',                   label: 'Max Calories',      min: 90, max: 410, step: 10, dir: 'max', unit: 'cal', default: 410 },
  { key: 'Total Fat (g)',              label: 'Max Fat',           min: 0,  max: 30,  step: 1,  dir: 'max', unit: 'g',   default: 30 },
  { key: 'Total Carbohydrates (g)',    label: 'Max Carbs',         min: 0,  max: 50,  step: 1,  dir: 'max', unit: 'g',   default: 50 },
  { key: 'Sugars (g)',                 label: 'Max Sugars',        min: 0,  max: 29,  step: 1,  dir: 'max', unit: 'g',   default: 29 },
  { key: 'Sugar Alcohol (g)',          label: 'Max Sugar Alcohol', min: 0,  max: 20,  step: 1,  dir: 'max', unit: 'g',   default: 20 },
  { key: 'Dietary Fiber (g)',          label: 'Min Fiber',         min: 0,  max: 17,  step: 1,  dir: 'min', unit: 'g',   default: 0 },
  { key: 'Sodium (mg)',                label: 'Max Sodium',        min: 0,  max: 760, step: 10, dir: 'max', unit: 'mg',  default: 760 },
];

const BRAND_LIST = ["88 Acres","Alani","Aloha","Anabar","Atkins","Atlas","B.T.R. Nation","Barebells","Bob's Red Mill","Bobo's","Built","CLIF Bar","Clif Builders","Clif ZBar","Daryl's Bars","David","Epic","Equate","FITCRUNCH","Fiber One","Fulfil","GNC Total Lean","Gatorade","Ghost","GoMacro","Gryp","Honey Stinger","IQ Bar","Jacob","Jambar","Kize","Laird","Larabar","Legendary","Lineage Provisions","Luna","Mezcla","Mosh","Munk Pack","Mush","Nature Valley","Nick's","No Cow","NuGo","One","PEAK Protein","PROBar","Perfect Bar","Possible","Power Crunch","Prima","Pure Protein","Quest","RXBAR","Raw Rev","Ready","Redefine","Rise","Send","Simply Protein","Stars and Honey","The Gluten Free Brothers","Trubar","Wonderslim","Zing","think!"];

// ─── State ───────────────────────────────────────────
let activeCerts    = {};
let sliderValues   = {};
let exclusions     = [];
let selectedBrands = new Set();
let activePreset   = null;
let activeGrade    = null;   // 'A' | 'B' | 'C' | 'D' | 'F' | null
let expandedRow    = null;
let currentFiltered = [];

function init() {
  buildBrandList();
  buildCertChips();
  buildSliders();
  buildGradeFilter();
  bindSearch();
  bindSort();
  bindExclInput();
  bindBrandSearch();
  bindPresets();
  readURLParams();
  document.getElementById('bar-count').textContent  = BARS.length;
  document.getElementById('footer-count').textContent = BARS.length;
  applyFilters();
}

function readURLParams() {
  const params = new URLSearchParams(window.location.search);

  // ?band=A  — activate grade filter
  const band = params.get('band');
  if (band && ['A','B','C','D','F'].includes(band.toUpperCase())) {
    activeGrade = band.toUpperCase();
    // Reflect in the grade filter UI
    document.querySelectorAll('.grade-filter-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.grade === activeGrade);
    });
  }

  // ?bar=slug  — auto-expand a specific bar on load
  const barSlug = params.get('bar');
  if (barSlug) {
    // Store for after first render
    window._autoExpandSlug = barSlug;
  }
}

function bindPresets() {
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => applyPreset(btn.dataset.preset));
  });
}

function buildGradeFilter() {
  const container = document.getElementById('grade-filter-btns');
  if (!container) return;
  const grades = [
    { band: 'A', label: 'Clean',  color: '#2a7a1f' },
    { band: 'B', label: 'Good',   color: '#5a8a2f' },
    { band: 'C', label: 'Okay',   color: '#b89a00' },
    { band: 'D', label: 'Poor',   color: '#c87020' },
    { band: 'F', label: 'Avoid',  color: '#c83020' },
  ];
  grades.forEach(({ band, label, color }) => {
    const btn = document.createElement('button');
    btn.className = 'grade-filter-btn';
    btn.dataset.grade = band;
    btn.setAttribute('aria-label', `Filter by grade ${band} — ${label}`);
    btn.innerHTML = `<span class="grade-filter-badge" style="background:${color}">${band}</span><span class="grade-filter-label">${label}</span>`;
    btn.addEventListener('click', () => {
      activeGrade = (activeGrade === band) ? null : band;
      container.querySelectorAll('.grade-filter-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.grade === activeGrade);
      });
      applyFilters();
    });
    container.appendChild(btn);
  });
}


function buildBrandList() {
  const list = document.getElementById('brand-list');
  BRAND_LIST.forEach(brand => {
    const item = document.createElement('label');
    item.className = 'brand-item';
    item.innerHTML = `<input type="checkbox" value="${brand}" onchange="toggleBrand('${brand}', this.checked)"><span>${brand}</span>`;
    list.appendChild(item);
  });
}

function toggleBrand(brand, checked) {
  if (checked) selectedBrands.add(brand);
  else selectedBrands.delete(brand);
  updateBrandCount();
  applyFilters();
}

function clearBrands() {
  selectedBrands.clear();
  document.querySelectorAll('#brand-list input[type=checkbox]').forEach(cb => cb.checked = false);
  document.getElementById('brand-search').value = '';
  filterBrandList('');
  updateBrandCount();
  applyFilters();
}

function updateBrandCount() {
  const el = document.getElementById('brand-selected-count');
  const clearBtn = document.getElementById('brand-clear-btn');
  if (selectedBrands.size > 0) {
    el.textContent = selectedBrands.size + ' selected';
    clearBtn.style.display = 'inline-block';
  } else {
    el.textContent = '';
    clearBtn.style.display = 'none';
  }
}

function bindBrandSearch() {
  const input = document.getElementById('brand-search');
  input.addEventListener('input', e => filterBrandList(e.target.value));
}

function filterBrandList(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('#brand-list .brand-item').forEach(item => {
    const brand = item.querySelector('span').textContent.toLowerCase();
    item.style.display = brand.includes(q) ? '' : 'none';
  });
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

// ─── Presets ─────────────────────────────────────────
const PRESETS = {
  efficiency: {
    label: 'High Protein Low Calorie',
    description: 'Protein calories ≥ 40% of total · sorted by best efficiency',
    apply: (bar) => {
      if (!bar['Calories'] || !bar['Protein (g)']) return false;
      const efficiency = (bar['Protein (g)'] * 4) / bar['Calories'];
      return efficiency >= 0.40;
    },
    sort: { col: 'efficiency', dir: 'desc' }
  },
  clean: {
    label: 'High Protein, No Artificial Sweeteners',
    description: 'Protein ≥ 15g · no sucralose, acesulfame, aspartame, saccharin, or maltitol · sorted by protein',
    apply: (bar) => {
      if (!bar['Protein (g)'] || bar['Protein (g)'] < 15) return false;
      const ingr = (bar['Ingredients'] || '').toLowerCase();
      const artificial = ['sucralose', 'acesulfame', 'aspartame', 'saccharin', 'maltitol'];
      return !artificial.some(s => ingr.includes(s));
    },
    sort: { col: 'Protein (g)', dir: 'desc' }
  },
  lowsugar: {
    label: 'High Protein, Least Sugar',
    description: 'Protein ≥ 15g · zero sugar alcohol · sorted by lowest sugars',
    apply: (bar) => {
      if (!bar['Protein (g)'] || bar['Protein (g)'] < 15) return false;
      if (bar['Sugar Alcohol (g)'] === null || bar['Sugar Alcohol (g)'] === undefined) return false;
      return bar['Sugar Alcohol (g)'] === 0;
    },
    sort: { col: 'Sugars (g)', dir: 'asc' }
  },
  fiber: {
    label: 'High Fiber, Low Sugar',
    description: '8g+ fiber · 5g or less sugar · sorted by most fiber',
    apply: (bar) => {
      const fiber = bar['Dietary Fiber (g)'];
      const sugar = bar['Sugars (g)'];
      if (fiber === null || fiber === undefined) return false;
      if (sugar === null || sugar === undefined) return false;
      return fiber >= 8 && sugar <= 5;
    },
    sort: { col: 'Dietary Fiber (g)', dir: 'desc' }
  }
};

function applyPreset(presetKey) {
  const btn = document.querySelector(`[data-preset="${presetKey}"]`);
  if (activePreset === presetKey) {
    activePreset = null;
    btn.classList.remove('active');
  } else {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    activePreset = presetKey;
    btn.classList.add('active');
  }
  applyFilters();
}

function updatePresetBanner(filteredCount) {
  const banner = document.getElementById('preset-banner');
  if (!banner) return;
  if (!activePreset) {
    banner.classList.add('hidden');
    banner.innerHTML = '';
    return;
  }
  const preset = PRESETS[activePreset];
  banner.classList.remove('hidden');
  banner.innerHTML = `
    <span class="banner-label">${preset.label}</span>
    <span class="banner-divider">·</span>
    <span class="banner-desc">${preset.description}</span>
    <span class="banner-count">${filteredCount} bars</span>
  `;
}


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
  document.getElementById('brand-search').value = '';
  selectedBrands.clear();
  document.querySelectorAll('#brand-list input[type=checkbox]').forEach(cb => cb.checked = false);
  filterBrandList('');
  updateBrandCount();
  activePreset = null;
  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
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
  const q = document.getElementById('search-input').value.toLowerCase();

  // Filter
  let filtered = BARS.filter(bar => {
    // Preset filter
    if (activePreset && !PRESETS[activePreset].apply(bar)) return false;

    // Grade filter
    if (activeGrade && bar['score_band'] !== activeGrade) return false;

    // Brand filter
    if (selectedBrands.size > 0 && !selectedBrands.has(bar['Brand Name'])) return false;

    // Flavor keyword search
    if (q) {
      const haystack = (bar['Flavor Name'] || '').toLowerCase();
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

  // Sort — preset overrides manual sort when active
  let sortCol = document.getElementById('sort-col').value;
  let sortDir = document.getElementById('sort-dir').value;

  if (activePreset && PRESETS[activePreset].sort) {
    sortCol = PRESETS[activePreset].sort.col;
    sortDir = PRESETS[activePreset].sort.dir;
  }

  filtered.sort((a, b) => {
    let av, bv;
    if (sortCol === 'brand') {
      av = (a['Brand Name'] || '').toLowerCase();
      bv = (b['Brand Name'] || '').toLowerCase();
    } else if (sortCol === 'efficiency') {
      av = a['Calories'] ? (a['Protein (g)'] * 4) / a['Calories'] : 0;
      bv = b['Calories'] ? (b['Protein (g)'] * 4) / b['Calories'] : 0;
    } else {
      av = a[sortCol] ?? -Infinity;
      bv = b[sortCol] ?? -Infinity;
    }
    if (av < bv) return sortDir === 'asc' ? -1 : 1;
    if (av > bv) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  currentFiltered = filtered;

  // Update preset banner
  updatePresetBanner(filtered.length);

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
      <td class="col-num col-hide-mobile">${fmt(bar['Calories'])}</td>
      <td class="col-num">${fmt(bar['Protein (g)'])}</td>
      <td class="col-num">${fmt(bar['Total Fat (g)'])}</td>
      <td class="col-num col-hide-mobile">${fmt(bar['Total Carbohydrates (g)'])}</td>
      <td class="col-num">${fmt(bar['Dietary Fiber (g)'])}</td>
      <td class="col-num">${fmt(bar['Sugars (g)'])}</td>
      <td class="col-num col-hide-mobile">${fmt(bar['Sugar Alcohol (g)'])}</td>
      <td class="col-num col-hide-mobile">${fmt(bar['Cholesterol (mg)'])}</td>
      <td class="col-num col-hide-mobile">${fmt(bar['Sodium (mg)'])}</td>
      <td class="col-certs col-hide-mobile">${badgeHTML}</td>
      <td class="col-link">${linkHTML}</td>`;

    row.addEventListener('click', () => toggleExpand(bar, row));
    row.dataset.slug = barSlug(bar);
    tbody.appendChild(row);
  });

  if (bars.length > limit) {
    truncEl.classList.remove('hidden');
    truncEl.textContent = `Showing first ${limit} of ${bars.length} results. Use filters to narrow down.`;
  } else {
    truncEl.classList.add('hidden');
  }

  // Auto-expand a bar from URL ?bar=slug param (runs once on first load)
  if (window._autoExpandSlug) {
    const slug = window._autoExpandSlug;
    delete window._autoExpandSlug;
    const match = bars.find(b => barSlug(b) === slug);
    if (match) {
      const rows = tbody.querySelectorAll('tr.bar-row');
      rows.forEach(row => {
        if (row.dataset.slug === slug) {
          row.scrollIntoView({ behavior: 'smooth', block: 'center' });
          setTimeout(() => row.click(), 300);
        }
      });
    }
  }
}

function barSlug(bar) {
  return ((bar['Brand Name'] || '') + '-' + (bar['Flavor Name'] || ''))
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
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

function nf(v, unit) {
  if (v === null || v === undefined) return null;
  return `${v}${unit}`;
}

function toggleExpand(bar, row) {
  const isOpen = row.classList.contains('expanded');
  closeExpand();
  if (isOpen) return;

  row.classList.add('expanded');
  expandedRow = row;

  // Certs
  const certFull = [];
  [['Vegan','Vegan (Y/N)'],['Gluten Free','Gluten Free (Y/N)'],['Dairy Free','Dairy Free (Y/N)'],
   ['Soy Free','Soy Free (Y/N)'],['Non-GMO','Non-GMO (Y/N)'],['Nut Free','Nut Free (Y/N)'],['Kosher','Kosher (Y/N)']
  ].forEach(([label, col]) => {
    if (bar[col]?.trim().toLowerCase() === 'yes') certFull.push(label);
  });

  // ── Nutrition label sections ──────────────────────
  const primary = [
    { label: 'Calories',        value: bar['Calories'],                    unit: '',    highlight: true },
    { label: 'Protein',         value: bar['Protein (g)'],                 unit: 'g',   highlight: true },
    { label: 'Total Fat',       value: bar['Total Fat (g)'],               unit: 'g',   highlight: false },
    { label: 'Saturated Fat',   value: bar['Saturated Fat (g)'],           unit: 'g',   highlight: false },
    { label: 'Trans Fat',       value: bar['Trans Fat (g)'],               unit: 'g',   highlight: false },
    { label: 'Cholesterol',     value: bar['Cholesterol (mg)'],            unit: 'mg',  highlight: false },
    { label: 'Sodium',          value: bar['Sodium (mg)'],                 unit: 'mg',  highlight: false },
    { label: 'Total Carbs',     value: bar['Total Carbohydrates (g)'],     unit: 'g',   highlight: false },
    { label: 'Dietary Fiber',   value: bar['Dietary Fiber (g)'],           unit: 'g',   highlight: true },
    { label: 'Sugars',          value: bar['Sugars (g)'],                  unit: 'g',   highlight: true },
    { label: 'Sugar Alcohol',   value: bar['Sugar Alcohol (g)'],           unit: 'g',   highlight: true },
    { label: 'Potassium',       value: bar['Potassium (mg)'],              unit: 'mg',  highlight: false },
    { label: 'Calcium',         value: bar['Calcium (mg)'],                unit: 'mg',  highlight: false },
    { label: 'Iron',            value: bar['Iron (mg)'],                   unit: 'mg',  highlight: false },
    { label: 'Caffeine',        value: bar['Caffeine (mg)'],               unit: 'mg',  highlight: false },
  ].filter(r => r.value !== null && r.value !== undefined);

  const vitamins = [
    { label: 'Vitamin A',       value: bar['Vitamin A (% DV)'],           unit: '% DV' },
    { label: 'Vitamin C',       value: bar['Vitamin C (% DV)'],           unit: '% DV' },
    { label: 'Vitamin D',       value: bar['Vitamin D (% DV)'],           unit: '% DV' },
    { label: 'Vitamin E',       value: bar['Vitamin E (% DV)'],           unit: '% DV' },
    { label: 'Vitamin K',       value: bar['Vitamin K (% DV)'],           unit: '% DV' },
    { label: 'Thiamin (B1)',    value: bar['Thiamin / B1 (% DV)'],        unit: '% DV' },
    { label: 'Riboflavin (B2)', value: bar['Riboflavin / B2 (% DV)'],     unit: '% DV' },
    { label: 'Niacin (B3)',     value: bar['Niacin / B3 (% DV)'],         unit: '% DV' },
    { label: 'Vitamin B6',      value: bar['Vitamin B6 (% DV)'],          unit: '% DV' },
    { label: 'Vitamin B12',     value: bar['Vitamin B12 (% DV)'],         unit: '% DV' },
    { label: 'Folic Acid',      value: bar['Folic Acid (% DV)'],          unit: '% DV' },
    { label: 'Biotin',          value: bar['Biotin (% DV)'],              unit: '% DV' },
    { label: 'Pantothenic Acid',value: bar['Pantothenic Acid (% DV)'],    unit: '% DV' },
  ].filter(r => r.value !== null && r.value !== undefined);

  const minerals = [
    { label: 'Phosphorus',      value: bar['Phosphorus (% DV)'],          unit: '% DV' },
    { label: 'Iodine',          value: bar['Iodine (% DV)'],              unit: '% DV' },
    { label: 'Magnesium',       value: bar['Magnesium (% DV)'],           unit: '% DV' },
    { label: 'Zinc',            value: bar['Zinc (% DV)'],                unit: '% DV' },
    { label: 'Selenium',        value: bar['Selenium (% DV)'],            unit: '% DV' },
    { label: 'Copper',          value: bar['Copper (% DV)'],              unit: '% DV' },
    { label: 'Manganese',       value: bar['Manganese (% DV)'],           unit: '% DV' },
    { label: 'Chromium',        value: bar['Chromium (% DV)'],            unit: '% DV' },
    { label: 'Molybdenum',      value: bar['Molybdenum (% DV)'],          unit: '% DV' },
  ].filter(r => r.value !== null && r.value !== undefined);

  // ── Build HTML ────────────────────────────────────
  const sizeServing = [bar['Size'], bar['Type'], bar['Serving Size (g)'] ? bar['Serving Size (g)'] + 'g serving' : null]
    .filter(Boolean).join(' · ');

  function renderNutritionRows(items) {
    return items.map(r => `
      <div class="nutr-row${r.highlight ? ' nutr-highlight' : ''}">
        <span class="nutr-label">${r.label}</span>
        <span class="nutr-val">${r.value}${r.unit}</span>
      </div>`).join('');
  }

  function renderMicroGrid(items) {
    return items.map(r => `
      <div class="micro-item">
        <span class="micro-label">${r.label}</span>
        <span class="micro-val">${r.value}${r.unit}</span>
      </div>`).join('');
  }

  const certPills = certFull.map(c => `<span class="cert-pill">${c}</span>`).join('');

  // Title case helper
  function toTitleCase(str) {
    if (!str) return str;
    return str.replace(/\w\S*/g, txt => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
  }

  const rawIngredients = bar['Ingredients'];
  const ingrSection = rawIngredients
    ? `<div class="ingr-label">Ingredients</div><div class="ingr-text">${toTitleCase(rawIngredients)}</div>`
    : `<div class="ingr-missing">Ingredient list not available for this bar.</div>`;

  const vitMinSection = (vitamins.length > 0 || minerals.length > 0) ? `
    <div class="nutr-section-label">Vitamins &amp; Minerals</div>
    <div class="micro-grid">
      ${renderMicroGrid([...vitamins, ...minerals])}
    </div>` : '';

  // ── Score tile ──────────────────────────────────────────
  const band        = bar['score_band'];
  const bandLabel   = bar['score_band_label'];
  const score       = bar['ingredient_score'];
  const posIngr     = bar['positive_ingredients'] || '';
  const negIngr     = bar['concern_ingredients'] || '';
  const insightsRaw = bar['score_insights'] || '';

  // Parse insight chips: "Name:type|Name:type|..."
  const insightChips = insightsRaw
    ? insightsRaw.split('|').filter(Boolean).map(item => {
        const [name, type] = item.split(':');
        return { name: name.trim(), type: type ? type.trim() : 'neutral' };
      })
    : [];

  const positiveChips = insightChips.filter(c => c.type === 'positive');
  const concernChips  = insightChips.filter(c => c.type === 'concern');
  const neutralChips  = insightChips.filter(c => c.type === 'neutral');

  function renderChips(chips, cssClass) {
    return chips.map(c => `<span class="insight-chip ${cssClass}">${c.name}</span>`).join('');
  }

  const allChipsHTML = [
    renderChips(positiveChips, 'chip-positive'),
    renderChips(concernChips,  'chip-concern'),
    renderChips(neutralChips,  'chip-neutral'),
  ].join('');

  // Positives / Concerns two-column ingredient breakdown
  const posItems = posIngr ? posIngr.split(',').map(i => toTitleCase(i.trim())).filter(Boolean) : [];
  const negItems = negIngr ? negIngr.split(',').map(i => toTitleCase(i.trim())).filter(Boolean) : [];

  const positivesHTML = posItems.length ? `
    <div class="ingr-col">
      <div class="ingr-col-label ingr-col-pos">Positive Ingredients</div>
      ${posItems.map(i => `<div class="ingr-col-item">${i}</div>`).join('')}
    </div>` : '';

  const concernsHTML = negItems.length ? `
    <div class="ingr-col">
      <div class="ingr-col-label ingr-col-neg">Concern Ingredients</div>
      ${negItems.map(i => `<div class="ingr-col-item">${i}</div>`).join('')}
    </div>` : '';

  const scoreSection = band ? `
    <div class="score-tile score-band-${band}">
      <div class="score-tile-header">
        <div class="score-grade-block">
          <div class="score-header-label">Ingredient Grade</div>
          <div class="score-grade-row">
            <span class="score-band-badge">${band}</span>
            <span class="score-band-label">${bandLabel}</span>
          </div>
        </div>
        <div class="score-num-block">
          <div class="score-header-label">Ingredient Score</div>
          <div class="score-number">${score}</div>
        </div>
      </div>
      ${allChipsHTML ? `<div class="score-chips">${allChipsHTML}</div>` : ''}
      ${(positivesHTML || concernsHTML) ? `<div class="score-ingr-cols">${positivesHTML}${concernsHTML}</div>` : ''}
    </div>` : '';


  const expandRow = document.createElement('tr');
  expandRow.className = 'expand-detail';
  expandRow.innerHTML = `<td colspan="12">
    <div class="expand-content">

      <div class="expand-meta">${sizeServing}</div>

      <div class="expand-columns">

        <div class="nutr-panel">
          <div class="nutr-panel-title">Nutrition Facts</div>
          ${renderNutritionRows(primary)}
          ${vitMinSection}
        </div>

        <div class="expand-right">
          ${scoreSection}
          ${certPills ? `<div class="cert-strip">${certPills}</div>` : ''}
          ${bar['Website'] ? `<a href="${bar['Website']}" target="_blank" rel="noopener" class="visit-link">Visit product page ↗</a>` : ''}
          ${bar['Amazon Affiliate'] ? `<a href="${bar['Amazon Affiliate']}" target="_blank" rel="noopener sponsored" class="amazon-link">Buy on Amazon ↗</a>` : ''}
          <div class="ingr-block">
            ${ingrSection}
          </div>
        </div>

      </div>
    </div>
  </td>`;

  row.after(expandRow);
}

// ─── Bootstrap ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
