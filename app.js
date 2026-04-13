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

const BRAND_LIST = ["88 Acres", "Afar", "Alani", "Alio", "Aloha", "Amirita", "Anabar", "Atkins", "Atlas", "B.T.R. Nation", "Barebells", "Bob's Red Mill", "Bobo's", "Built", "CLIF Bar", "Clif Builders", "Clif ZBar", "Daryl's Bars", "David", "Epic", "Equate", "FITCRUNCH", "Fiber One", "Forward", "Fulfil", "GNC Total Lean", "Gatorade", "Ghost", "GoMacro", "Gryp", "Honey Stinger", "IQ Bar", "Jacob", "Jambar", "Kize", "Laird", "Larabar", "Legendary", "Lenny & Larry's", "Lineage Provisions", "Luna", "Magic Spoon", "Melo", "Mezcla", "Mosh", "Munk Pack", "Mush", "Nature Valley", "Neoh", "Nick's", "No Cow", "No Nuts!", "NuGo", "One", "PEAK Protein", "PROBar", "Perfect Bar", "Posana", "Possible", "Power Crunch", "Prima", "Pure Protein", "Quest", "RXBAR", "Ratio", "Raw Rev", "Ready", "Redefine", "Rello", "Rise", "Send", "Simply Protein", "Skout", "Stars and Honey", "The Gluten Free Brothers", "Trubar", "Wonderslim", "Zing", "think!"];

// ─── State ───────────────────────────────────────────
let activeCerts    = {};
let sliderValues   = {};
let exclusions     = [];
let selectedBrands = new Set();
let activePreset   = null;
let activeGrades   = new Set(); // multi-select: 'A', 'B', 'C', 'D', 'F'
let expandedRow    = null;
let currentFiltered = [];
let compareSet     = new Map(); // key: "Brand|Flavor", value: bar object
let _restoringCompare = false;  // prevents serializeState from clobbering compare during restore

// ─── Macro Rank Precomputation ───────────────────────
// Computed once at load. For each macro, stores sorted arrays
// so rank lookup is O(1) during expanded row rendering.
const MACRO_RANKS = (function() {
  // Config: key = bar field, direction = 'highest'|'lowest'|'neutral'
  const MACROS = [
    { key: 'Protein (g)',           dir: 'highest' },
    { key: 'Calories',              dir: 'lowest'  },
    { key: 'Sugars (g)',            dir: 'lowest'  },
    { key: 'Dietary Fiber (g)',     dir: 'highest' },
    { key: 'Total Fat (g)',         dir: 'neutral' },
  ];

  const ranks = {};

  MACROS.forEach(({ key, dir }) => {
    // Collect all non-null values with bar references
    const vals = BARS
      .map(b => ({ val: b[key], bar: b }))
      .filter(x => x.val !== null && x.val !== undefined);

    // Sort: highest = desc, lowest = asc, neutral = desc (arbitrary, just for rank)
    vals.sort((a, b) => dir === 'lowest' ? a.val - b.val : b.val - a.val);

    // Build map: bar key → rank (1-based)
    const rankMap = {};
    vals.forEach((x, i) => {
      const barKey = x.bar['Brand Name'] + '|' + x.bar['Flavor Name'];
      // Handle ties — same value gets same rank
      if (i > 0 && x.val === vals[i-1].val) {
        const prevKey = vals[i-1].bar['Brand Name'] + '|' + vals[i-1].bar['Flavor Name'];
        rankMap[barKey] = rankMap[prevKey];
      } else {
        rankMap[barKey] = i + 1;
      }
    });

    ranks[key] = { dir, rankMap, total: vals.length };
  });

  return ranks;
})();

function getMacroRank(bar, macroKey) {
  const r = MACRO_RANKS[macroKey];
  if (!r) return null;
  const barKey = bar['Brand Name'] + '|' + bar['Flavor Name'];
  const rank = r.rankMap[barKey];
  if (!rank) return null;
  return { rank, total: r.total, dir: r.dir };
}

function getRankTagClass(rank, total, dir) {
  if (dir === 'neutral') return 'rank-gray';
  const pct = rank / total;
  // Top 25% in favorable direction = green, bottom 25% = amber, middle = gray
  if (pct <= 0.25) return 'rank-green';
  if (pct >= 0.75) return 'rank-amber';
  return 'rank-gray';
}

function renderMacroRankGrid(bar) {
  const CELLS = [
    { label: 'Protein',  key: 'Protein (g)',       unit: 'g'  },
    { label: 'Calories', key: 'Calories',           unit: ''   },
    { label: 'Sugar',    key: 'Sugars (g)',          unit: 'g'  },
    { label: 'Fiber',    key: 'Dietary Fiber (g)',   unit: 'g'  },
    { label: 'Fat',      key: 'Total Fat (g)',        unit: 'g'  },
  ];

  const cells = CELLS.map(({ label, key, unit }) => {
    const val = bar[key];
    if (val === null || val === undefined) return '';
    const r = getMacroRank(bar, key);
    let rankHtml = '';
    if (r) {
      const cls = getRankTagClass(r.rank, r.total, r.dir);
      const dirWord = r.dir === 'neutral' ? `of ${r.total}` : r.dir;
      rankHtml = `<span class="macro-rank-tag ${cls}">#${r.rank} ${dirWord}</span>`;
    }
    return `<div class="macro-rank-cell">
      <span class="macro-rank-lbl">${label}</span>
      <span class="macro-rank-val">${val}${unit}</span>
      ${rankHtml}
    </div>`;
  }).join('');

  return `<div class="macro-rank-grid">${cells}</div>`;
}

