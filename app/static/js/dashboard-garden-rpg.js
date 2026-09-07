/**
 * Dashboard Garden RPG — region interactions, mission toggles with
 * feedback loop, petal toggles, XP chart, day/night, judge actions.
 */
document.addEventListener('DOMContentLoaded', function () {

  // ── Region Interaction ──
  function triggerRegionPulse(regionKey) {
    var wrapper = document.querySelector('[data-region="' + regionKey + '"]');
    if (!wrapper) return;
    wrapper.classList.add('grpg-region-pulse');
    setTimeout(function () {
      wrapper.classList.remove('grpg-region-pulse');
    }, 2000);
  }

  function closeAllRegionPanels() {
    document.querySelectorAll('.grpg-region-expanded').forEach(function (panel) {
      panel.hidden = true;
    });
    document.querySelectorAll('.grpg-region-art-wrapper').forEach(function (w) {
      w.classList.remove('grpg-region-selected');
      w.setAttribute('aria-expanded', 'false');
    });
  }

  document.querySelectorAll('.grpg-region-art-wrapper').forEach(function (wrapper) {
    function toggleExpanded() {
      var panel = wrapper.querySelector('.grpg-region-expanded');
      var isOpen = !panel.hidden;
      closeAllRegionPanels();
      if (!isOpen) {
        panel.hidden = false;
        wrapper.classList.add('grpg-region-selected');
        wrapper.setAttribute('aria-expanded', 'true');
      }
    }

    wrapper.addEventListener('click', toggleExpanded);
    wrapper.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleExpanded();
      }
    });
  });

  // ── Mission Toggles + expandable rows (H3) ──
  document.querySelectorAll('.grpg-mission-status').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var row = this.closest('.grpg-mission-row');
      var isDone = row.getAttribute('data-done') === 'true';
      row.setAttribute('data-done', isDone ? 'false' : 'true');
      this.setAttribute('aria-pressed', isDone ? 'false' : 'true');

      var meta = row.querySelector('.grpg-mission-meta');
      var xp = parseInt(this.getAttribute('data-xp')) || 0;

      if (!isDone) {
        meta.innerHTML = '<span class="grpg-done-label">\u2713 DONE</span>';
        updateTopbarXP(xp);

        // Feedback loop: identify target region and attrs from the row
        var region = row.getAttribute('data-target-region');
        var attrs = row.getAttribute('data-attr-deltas') || '';
        if (region) {
          meta.insertAdjacentHTML('beforeend',
            '<span class="grpg-inline-feedback">' + attrs + ' <span class="grpg-feedback-arrow">\u2192</span> ' + regionLabel(region) + '</span>');
          triggerRegionPulse(region);
        }
      } else {
        meta.textContent = row.getAttribute('data-time-range') || '';
        updateTopbarXP(-xp);
      }
    });
  });

  // Toggle expanded mission detail when the row (not the status button) is clicked
  document.querySelectorAll('.grpg-mission-row').forEach(function (row) {
    row.addEventListener('click', function (e) {
      if (e.target.closest('button')) return; // let button handlers deal with their own actions
      row.classList.toggle('grpg-mission-expanded-open');
    });
  });

  // Mission action buttons (START/RESCHEDULE/ABANDON) — demo interactions
  document.querySelectorAll('.grpg-mission-action').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var action = btn.getAttribute('data-action');
      var row = btn.closest('.grpg-mission-row') ||
           (btn.closest('.grpg-current-objective') ? null : null);
      if (action === 'abandon' && row) {
        row.setAttribute('data-status', 'ABANDONED');
        row.setAttribute('data-done', 'false');
        var meta = row.querySelector('.grpg-mission-meta');
        if (meta) meta.innerHTML = '<span class="grpg-done-label" style="color:var(--accent-danger);opacity:0.6;">\u2716 ABANDONED</span>';
        row.classList.remove('grpg-mission-expanded-open');
      }
    });
  });

  // ── Petal Toggles ──
  document.querySelectorAll('.grpg-check-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var row = this.closest('.grpg-check-row');
      var isDone = row.getAttribute('data-done') === 'true';
      row.setAttribute('data-done', isDone ? 'false' : 'true');
      this.setAttribute('aria-pressed', isDone ? 'false' : 'true');
    });
  });

  // ── XP Chart (Canvas 2D) — fixed axis 0/800/1.6k/2.4k, Mon–Sun, animate-in ──
  function drawXpChart(animate) {
    var canvas = document.getElementById('grpg-xp-chart');
    if (!canvas) return;

    var dataEl = document.getElementById('grpg-xp-data');
    var data;
    try {
      data = JSON.parse(dataEl.textContent);
    } catch (e) {
      data = [0, 0, 0, 0, 0, 0, 0];
    }
    data = (data || []).slice(0, 7);
    while (data.length < 7) data.push(0);

    var MAX_XP = 2400;
    var ticks = [0, 800, 1600, 2400];
    var fmtTick = function (v) {
      return v >= 1000 ? (v / 1000) + 'k' : String(v);
    };

    var ctx = canvas.getContext('2d');
    var dpr = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(10, Math.round(rect.width * dpr));
    canvas.height = Math.max(10, Math.round(rect.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var w = rect.width;
    var h = rect.height;
    var gutter = Math.max(24, Math.min(34, w / 16)); // left room for y-tick labels
    var plotTop = 4;
    var plotBottom = h - 6;
    var plotH = plotBottom - plotTop;
    var plotW = w - gutter;
    var barCount = data.length;

    // moderate-width bars: ~60% of each day slot, ~40% visible gap
    var slot = plotW / barCount;
    var barWidth = Math.max(3, slot * 0.6);

    var style = getComputedStyle(document.documentElement);
    var infoColor = style.getPropertyValue('--accent-info').trim() || '#3AB6F0';
    var gridColor = 'rgba(150,180,200,0.12)';

    var tickFont = (Math.max(8, Math.min(10, w / 48))) + 'px Rajdhani, sans-serif';

    function drawGridAndLabels() {
      ctx.font = tickFont;
      ctx.textBaseline = 'bottom';
      ctx.lineWidth = 1;
      for (var t = 0; t < ticks.length; t++) {
        var yy = plotBottom - (ticks[t] / MAX_XP) * plotH;
        ctx.strokeStyle = gridColor;
        ctx.beginPath();
        ctx.moveTo(gutter, yy);
        ctx.lineTo(w, yy);
        ctx.stroke();
        ctx.fillStyle = 'rgba(180,200,215,0.55)';
        ctx.textAlign = 'right';
        ctx.fillText(fmtTick(ticks[t]), gutter - 6, yy - 1);
      }
    }

    var progress = animate ? 0 : 1;

    function renderFrame(p) {
      ctx.clearRect(0, 0, w, h);
      drawGridAndLabels();
      ctx.shadowColor = infoColor;

      for (var i = 0; i < barCount; i++) {
        // clamp above fixed max
        var value = Math.min(data[i], MAX_XP);
        var barHeight = (value / MAX_XP) * plotH;
        barHeight = barHeight * p; // animate height, not position

        // edge-to-edge: first bar starts at gutter, last ends at w
        var x = gutter + i * slot + (slot - barWidth) / 2;
        var y = plotBottom - barHeight;

        ctx.shadowBlur = 5;
        ctx.fillStyle = infoColor;
        ctx.globalAlpha = 0.9;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(x, y, barWidth, barHeight, [3, 3, 0, 0]);
        else ctx.rect(x, y, barWidth, barHeight);
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.shadowBlur = 0;
      }
    }

    if (!animate) {
      renderFrame(1);
      return;
    }

    var start = null;
    var duration = 900;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min(1, (ts - start) / duration);
      p = 1 - Math.pow(1 - p, 3);
      renderFrame(p);
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  drawXpChart(false);

  // ── Load animations: XP fill bar + progress rings (skip if reduced motion) ──
  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function animateXpBars() {
    document.querySelectorAll('.grpg-xp-bar-fill').forEach(function (fill) {
      var target = fill.style.width;
      if (!target) return;
      fill.style.transition = 'none';
      fill.style.width = '0%';
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          fill.style.transition = '';
          fill.style.width = target;
        });
      });
    });
  }

  function animateRings() {
    document.querySelectorAll('.grpg-ring-progress').forEach(function (ring) {
      var dasharray = parseFloat(ring.getAttribute('stroke-dasharray'));
      var finalOffset = parseFloat(ring.getAttribute('stroke-dashoffset'));
      if (isNaN(dasharray) || isNaN(finalOffset)) return;
      ring.setAttribute('stroke-dashoffset', dasharray);
      var start = null;
      var duration = 900;
      function step(ts) {
        if (!start) start = ts;
        var p = Math.min(1, (ts - start) / duration);
        p = 1 - Math.pow(1 - p, 3);
        ring.setAttribute('stroke-dashoffset', (dasharray - (dasharray - finalOffset) * p).toFixed(1));
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  if (!prefersReducedMotion()) {
    window.addEventListener('load', function () {
      animateXpBars();
      animateRings();
    });
  }

  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(drawXpChart, 200);
  });

  // ── Day/Night Toggle ──
  var dayNightBtn = document.getElementById('grpg-daynight-toggle');
  if (dayNightBtn) {
    dayNightBtn.addEventListener('click', function () {
      var isChecked = this.getAttribute('aria-checked') === 'true';
      this.setAttribute('aria-checked', isChecked ? 'false' : 'true');
      document.querySelector('.grpg-dashboard').classList.toggle('grpg-night-mode', !isChecked);
    });
  }

  // ── Judge Review Actions ──
  document.querySelectorAll('[data-review-id]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var id = this.getAttribute('data-review-id');
      var action = this.getAttribute('data-action');
      var container = this.closest('.grpg-panel');
      this.disabled = true;
      this.textContent = action === 'accept' ? 'ACCEPTED' : 'DISPUTED';
      // Hide the other action button
      var siblings = this.closest('div').querySelectorAll('button');
      siblings.forEach(function (s) {
        if (s !== btn) s.disabled = true;
      });
      container.querySelector('.grpg-penalty-row').style.display = 'none';
    });
  });

  // ── Helper: region label lookup ──
  function regionLabel(key) {
    var map = {
      'academy': 'Academy',
      'river': 'River',
      'moon': 'Moon',
      'village': 'Village'
    };
    return map[key] || key;
  }

  // ── Helper: Update topbar XP ──
  function updateTopbarXP(delta) {
    var xpEl = document.querySelector('.grpg-xp-value');
    if (!xpEl) return;
    var parts = xpEl.textContent.split('/').map(function (s) { return parseInt(s.trim()); });
    if (parts.length !== 2) return;
    var current = parts[0] + delta;
    var next = parts[1];
    xpEl.textContent = current + ' / ' + next;

    var barFill = document.querySelector('.grpg-xp-bar-fill');
    if (barFill && next > 0) {
      barFill.style.width = Math.min(100, (current / next * 100)).toFixed(1) + '%';
    }
  }
});