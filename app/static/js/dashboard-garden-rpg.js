/**
 * Dashboard Garden RPG — mission toggles, petal toggles, XP chart, day/night
 */
document.addEventListener('DOMContentLoaded', function () {

  // ── Mission Toggles ──
  document.querySelectorAll('.grpg-mission-status').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var row = this.closest('.grpg-mission-row');
      var isDone = row.getAttribute('data-done') === 'true';
      row.setAttribute('data-done', isDone ? 'false' : 'true');

      var meta = row.querySelector('.grpg-mission-meta');
      var xp = parseInt(this.getAttribute('data-xp')) || 0;

      if (!isDone) {
        meta.innerHTML = '<span class="grpg-done-label">✓ DONE</span>';
        updateTopbarXP(xp);
      } else {
        meta.textContent = row.getAttribute('data-time-range') || '';
        updateTopbarXP(-xp);
      }
    });
  });

  // ── Petal Toggles ──
  document.querySelectorAll('.grpg-check-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var row = this.closest('.grpg-check-row');
      var isDone = row.getAttribute('data-done') === 'true';
      row.setAttribute('data-done', isDone ? 'false' : 'true');
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
    });
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