// ─── Similar Bars Precomputation ─────────────────────
// Weighted euclidean distance on normalized macros + grade proximity.
// Computed once at load. Cross-brand only, top 3 results per bar.
const SIMILAR_BARS = (function() {
  const GRADE_SCORE = { A: 4, B: 3, C: 2, D: 1, F: 0 };
  const MAX = { protein: 35, calories: 400, sugar: 30, fiber: 20, fat: 25 };
  const W   = { protein: 0.35, calories: 0.25, sugar: 0.20, fiber: 0.10, fat: 0.10 };

  function norm(b) {
    return {
      protein:  (b['Protein (g)']       || 0) / MAX.protein,
      calories: (b['Calories']           || 0) / MAX.calories,
      sugar:    (b['Sugars (g)']         || 0) / MAX.sugar,
      fiber:    (b['Dietary Fiber (g)']  || 0) / MAX.fiber,
      fat:      (b['Total Fat (g)']      || 0) / MAX.fat,
    };
  }

  function dist(a, b) {
    const na = norm(a), nb = norm(b);
    const macroDist = Math.sqrt(
      Object.keys(W).reduce((sum, k) => sum + W[k] * Math.pow(na[k] - nb[k], 2), 0)
    );
    const ga = GRADE_SCORE[a.score_band] ?? 2;
    const gb = GRADE_SCORE[b.score_band] ?? 2;
    return macroDist + Math.abs(ga - gb) * 0.06;
  }

  function whySimilar(target, candidate) {
    const tp = target['Protein (g)'] || 0;
    const cp = candidate['Protein (g)'] || 0;
    const tc = target['Calories'] || 0;
    const cc = candidate['Calories'] || 0;
    const tg = GRADE_SCORE[target.score_band] ?? 2;
    const cg = GRADE_SCORE[candidate.score_band] ?? 2;
    if (Math.abs(tp - cp) <= 2 && Math.abs(tc - cc) <= 20) return 'Closest macro match in database';
    if (cg > tg) return 'Higher ingredient grade, similar macro profile';
    if (Math.abs(tp - cp) <= 3) return 'Similar protein content and calorie range';
    return 'Comparable macro profile';
  }

  const map = {};
  const scored = BARS.filter(b => b['Protein (g)'] && b.score_band);

  scored.forEach(target => {
    const key = target['Brand Name'] + '|' + target['Flavor Name'];
    const results = [];
    scored.forEach(candidate => {
      if (candidate['Brand Name'] === target['Brand Name']) return;
      results.push({ d: dist(target, candidate), bar: candidate });
    });
    results.sort((a, b) => a.d - b.d);
    map[key] = results.slice(0, 3).map(r => ({
      bar: r.bar,
      why: whySimilar(target, r.bar),
    }));
  });

  return map;
})();

function renderSimilarBars(bar) {
  const key = bar['Brand Name'] + '|' + bar['Flavor Name'];
  const similar = SIMILAR_BARS[key];
  if (!similar || similar.length === 0) return '';

  const GRADE_COLORS = { A:'#2a7a1f', B:'#5a8a2f', C:'#b89a00', D:'#c87020', F:'#c83020' };

  const cards = similar.map(({ bar: b, why }) => {
    const color = GRADE_COLORS[b.score_band] || '#888';
    const bkey = (b['Brand Name'] + '|' + b['Flavor Name']).replace(/'/g, "\\'");
    return `<div class="sim-card" onclick="jumpToBar('${bkey}')" title="Click to expand this bar">
      <div class="sim-card-top">
        <span class="sim-brand">${b['Brand Name']}</span>
        <span class="sim-grade" style="background:${color}">${b.score_band}</span>
      </div>
      <div class="sim-flavor">${b['Flavor Name']}</div>
      <div class="sim-macros">
        <div class="sim-macro"><span class="sim-macro-val">${b['Protein (g)'] ?? '—'}g</span><span class="sim-macro-lbl">Protein</span></div>
        <div class="sim-macro"><span class="sim-macro-val">${b['Calories'] ?? '—'}</span><span class="sim-macro-lbl">Cal</span></div>
        <div class="sim-macro"><span class="sim-macro-val">${b['Sugars (g)'] ?? '—'}g</span><span class="sim-macro-lbl">Sugar</span></div>
      </div>
      <div class="sim-why">${why}</div>
    </div>`;
  }).join('');

  return `<div class="similar-section">
    <div class="similar-label">Similar bars &mdash; different brands, comparable macros</div>
    <div class="similar-cards">${cards}</div>
  </div>`;
}

function jumpToBar(barKey) {
  if (expandedRow) {
    expandedRow.remove();
    expandedRow = null;
  }
  const rows = document.querySelectorAll('tr.bar-row');
  for (const row of rows) {
    if (row.dataset.key === barKey) {
      row.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setTimeout(() => row.click(), 300);
      return;
    }
  }
  // Not in current filtered view — reset and try again
  resetAll();
  setTimeout(() => {
    const rows2 = document.querySelectorAll('tr.bar-row');
    for (const row of rows2) {
      if (row.dataset.key === barKey) {
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => row.click(), 300);
        return;
      }
    }
  }, 500);
}

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
  restoreCompareFromURL();
  document.getElementById('bar-count').textContent  = BARS.length;
  document.getElementById('footer-count').textContent = BARS.length;
  applyFilters();
  checkAdvancedState();
}

