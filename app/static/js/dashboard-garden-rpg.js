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

  // ── XP Chart (Canvas 2D) ──
  function drawXpChart() {
    var canvas = document.getElementById('grpg-xp-chart');
    if (!canvas) return;

    var dataEl = document.getElementById('grpg-xp-data');
    var data;
    try {
      data = JSON.parse(dataEl.textContent);
    } catch (e) {
      data = [0, 0, 0, 0, 0, 0, 0];
    }

    var ctx = canvas.getContext('2d');
    var dpr = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    var w = rect.width;
    var h = rect.height;
    var max = Math.max.apply(null, data) || 1;
    var barCount = data.length;
    var gap = 6;
    var barWidth = (w - gap * (barCount + 1)) / barCount;

    var style = getComputedStyle(document.documentElement);
    var infoColor = style.getPropertyValue('--accent-info').trim() || '#34C6E8';

    ctx.clearRect(0, 0, w, h);

    for (var i = 0; i < barCount; i++) {
      var barHeight = (data[i] / max) * (h - 8);
      var x = gap + i * (barWidth + gap);
      var y = h - barHeight;

      ctx.fillStyle = infoColor;
      ctx.globalAlpha = 0.8;
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barHeight, 3);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  drawXpChart();

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