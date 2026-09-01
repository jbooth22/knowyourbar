/* ===================================================
   KYB Analytics — shared GA4 event tracking helper
   ===================================================
   Loaded on EVERY page (home, bar-finder, every brand page, every guide
   page). Do not duplicate this logic inline per page — add new tracked
   interactions here so every current and future page picks them up for
   free, the same way style.css is the single source of truth for styles.

   Covers, via one delegated document click listener (no per-page wiring
   needed): buy_click, explore_cta_click, explore_more_click, faq_open,
   bar_expand.

   Preset/filter/compare tracking (preset_apply, filter_change,
   bar_compare_add) is fired directly from app.js at the point those
   state changes happen, since only app.js knows that state — see the
   kybTrack() calls there. This file still needs to be loaded on
   bar-finder.html for those calls to resolve.

   All events funnel through KYB.track() so naming/params stay consistent.
   Never throws if gtag isn't present (e.g. ad blockers, local testing). */
(function () {

  function track(name, params) {
    if (typeof gtag === 'function') {
      gtag('event', name, params || {});
    }
  }

  function pageType() {
    var cls = document.body.classList;
    if (cls.contains('page-brand')) return 'brand';
    if (cls.contains('page-guide')) return 'guide';
    if (document.getElementById('results-table')) return 'finder';
    return 'home';
  }

  function pageSlug() {
    var path = window.location.pathname.replace(/^\/+/, '').replace(/\.html$/, '');
    return path === '' ? 'home' : path;
  }

  function text(el) {
    return el ? el.textContent.trim() : null;
  }

  // Brand pages set <body data-brand="..."> (see analytics.js changelog) —
  // the one reliable, page-level source of the brand name for markup on
  // those pages (like .bar-row and .bw-card) that doesn't repeat it per row.
  function pageBrand() {
    return document.body.getAttribute('data-brand') || null;
  }

  // Resolve bar_brand/bar_flavor/bar_grade for a clicked element across
  // every markup pattern on the site: the finder table, brand/guide
  // tables, the compare overlay, and the homepage top-bar cards.
  function findBarContext(el) {
    var row = el.closest('.bar-row');
    if (row) {
      return {
        bar_brand: text(row.querySelector('.bar-brand')) || pageBrand(),
        bar_flavor: text(row.querySelector('.bar-flavor')),
        bar_grade: row.dataset.grade || text(row.querySelector('.table-grade-badge')),
      };
    }
    // Buy buttons inside an expand/ingredient detail row sit one <tr>
    // after the .bar-row that has the brand/flavor text.
    var tr = el.closest('tr');
    if (tr && tr.previousElementSibling && tr.previousElementSibling.classList &&
        tr.previousElementSibling.classList.contains('bar-row')) {
      var prev = tr.previousElementSibling;
      return {
        bar_brand: text(prev.querySelector('.bar-brand')) || pageBrand(),
        bar_flavor: text(prev.querySelector('.bar-flavor')),
        bar_grade: prev.dataset.grade || text(prev.querySelector('.table-grade-badge')),
      };
    }
    var cmpCell = el.closest('.cmp-bar-header-cell');
    if (cmpCell) {
      return {
        bar_brand: text(cmpCell.querySelector('.cmp-brand')),
        bar_flavor: text(cmpCell.querySelector('.cmp-flavor')),
        bar_grade: text(cmpCell.querySelector('.cmp-grade-badge')),
      };
    }
    var card = el.closest('.top-bar-card');
    if (card) {
      return {
        bar_brand: text(card.querySelector('.top-bar-brand')),
        bar_flavor: text(card.querySelector('.top-bar-name')),
        bar_grade: text(card.querySelector('.top-bar-badge')),
      };
    }
    // "Highest / lowest ingredient quality" pick cards on brand pages
    // (.bw-card.best / .bw-card.worst). These don't carry a brand name of
    // their own since the whole page is one brand — use the page's
    // data-brand attribute.
    var bwCard = el.closest('.bw-card');
    if (bwCard) {
      return {
        bar_brand: pageBrand(),
        bar_flavor: text(bwCard.querySelector('.bw-flavor')),
        bar_grade: text(bwCard.querySelector('.grade-badge')),
      };
    }
    // "Top picks" tiles on guide pages (.pick-tile) — the compact grid at
    // the top of each guide (Best overall / Best protein-calorie ratio /
    // etc.) with its own brand+flavor labels, separate from the full
    // .bar-row table further down the page.
    var pickTile = el.closest('.pick-tile');
    if (pickTile) {
      return {
        bar_brand: text(pickTile.querySelector('.pick-tile-brand')),
        bar_flavor: text(pickTile.querySelector('.pick-tile-flavor-name')),
        bar_grade: text(pickTile.querySelector('.table-grade-badge')),
      };
    }
    return { bar_brand: null, bar_flavor: null, bar_grade: null };
  }

  // Every buy-button class in the locked BUTTONS list (BRIEFING.md /
  // style.css), plus the two live on the homepage top-bar cards
  // (.buy-amazon / .buy-site).
  var BUY_SELECTOR = [
    '.amazon-link', '.visit-link', '.cmp-buy-btn', '.cmp-site-btn',
    '.buy-amazon', '.buy-site', '.buy-btn', '.cta-amazon',
    '.bar-link-amz', '.bar-link-site', '.bar-buy-btn',
  ].join(', ');
  var AMAZON_CLASSES = [
    'amazon-link', 'cmp-buy-btn', 'buy-amazon', 'buy-btn',
    'cta-amazon', 'bar-link-amz', 'bar-buy-btn',
  ];

  function isAmazonButton(el) {
    return AMAZON_CLASSES.some(function (c) { return el.classList.contains(c); });
  }

  document.addEventListener('click', function (e) {
    var buyBtn = e.target.closest(BUY_SELECTOR);
    if (buyBtn) {
      var ctx = findBarContext(buyBtn);
      track('buy_click', {
        button_type: isAmazonButton(buyBtn) ? 'amazon' : 'brand_site',
        bar_brand: ctx.bar_brand,
        bar_flavor: ctx.bar_flavor,
        bar_grade: ctx.bar_grade,
        page_type: pageType(),
        page_slug: pageSlug(),
      });
      return;
    }

    var cta = e.target.closest(
      '.explore-cta-btn, .finder-hero-btn, .guide-finder-cta a, .site-nav-link--highlight, .site-nav-mobile-bar-finder'
    );
    if (cta) {
      track('explore_cta_click', {
        cta_label: text(cta),
        destination_href: cta.getAttribute('href'),
        source_page_type: pageType(),
        source_page_slug: pageSlug(),
      });
      return;
    }

    var moreCard = e.target.closest('.explore-more-card, .goal-card');
    if (moreCard) {
      track('explore_more_click', {
        source_page_type: pageType(),
        source_page_slug: pageSlug(),
        destination_href: moreCard.getAttribute('href'),
      });
      return;
    }

    var faqQ = e.target.closest('.faq-q');
    if (faqQ) {
      // The page's own faq-q click handler (inline, per page) toggles the
      // .open class on .faq-item synchronously before this bubbles up to
      // document, so checking the class here reflects the post-toggle
      // state — only fire on open, never on close.
      var item = faqQ.closest('.faq-item');
      if (item && item.classList.contains('open')) {
        track('faq_open', {
          page_type: pageType(),
          page_slug: pageSlug(),
          question_text: text(faqQ) ? text(faqQ).slice(0, 100) : null,
        });
      }
      return;
    }

    var barRow = e.target.closest('.bar-row');
    if (barRow) {
      // Same timing logic as faq_open: the row's own onclick (toggleIngr
      // on brand/guide pages, toggleExpand's class add on the finder)
      // already ran by the time this delegated bubble handler fires.
      var justOpened = barRow.classList.contains('open') ||
        barRow.classList.contains('row-open') ||
        barRow.classList.contains('expanded');
      if (justOpened) {
        var barCtx = findBarContext(barRow);
        track('bar_expand', {
          bar_brand: barCtx.bar_brand,
          bar_flavor: barCtx.bar_flavor,
          bar_grade: barCtx.bar_grade,
          page_type: pageType(),
          page_slug: pageSlug(),
        });
      }
    }
  });

  // Exposed for app.js (bar-finder only) to fire preset_apply,
  // filter_change, and bar_compare_add at the exact points those state
  // changes happen — see the kybTrack() calls in app.js.
  window.KYB = {
    track: track,
    pageType: pageType,
    pageSlug: pageSlug,
  };

})();