function readURLParams() {
  const params = new URLSearchParams(window.location.search);

  // grade — ?grade=A or ?grade=A,B or legacy ?band=A
  const bandParam = (params.get('grade') || params.get('band') || '');
  bandParam.split(',').map(b => b.trim().toUpperCase()).filter(b => ['A','B','C','D','F'].includes(b)).forEach(b => {
    activeGrades.add(b);
  });
  if (activeGrades.size > 0) {
    document.querySelectorAll('.grade-filter-btn').forEach(btn => {
      btn.classList.toggle('active', activeGrades.has(btn.dataset.grade));
    });
  }

  // preset — ?preset=lose_weight|clean|skip_sugar|high_protein|keto
  const preset = params.get('preset');
  if (preset && PRESETS[preset]) {
    activePreset = preset;
    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.preset === preset);
    });
  }

  // brands — ?brands=Quest,Barebells
  const brandsParam = params.get('brands');
  if (brandsParam) {
    brandsParam.split(',').map(b => b.trim()).filter(Boolean).forEach(brand => {
      selectedBrands.add(brand);
      const cb = document.querySelector(`#brand-list input[value="${CSS.escape(brand)}"]`);
      if (cb) cb.checked = true;
    });
  }

  // sliders — only non-default values serialized
  // keys: protein, cal, fat, carbs, sugar, sa, fiber, sodium
  const sliderMap = {
    protein: 'Protein (g)',
    cal:     'Calories',
    fat:     'Total Fat (g)',
    carbs:   'Total Carbohydrates (g)',
    sugar:   'Sugars (g)',
    sa:      'Sugar Alcohol (g)',
    fiber:   'Dietary Fiber (g)',
    sodium:  'Sodium (mg)',
  };
  Object.entries(sliderMap).forEach(([urlKey, stateKey]) => {
    const val = params.get(urlKey);
    if (val !== null) {
      const num = parseFloat(val);
      if (!isNaN(num)) {
        sliderValues[stateKey] = num;
        const input = document.getElementById('sl-' + stateKey);
        const display = document.getElementById('sv-' + stateKey);
        const cfg = SLIDERS_CFG.find(c => c.key === stateKey);
        if (input) input.value = num;
        if (display && cfg) display.textContent = num + cfg.unit;
      }
    }
  });

  // certs — ?certs=GF,Vegan,Kosher
  const certsParam = params.get('certs');
  if (certsParam) {
    certsParam.split(',').map(c => c.trim()).filter(Boolean).forEach(label => {
      if (activeCerts.hasOwnProperty(label)) {
        activeCerts[label] = true;
        const chip = document.getElementById('cert-' + label);
        if (chip) {
          chip.classList.add('active');
          chip.setAttribute('aria-pressed', 'true');
        }
      }
    });
  }

  // exclusions — ?excl=sucralose,palm oil
  const exclParam = params.get('excl');
  if (exclParam) {
    exclParam.split(',').map(e => e.trim()).filter(Boolean).forEach(term => {
      exclusions.push(term);
      renderExclusionTag(term);
    });
  }

  // flavor search — ?q=chocolate
  const q = params.get('q');
  if (q) {
    const input = document.getElementById('search-input');
    if (input) input.value = q;
  }

  // sort — ?sort=protein:desc
  const sort = params.get('sort');
  if (sort && sort.includes(':')) {
    const [col, dir] = sort.split(':');
    const colEl = document.getElementById('sort-col');
    const dirEl = document.getElementById('sort-dir');
    if (colEl) colEl.value = col;
    if (dirEl && ['asc','desc'].includes(dir)) dirEl.value = dir;
  }

  // ?bar=slug  — auto-expand a specific bar on load
  const barSlug = params.get('bar');
  if (barSlug) {
    window._autoExpandSlug = barSlug;
  }
}

function serializeState() {
  const params = new URLSearchParams();

  // grade
  if (activeGrades.size > 0) params.set('grade', [...activeGrades].join(','));

  // preset
  if (activePreset) params.set('preset', activePreset);

  // brands
  if (selectedBrands.size > 0) params.set('brands', [...selectedBrands].join(','));

  // sliders — only non-default values
  const sliderMap = {
    protein: 'Protein (g)',
    cal:     'Calories',
    fat:     'Total Fat (g)',
    carbs:   'Total Carbohydrates (g)',
    sugar:   'Sugars (g)',
    sa:      'Sugar Alcohol (g)',
    fiber:   'Dietary Fiber (g)',
    sodium:  'Sodium (mg)',
  };
  Object.entries(sliderMap).forEach(([urlKey, stateKey]) => {
    const cfg = SLIDERS_CFG.find(c => c.key === stateKey);
    if (cfg && sliderValues[stateKey] !== cfg.default) {
      params.set(urlKey, sliderValues[stateKey]);
    }
  });

  // certs
  const activeCertList = Object.keys(activeCerts).filter(k => activeCerts[k]);
  if (activeCertList.length > 0) params.set('certs', activeCertList.join(','));

  // exclusions
  if (exclusions.length > 0) params.set('excl', exclusions.join(','));

  // flavor search
  const q = document.getElementById('search-input')?.value?.trim();
  if (q) params.set('q', q);

  // sort — only when non-default
  const sortCol = document.getElementById('sort-col')?.value;
  const sortDir = document.getElementById('sort-dir')?.value;
  if (sortCol && sortDir && !(sortCol === 'default' && sortDir === 'desc')) {
    params.set('sort', `${sortCol}:${sortDir}`);
  }

  // preserve ?bar= if a bar is expanded
  if (window._activeBarSlug) params.set('bar', window._activeBarSlug);

  // preserve ?compare= if comparison is active — write as slugs
  if (!_restoringCompare && compareSet.size > 0) {
    const slugs = [...compareSet.values()].map(b => barSlug(b)).join(',');
    params.set('compare', slugs);
  }

  const newURL = params.toString()
    ? `${window.location.pathname}?${params.toString()}`
    : window.location.pathname;
  history.replaceState(null, '', newURL);
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
      if (activeGrades.has(band)) {
        activeGrades.delete(band);
      } else {
        activeGrades.add(band);
      }
      container.querySelectorAll('.grade-filter-btn').forEach(b => {
        b.classList.toggle('active', activeGrades.has(b.dataset.grade));
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
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = brand;
    cb.addEventListener('change', () => toggleBrand(brand, cb.checked));
    const span = document.createElement('span');
    span.textContent = brand;
    item.appendChild(cb);
    item.appendChild(span);
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
  lose_weight: {
    label: 'Lose Weight',
    emoji: '🎯',
    tagline: 'High protein, low calorie, low sugar',
    why: 'Protein keeps you full longer per calorie. We filtered to bars with at least 20g of protein under 200 calories, with no more than 3g of sugar. These are the bars that work hardest for weight management without loading you up with sweeteners or empty calories.',
    criteria: '20g+ protein &middot; under 200 cal &middot; under 3g sugar &middot; A or B ingredient grade',
    apply: (bar) => {
      const prot = bar['Protein (g)'];
      const cal  = bar['Calories'];
      const sug  = bar['Sugars (g)'];
      const band = bar['score_band'];
      if (!prot || !cal || sug === null || sug === undefined) return false;
      return prot >= 20 && cal <= 200 && sug <= 3 && (band === 'A' || band === 'B');
    },
    sort: { col: 'Protein (g)', dir: 'desc' }
  },
  clean: {
    label: 'Clean Ingredients',
    emoji: '🌿',
    tagline: 'No artificial sweeteners, no sugar alcohols',
    why: 'About 65% of protein bars contain artificial sweeteners or sugar alcohols. These bars contain neither. Every result here earns an A (Clean) ingredient grade with at least 12g of protein and no sucralose, acesulfame, aspartame, erythritol, maltitol, or xylitol anywhere in the ingredient list.',
    criteria: 'A ingredient grade &middot; 12g+ protein &middot; no artificial sweeteners &middot; no sugar alcohols',
    apply: (bar) => {
      if (bar['score_band'] !== 'A') return false;
      const prot = bar['Protein (g)'];
      if (!prot || prot < 12) return false;
      const ingr = (bar['Ingredients'] || '').toLowerCase();
      const bad = ['sucralose','acesulfame','aspartame','saccharin','erythritol','maltitol','xylitol','sorbitol','mannitol','isomalt'];
      return !bad.some(s => ingr.includes(s));
    },
    sort: { col: 'ingredient_score', dir: 'desc' }
  },
  skip_sugar: {
    label: 'Skip the Sugar',
    emoji: '🚫',
    tagline: 'Under 2g sugar, no maltitol or sorbitol',
    why: 'Low sugar does not have to mean artificial sweeteners. These bars keep natural sugar under 2g and skip the problematic sugar alcohols (maltitol and sorbitol, which have the highest glycemic impact and worst digestive side effects). A small amount of erythritol is allowed but kept under 4g.',
    criteria: 'Under 2g sugar &middot; under 4g sugar alcohol &middot; no maltitol or sorbitol &middot; A or B grade',
    apply: (bar) => {
      const sug  = bar['Sugars (g)'];
      const sa   = bar['Sugar Alcohol (g)'];
      const band = bar['score_band'];
      if (sug === null || sug === undefined || sa === null || sa === undefined) return false;
      if (sug > 2 || sa > 4) return false;
      if (band !== 'A' && band !== 'B') return false;
      const ingr = (bar['Ingredients'] || '').toLowerCase();
      return !['maltitol','sorbitol'].some(s => ingr.includes(s));
    },
    sort: { col: 'Sugars (g)', dir: 'asc' }
  },
  high_protein: {
    label: 'Most Protein Per Calorie',
    emoji: '💪',
    tagline: 'Highest protein efficiency — most protein for your calorie budget',
    why: 'Raw protein grams can be misleading. A bar with 30g protein at 400 calories is less efficient than one with 22g at 180 calories. This filter ranks by protein efficiency: grams of protein divided by total calories. Every result here has at least 15g protein and earns A, B, or C on ingredient quality.',
    criteria: 'Protein efficiency ranked &middot; 15g+ protein &middot; A, B, or C ingredient grade',
    apply: (bar) => {
      const prot = bar['Protein (g)'];
      const cal  = bar['Calories'];
      const band = bar['score_band'];
      if (!prot || !cal) return false;
      const eff = (prot * 4) / cal;
      return prot >= 15 && eff >= 0.45 && (band === 'A' || band === 'B' || band === 'C');
    },
    sort: { col: 'efficiency', dir: 'desc' }
  },
  keto: {
    label: 'Keto Friendly',
    emoji: '⚡',
    tagline: 'Under 5 net carbs, higher fat',
    why: 'Net carbs = total carbs minus fiber minus sugar alcohols. These bars keep net carbs under 5g and have at least 10g of fat, fitting a ketogenic macro profile. All results earn A or B on ingredient quality so you are not just getting a list of maltitol-heavy options.',
    criteria: 'Under 5g net carbs &middot; 10g+ fat &middot; A or B ingredient grade',
    apply: (bar) => {
      const carb = bar['Total Carbohydrates (g)'];
      const fib  = bar['Dietary Fiber (g)'] || 0;
      const sa   = bar['Sugar Alcohol (g)'] || 0;
      const fat  = bar['Total Fat (g)'];
      const band = bar['score_band'];
      if (!carb || !fat) return false;
      const netCarbs = carb - fib - sa;
      return netCarbs <= 5 && fat >= 10 && (band === 'A' || band === 'B');
    },
    sort: { col: 'Total Fat (g)', dir: 'desc' }
  }
};

function applyPreset(presetKey) {
  const btn = document.querySelector(`[data-preset="${presetKey}"]`);
  if (activePreset === presetKey) {
    activePreset = null;
    btn.classList.remove('active');
    // On mobile: re-show filter panel when preset is cleared
    if (window.innerWidth <= 900) {
      const panel = document.getElementById('filter-panel');
      if (panel) panel.classList.remove('panel-collapsed');
    }
  } else {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
    activePreset = presetKey;
    btn.classList.add('active');
    // On mobile: collapse filter panel so user sees results immediately
    if (window.innerWidth <= 900) {
      const panel = document.getElementById('filter-panel');
      if (panel) panel.classList.add('panel-collapsed');
      // Scroll to results
      setTimeout(() => {
        const results = document.getElementById('results-table');
        if (results) results.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }
  applyFilters();
}

function updatePresetBanner(filteredCount) {
  const banner = document.getElementById('preset-banner');
  const resultsPanel = document.querySelector('.results-panel');
  if (!banner) return;
  if (!activePreset) {
    banner.classList.add('hidden');
    banner.innerHTML = '';
    if (resultsPanel) resultsPanel.classList.remove('preset-active-mobile');
    return;
  }
  const preset = PRESETS[activePreset];
  banner.classList.remove('hidden');
  banner.innerHTML = `
    <div class="banner-inner">
      <div class="banner-top">
        <span class="banner-emoji">${preset.emoji}</span>
        <span class="banner-label">${preset.label}</span>
        <span class="banner-count">${filteredCount} bar${filteredCount !== 1 ? 's' : ''} match</span>
        <button class="banner-clear" onclick="resetAll()" aria-label="Clear filter">Clear</button>
      </div>
      <div class="banner-why">${preset.why}</div>
      <div class="banner-criteria">${preset.criteria}</div>
    </div>
  `;
  if (resultsPanel) resultsPanel.classList.add('preset-active-mobile');
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

function renderExclusionTag(term) {
  const div = document.getElementById('excl-tags');
  if (!div) return;
  const tag = document.createElement('span');
  tag.className = 'excl-tag';
  tag.innerHTML = `${term} <button aria-label="Remove ${term}" onclick="removeExclusion('${term}')">×</button>`;
  div.appendChild(tag);
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
  // On mobile: restore filter panel when resetting
  const panel = document.getElementById('filter-panel');
  if (panel) panel.classList.remove('panel-collapsed');
  // Close advanced filters on reset
  const advPanel = document.getElementById('panel-advanced');
  const advToggle = document.getElementById('advanced-toggle');
  if (advPanel) advPanel.classList.remove('open');
  if (advToggle) advToggle.classList.remove('open');
  const label = document.getElementById('refine-toggle-label');
  if (label) label.textContent = 'Refine filters';
  activeGrades.clear();
  document.querySelectorAll('.grade-filter-btn').forEach(b => b.classList.remove('active'));
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
  clearCompare();
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
    if (activeGrades.size > 0 && !activeGrades.has(bar['score_band'])) return false;

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

  // Sync URL state
  serializeState();
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

    const band = bar['score_band'];
    const gradeHTML = band
      ? `<span class="table-grade-badge grade-${band}" title="${bar['score_band_label'] || ''}">${band}</span>`
      : '';

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
      <td class="col-grade">${gradeHTML}</td>
      <td class="col-compare">
        <button class="compare-cb${compareSet.has(bar['Brand Name'] + '|' + bar['Flavor Name']) ? ' active' : ''}"
          data-barkey="${bar['Brand Name']}|${bar['Flavor Name']}"
          title="Add to comparison">+</button>
      </td>`;

    row.addEventListener('click', () => toggleExpand(bar, row));
    row.dataset.slug = barSlug(bar);
    row.dataset.key  = bar['Brand Name'] + '|' + bar['Flavor Name'];
    row.classList.add('bar-row');
    tbody.appendChild(row);

    // Compare button — use direct closure over bar, stop propagation from row click
    const compareBtn = row.querySelector('.compare-cb');
    if (compareBtn) {
      compareBtn.addEventListener('click', e => {
        e.stopPropagation();
        toggleCompare(bar);
      });
    }
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

function toTitleCase(str) {
  if (!str) return str;
  return str.replace(/\w\S*/g, txt => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
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
  window._activeBarSlug = null;
  serializeState();
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
  window._activeBarSlug = barSlug(bar);
  serializeState();

  // Certs
  const certFull = [];
  [['Vegan','Vegan (Y/N)'],['Gluten Free','Gluten Free (Y/N)'],['Dairy Free','Dairy Free (Y/N)'],
   ['Soy Free','Soy Free (Y/N)'],['Non-GMO','Non-GMO (Y/N)'],['Nut Free','Nut Free (Y/N)'],['Kosher','Kosher (Y/N)']
  ].forEach(([label, col]) => {
    if (bar[col]?.trim().toLowerCase() === 'yes') certFull.push(label);
  });

  // ── Nutrition label sections ──────────────────────
  const primary = [
    { label: 'Calories',        value: bar['Calories'],                    unit: '',    highlight: false },
    { label: 'Protein',         value: bar['Protein (g)'],                 unit: 'g',   highlight: false },
    { label: 'Total Fat',       value: bar['Total Fat (g)'],               unit: 'g',   highlight: false },
    { label: 'Saturated Fat',   value: bar['Saturated Fat (g)'],           unit: 'g',   highlight: false },
    { label: 'Trans Fat',       value: bar['Trans Fat (g)'],               unit: 'g',   highlight: false },
    { label: 'Cholesterol',     value: bar['Cholesterol (mg)'],            unit: 'mg',  highlight: false },
    { label: 'Sodium',          value: bar['Sodium (mg)'],                 unit: 'mg',  highlight: false },
    { label: 'Total Carbs',     value: bar['Total Carbohydrates (g)'],     unit: 'g',   highlight: false },
    { label: 'Dietary Fiber',   value: bar['Dietary Fiber (g)'],           unit: 'g',   highlight: false },
    { label: 'Sugars',          value: bar['Sugars (g)'],                  unit: 'g',   highlight: false },
    { label: 'Sugar Alcohol',   value: bar['Sugar Alcohol (g)'],           unit: 'g',   highlight: false },
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
      <div class="nutr-row">
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

  // Parse insight chips: "Name:type:severity|..." (severity optional)
  let insightChips = insightsRaw
    ? insightsRaw.split('|').filter(Boolean).map(item => {
        const parts = item.split(':');
        return {
          name:     parts[0] ? parts[0].trim() : '',
          type:     parts[1] ? parts[1].trim() : 'neutral',
          severity: parts[2] ? parts[2].trim() : ''
        };
      }).filter(c => c.name && c.name !== 'Sugar Alcohol Early')
    : [];

  // Fallback: derive basic chips from ingredient text if score_insights is empty
  // (schema-scored bars don't have pre-generated insights)
  if (insightChips.length === 0 && bar['Ingredients']) {
    const ingr = (bar['Ingredients'] || '').toLowerCase();
    const ARTIFICIAL = ['sucralose','acesulfame','aspartame','saccharin'];
    const SA_KW      = ['erythritol','maltitol','xylitol','sorbitol','mannitol','isomalt','lactitol'];
    const OIL_KW     = ['palm kernel oil','palm oil','canola oil','soybean oil','hydrogenated'];
    if (ARTIFICIAL.some(k => ingr.includes(k))) {
      insightChips.push({ name: 'Artificial Sweeteners', type: 'concern', severity: 'elevated' });
    }
    if (SA_KW.some(k => ingr.includes(k))) {
      const saPos = Math.min(...SA_KW.filter(k => ingr.includes(k)).map(k => ingr.indexOf(k)));
      const elevated = saPos < ingr.indexOf(',', ingr.indexOf(',') + 1); // in first 2 ingredients roughly
      insightChips.push({ name: 'Sugar Alcohols', type: 'concern', severity: elevated ? 'elevated' : 'minor' });
    }
    if (OIL_KW.some(k => ingr.includes(k) && !ingr.includes('high oleic'))) {
      insightChips.push({ name: 'Processed Oils', type: 'concern', severity: 'minor' });
    }
    // Positive signals from positive_ingredients field
    const posIngr = (bar['positive_ingredients'] || '').toLowerCase();
    if (posIngr.includes('protein') || posIngr.includes('whey') || posIngr.includes('egg white')) {
      insightChips.push({ name: 'Quality Protein Source', type: 'positive', severity: '' });
    }
    if (bar['score_band'] === 'A' && !ARTIFICIAL.some(k => ingr.includes(k)) && !SA_KW.some(k => ingr.includes(k))) {
      insightChips.push({ name: 'Clean Ingredients', type: 'positive', severity: '' });
    }
  }

  const positiveChips = insightChips.filter(c => c.type === 'positive');
  const concernChips  = insightChips.filter(c => c.type === 'concern');
  const neutralChips  = insightChips.filter(c => c.type === 'neutral');

  function renderChips(chips, cssClass) {
    return chips.map(c => {
      const sevClass = (c.type === 'concern' && c.severity === 'elevated') ? ' chip-elevated' : '';
      return `<span class="insight-chip ${cssClass}${sevClass}">${c.name}</span>`;
    }).join('');
  }

  const allChipsHTML = [
    renderChips(positiveChips, 'chip-positive'),
    renderChips(concernChips,  'chip-concern'),
    renderChips(neutralChips,  'chip-neutral'),
  ].join('');

  // +/- score breakdown bar
  const scorePos = bar['score_pos'];
  const scoreNeg = bar['score_neg'];
  const scorePosNegHTML = (scorePos != null && scoreNeg != null) ? (() => {
    const absPos = Math.abs(scorePos);
    const absNeg = Math.abs(scoreNeg);
    const total  = absPos + absNeg;
    const posPct = total > 0 ? Math.round(absPos / total * 100) : 50;
    const negPct = 100 - posPct;
    return `
    <div class="score-breakdown">
      <div class="score-breakdown-bar">
        <div class="sbd-pos" style="width:${posPct}%" title="Positive contributions: +${scorePos}"></div>
        <div class="sbd-neg" style="width:${negPct}%" title="Concern contributions: ${scoreNeg}"></div>
      </div>
      <div class="score-breakdown-labels">
        <span class="sbd-label-pos">+${scorePos} positive</span>
        <span class="sbd-label-neg">${scoreNeg} concerns</span>
      </div>
    </div>`;
  })() : '';

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
          <div class="score-header-label">Ingredient Quality Grade</div>
          <div class="score-grade-row">
            <span class="score-band-badge">${band}</span>
            <span class="score-band-label">${bandLabel}</span>
          </div>
        </div>
        <div class="score-num-block">
          <div class="score-header-label">Ingredient Quality Score</div>
          <div class="score-number">${score}</div>
        </div>
      </div>
      ${scorePosNegHTML}
      ${allChipsHTML ? `<div class="score-chips">${allChipsHTML}</div>` : ''}
      ${(positivesHTML || concernsHTML) ? `<div class="score-ingr-cols">${positivesHTML}${concernsHTML}</div>` : ''}
    </div>` : '';


  const expandRow = document.createElement('tr');
  expandRow.className = 'expand-detail';
  expandRow.innerHTML = `<td colspan="13">
    <div class="expand-content">

      <div class="expand-meta">${sizeServing}</div>

      ${renderMacroRankGrid(bar)}

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
          <button class="expand-compare-btn${compareSet.has(bar['Brand Name'] + '|' + bar['Flavor Name']) ? ' active' : ''}"
            data-barkey="${bar['Brand Name']}|${bar['Flavor Name']}">
            ${compareSet.has(bar['Brand Name'] + '|' + bar['Flavor Name']) ? '✓ In comparison' : '+ Add to comparison'}
          </button>
          <div class="ingr-block">
            ${ingrSection}
          </div>
        </div>

      </div>

      ${renderSimilarBars(bar)}

    </div>
  </td>`;

  row.after(expandRow);

  // Expand row compare button — direct closure over bar
  const expandCompareBtn = expandRow.querySelector('.expand-compare-btn');
  if (expandCompareBtn) {
    expandCompareBtn.addEventListener('click', e => {
      e.stopPropagation();
      toggleCompare(bar);
    });
  }
}

// ─── Bootstrap ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);

// ─── Comparison Feature ─────────────────────────────
// compareSet declared in State block at top of file

function toggleCompare(bar) {
  const key = bar['Brand Name'] + '|' + bar['Flavor Name'];
  if (compareSet.has(key)) {
    compareSet.delete(key);
  } else {
    if (compareSet.size >= 4) {
      showCompareLimitToast();
      return;
    }
    compareSet.set(key, bar);
  }
  updateAllCompareButtons();
  updateCompareTray();
  serializeState();
}

function toggleFilterPanel() {
  const panel = document.getElementById('filter-panel');
  const label = document.getElementById('refine-toggle-label');
  if (!panel) return;
  const isCollapsed = panel.classList.contains('panel-collapsed');
  panel.classList.toggle('panel-collapsed', !isCollapsed);
  if (label) label.textContent = isCollapsed ? 'Hide filters' : 'Refine filters';
}

function updateAllCompareButtons() {
  document.querySelectorAll('[data-barkey]').forEach(btn => {
    const key = btn.dataset.barkey;
    const active = compareSet.has(key);
    btn.classList.toggle('active', active);
    if (btn.classList.contains('expand-compare-btn')) {
      btn.textContent = active ? '✓ In comparison' : '+ Add to comparison';
    }
  });
}

function updateCompareTray() {
  let tray = document.getElementById('compare-tray');
  if (compareSet.size === 0) {
    if (tray) tray.remove();
    document.body.style.paddingBottom = '';
    return;
  }
  if (!tray) {
    tray = document.createElement('div');
    tray.id = 'compare-tray';
    document.body.appendChild(tray);
  }
  const items = [...compareSet.values()];
  tray.innerHTML = `
    <div class="tray-inner">
      <div class="tray-label">Comparing <span class="tray-count">${items.length}/4</span></div>
      <div class="tray-bars">
        ${items.map(b => `<div class="tray-bar">
          <span class="tray-bar-name">${b['Brand Name']} ${b['Flavor Name']}</span>
          <button class="tray-remove" data-key="${b['Brand Name']}|${b['Flavor Name']}">×</button>
        </div>`).join('')}
      </div>
      <div class="tray-actions">
        <button class="tray-clear">Clear</button>
        <button class="tray-compare${items.length < 2 ? ' disabled' : ''}"${items.length < 2 ? ' disabled' : ''}>
          ${items.length >= 2 ? 'Compare ' + items.length + ' bars' : 'Need 2+ bars'}
        </button>
      </div>
    </div>`;

  tray.querySelectorAll('.tray-remove').forEach(btn => {
    btn.addEventListener('click', () => {
      compareSet.delete(btn.dataset.key);
      updateAllCompareButtons();
      updateCompareTray();
      serializeState();
    });
  });
  tray.querySelector('.tray-clear').addEventListener('click', clearCompare);
  tray.querySelector('.tray-compare').addEventListener('click', () => {
    if (compareSet.size >= 2) openCompareOverlay();
  });

  requestAnimationFrame(() => {
    if (tray) document.body.style.paddingBottom = tray.offsetHeight + 'px';
  });
}

function clearCompare() {
  compareSet.clear();
  updateAllCompareButtons();
  updateCompareTray();
  serializeState();
}

function showCompareLimitToast() {
  let t = document.getElementById('compare-toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'compare-toast';
    t.textContent = 'Max 4 bars in comparison';
    document.body.appendChild(t);
  }
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}

// ─── Comparison Overlay ──────────────────────────────
function openCompareOverlay() {
  const bars = [...compareSet.values()];
  if (bars.length < 2) return;

  const slugs = bars.map(b => barSlug(b)).join(',');
  const url = new URL(window.location.href);
  url.searchParams.set('compare', slugs);
  history.replaceState(null, '', url.toString());

  const BAND_COLORS = { A:'#2a7a1f', B:'#5a8a2f', C:'#b89a00', D:'#c87020', F:'#c83020' };
  const BAND_LABELS = { A:'Clean', B:'Good', C:'Okay', D:'Poor', F:'Avoid' };
  const colCount = bars.length;

  // Calculate column width — tighter on mobile
  const labelW = window.innerWidth <= 700 ? 72 : 100;
  const padding = window.innerWidth <= 700 ? 0 : 24;
  const availW = Math.min(window.innerWidth - padding, 1000) - labelW;
  const minBarW = window.innerWidth <= 700 ? 120 : 160;
  const barColW = Math.max(minBarW, Math.floor(availW / colCount));

  const colgroup = `<colgroup>
    <col style="width:${labelW}px">
    ${bars.map(() => `<col style="width:${barColW}px">`).join('')}
  </colgroup>`;

  const MACRO_ROWS = [
    { key:'Calories',                label:'Calories',      unit:'',   better:'lower'  },
    { key:'Protein (g)',             label:'Protein',       unit:'g',  better:'higher' },
    { key:'Total Fat (g)',           label:'Fat',           unit:'g',  better:null     },
    { key:'Total Carbohydrates (g)', label:'Carbs',         unit:'g',  better:'lower'  },
    { key:'Dietary Fiber (g)',       label:'Fiber',         unit:'g',  better:'higher' },
    { key:'Sugars (g)',              label:'Sugars',        unit:'g',  better:'lower'  },
    { key:'Sugar Alcohol (g)',       label:'Sugar Alcohol', unit:'g',  better:null     },
    { key:'Sodium (mg)',             label:'Sodium',        unit:'mg', better:null     },
  ];

  function getBest(key, better) {
    if (!better) return null;
    const vals = bars.map(b => b[key]).filter(v => v != null);
    if (vals.length < 2) return null;
    const best = better === 'higher' ? Math.max(...vals) : Math.min(...vals);
    return vals.filter(v => v === best).length < bars.length ? best : null;
  }

  // Bar header cells (thead row)
  const barHeaderCells = bars.map(b => {
    const band = b['score_band'];
    const color = BAND_COLORS[band] || '#888';
    const aff = b['Amazon Affiliate'];
    const buy = aff && String(aff).startsWith('http')
      ? `<a href="${aff}" target="_blank" rel="noopener sponsored" class="cmp-buy-btn">Buy on Amazon</a>`
      : `<span class="cmp-buy-btn cmp-buy-placeholder">&nbsp;</span>`;
    const site = b['Website']
      ? `<a href="${b['Website']}" target="_blank" rel="noopener" class="cmp-site-btn">Product page</a>` : '';
    return `<th class="cmp-bar-header-cell">
      <div class="cmp-bar-card-inner">
        <div class="cmp-brand">${b['Brand Name']}</div>
        <div class="cmp-flavor">${b['Flavor Name']}</div>
        <div class="cmp-grade-row">
          <span class="cmp-grade-badge" style="background:${color}">${band || '?'}</span>
          <span class="cmp-grade-label">${BAND_LABELS[band] || ''} &middot; ${b['ingredient_score'] ?? '&mdash;'}</span>
        </div>
        <div class="cmp-btns">${site}${buy}</div>
      </div>
    </th>`;
  }).join('');

  // Cert rows first (compact, easy to scan)
  const CERT_COLS = [
    ['Vegan','Vegan (Y/N)'],['GF','Gluten Free (Y/N)'],['Dairy Free','Dairy Free (Y/N)'],
    ['Soy Free','Soy Free (Y/N)'],['Non-GMO','Non-GMO (Y/N)'],['Nut Free','Nut Free (Y/N)'],['Kosher','Kosher (Y/N)'],
  ];
  const certRows = CERT_COLS.map(([label, col]) => {
    const cells = bars.map(b => {
      const yes = b[col]?.trim().toLowerCase() === 'yes';
      return `<td class="cmp-cell cmp-cert-cell">${yes ? '<span class="cmp-yes">&#10003;</span>' : '<span class="cmp-no">&ndash;</span>'}</td>`;
    }).join('');
    return `<tr><td class="cmp-row-label">${label}</td>${cells}</tr>`;
  }).join('');

  // Macro rows
  const macroRows = MACRO_ROWS.map(({key, label, unit, better}) => {
    const best = getBest(key, better);
    const cells = bars.map(b => {
      const v = b[key];
      return `<td class="cmp-cell${best != null && v === best ? ' cmp-best' : ''}">${v != null ? v + unit : '&mdash;'}</td>`;
    }).join('');
    return `<tr><td class="cmp-row-label">${label}</td>${cells}</tr>`;
  }).join('');

  // Insight chips
  const chipCells = bars.map(b => {
    const raw = b['score_insights'] || '';
    const chips = raw.split('|').filter(Boolean).map(item => {
      const p = item.split(':');
      const name = p[0]?.trim(), type = p[1]?.trim(), sev = p[2]?.trim();
      if (!name || name === 'Sugar Alcohol Early') return '';
      if (type === 'positive') return `<span class="insight-chip chip-positive">${name}</span>`;
      if (type === 'concern')  return `<span class="insight-chip chip-concern${sev === 'elevated' ? ' chip-elevated' : ''}">${name}</span>`;
      return `<span class="insight-chip chip-neutral">${name}</span>`;
    }).join('');
    return `<td class="cmp-cell cmp-chips-cell">${chips || '&mdash;'}</td>`;
  }).join('');

  // Ingredient breakdown
  const ingrCells = bars.map(b => {
    const pos = (b['positive_ingredients'] || '').split(',').map(s => s.trim()).filter(Boolean);
    const neg = (b['concern_ingredients']  || '').split(',').map(s => s.trim()).filter(Boolean);
    const posHTML = pos.length ? `<div class="cmp-ingr-section"><div class="cmp-ingr-label pos">Positives</div>${pos.map(i => `<div class="cmp-ingr-item">${toTitleCase(i)}</div>`).join('')}</div>` : '';
    const negHTML = neg.length ? `<div class="cmp-ingr-section"><div class="cmp-ingr-label neg">Concerns</div>${neg.map(i => `<div class="cmp-ingr-item">${toTitleCase(i)}</div>`).join('')}</div>` : '';
    const full = b['Ingredients'] ? `<div class="cmp-ingr-full">${toTitleCase(b['Ingredients'])}</div>` : '';
    return `<td class="cmp-cell cmp-ingr-cell">${posHTML}${negHTML}${full || '<em style="color:#ccc">Not available</em>'}</td>`;
  }).join('');

  const overlay = document.createElement('div');
  overlay.id = 'compare-overlay';
  overlay.innerHTML = `
    <div class="cmp-overlay-inner">
      <div class="cmp-header">
        <div class="cmp-title">Comparing ${bars.length} bars</div>
        <div class="cmp-header-actions">
          <button class="cmp-share-btn" id="cmp-share-btn">&#9015; Copy link</button>
          <button class="cmp-close-btn" id="cmp-close-btn">&#10005; Close</button>
        </div>
      </div>
      <div class="cmp-scroll">
        <table class="cmp-table">
          ${colgroup}
          <thead>
            <tr>
              <th class="cmp-row-label" style="background:var(--off-white);border-bottom:2px solid var(--border)"></th>
              ${barHeaderCells}
            </tr>
          </thead>
          <tbody>
            <tr class="cmp-section-header"><td colspan="${colCount+1}">Certifications</td></tr>
            ${certRows}
            <tr class="cmp-section-header"><td colspan="${colCount+1}">Macros</td></tr>
            ${macroRows}
            <tr class="cmp-section-header"><td colspan="${colCount+1}">Ingredient Quality</td></tr>
            <tr><td class="cmp-row-label">Insights</td>${chipCells}</tr>
            <tr class="cmp-section-header"><td colspan="${colCount+1}">Ingredients</td></tr>
            <tr><td class="cmp-row-label">Breakdown</td>${ingrCells}</tr>
          </tbody>
        </table>
      </div>
    </div>`;

  document.body.appendChild(overlay);
  document.body.classList.add('overlay-open');
  document.getElementById('cmp-close-btn').addEventListener('click', closeCompareOverlay);
  document.getElementById('cmp-share-btn').addEventListener('click', copyCompareLink);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeCompareOverlay(); });
}

function closeCompareOverlay() {
  const overlay = document.getElementById('compare-overlay');
  if (overlay) overlay.remove();
  document.body.classList.remove('overlay-open');
  const url = new URL(window.location.href);
  url.searchParams.delete('compare');
  history.replaceState(null, '', url.toString());
}

function copyCompareLink() {
  const slugs = [...compareSet.values()].map(b => barSlug(b)).join(',');
  const url = new URL(window.location.href);
  url.searchParams.set('compare', slugs);
  navigator.clipboard.writeText(url.toString()).then(() => {
    const btn = document.getElementById('cmp-share-btn');
    if (btn) { btn.textContent = '✓ Copied!'; setTimeout(() => btn.textContent = '⎘ Copy link', 2000); }
  });
}

function restoreCompareFromURL() {
  const params = new URLSearchParams(window.location.search);
  const compareParam = params.get('compare');
  if (!compareParam) return;

  _restoringCompare = true;

  const slugs = compareParam.split(',').map(s => s.trim()).filter(Boolean);
  slugs.forEach(slug => {
    const bar = BARS.find(b => barSlug(b) === slug);
    if (bar && compareSet.size < 4) {
      const key = bar['Brand Name'] + '|' + bar['Flavor Name'];
      compareSet.set(key, bar);
    }
  });

  if (compareSet.size > 0) {
    updateAllCompareButtons();
    updateCompareTray();
    if (compareSet.size >= 2) {
      setTimeout(() => {
        openCompareOverlay();
        _restoringCompare = false;
      }, 400);
    } else {
      _restoringCompare = false;
    }
  } else {
    _restoringCompare = false;
  }
}

// ─── Mobile Nav Toggle ───────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  const toggle = document.getElementById('nav-toggle');
  const links  = document.querySelector('.site-nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function() {
      links.classList.toggle('open');
    });
    // Close on outside click
    document.addEventListener('click', function(e) {
      if (!e.target.closest('.site-nav')) {
        links.classList.remove('open');
      }
    });
  }
});

// ─── Advanced Filter Toggle ──────────────────────
function toggleAdvanced() {
  const panel  = document.getElementById('panel-advanced');
  const toggle = document.getElementById('advanced-toggle');
  const icon   = document.getElementById('advanced-icon');
  if (!panel) return;
  const isOpen = panel.classList.contains('open');
  panel.classList.toggle('open', !isOpen);
  toggle.classList.toggle('open', !isOpen);
  if (icon) icon.textContent = isOpen ? '+' : '+';
}

// Auto-open advanced if any advanced filter is active (on page load from URL state)
function checkAdvancedState() {
  const hasSliders = Object.values(sliderValues).some((v, i) => {
    const cfg = SLIDER_CONFIG[i];
    return cfg && v !== cfg.default;
  });
  const hasCerts   = selectedCerts.size > 0;
  const hasExcl    = exclusions.length > 0;
  if (hasSliders || hasCerts || hasExcl) {
    const panel  = document.getElementById('panel-advanced');
    const toggle = document.getElementById('advanced-toggle');
    if (panel)  panel.classList.add('open');
    if (toggle) toggle.classList.add('open');
  }
}
