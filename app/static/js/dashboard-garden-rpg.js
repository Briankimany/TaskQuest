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

  // ── Mission helpers ──
  function missionTaskId(row) {
    var n = parseInt((row.getAttribute('data-mission-id') || '').replace('mission-', ''), 10);
    return isNaN(n) ? null : n;
  }

  function nowFormatted() {
    var d = new Date();
    function p(v) { return (v < 10 ? '0' : '') + v; }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
      'T' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function browserTimezone() {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Africa/Nairobi';
    } catch (e) {
      return 'Africa/Nairobi';
    }
  }

  // ── Complete mission (✓ toggle) → backend ──
  document.querySelectorAll('.grpg-mission-status').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (btn.getAttribute('aria-pressed') === 'true') return; // one-way commit
      var row = btn.closest('.grpg-mission-row');
      var taskId = missionTaskId(row);
      if (!taskId) return;
      var meta = row.querySelector('.grpg-mission-meta');
      var xp = parseInt(btn.getAttribute('data-xp')) || 0;
      var region = row.getAttribute('data-target-region');
      var attrs = row.getAttribute('data-attr-deltas') || '';

      btn.disabled = true;
      fetch('/api/complete/complete_activity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timetable_entry_id: taskId,
          status: 'completed',
          completed_on: nowFormatted(),
          comment: ''
        })
      }).then(function (res) {
        if (res.status !== 201) {
          return res.json().catch(function () { return {}; }).then(function (j) {
            throw new Error((j && j.msg) || 'Status ' + res.status);
          });
        }
        return res.json();
      }).then(function (result) {
        row.setAttribute('data-done', 'true');
        btn.setAttribute('aria-pressed', 'true');
        meta.innerHTML = '<span class="grpg-done-label">\u2713 DONE</span>';

        var change = typeof result.exp_change === 'number' ? result.exp_change : xp;
        updateTopbarXP(change);

        if (region) {
          meta.insertAdjacentHTML('beforeend',
            '<span class="grpg-inline-feedback">' + attrs + ' <span class="grpg-feedback-arrow">\u2192</span> ' + regionLabel(region) + '</span>');
          triggerRegionPulse(region);
        }
        showNotification(change >= 0 ? 'success' : 'warning', 'Mission Complete',
          change >= 0 ? 'Gained <strong>' + change + '</strong> XP!' : 'Lost <strong>' + Math.abs(change) + '</strong> XP!');
      }).catch(function (err) {
        btn.disabled = false;
        showNotification('danger', 'Error', 'Could not complete mission: ' + err.message);
      });
    });
  });

  // Toggle expanded mission detail when the row (not a button) is clicked
  document.querySelectorAll('.grpg-mission-row').forEach(function (row) {
    row.addEventListener('click', function (e) {
      if (e.target.closest('button')) return; // let button handlers deal with their own actions
      row.classList.toggle('grpg-mission-expanded-open');
    });
  });

  // Resolve the mission row for an action button (objective block has no row → first ACTIVE mission)
  function resolveMissionRow(btn) {
    var row = btn.closest('.grpg-mission-row');
    if (row) return row;
    return document.querySelector('.grpg-mission-row[data-status="ACTIVE"]');
  }

  // ── RESCHEDULE (modal → PUT /api/timetable/task/<id>) ──
  function openRescheduleModal(btn) {
    var row = resolveMissionRow(btn);
    var taskId = missionTaskId(row);
    if (!taskId) { showNotification('warning', 'No Mission', 'No active mission to reschedule.'); return; }
    var titleEl = row.querySelector('.grpg-mission-title');
    var title = titleEl ? titleEl.textContent.trim() : 'Mission';
    var duration = parseInt(row.getAttribute('data-duration')) || 0;

    var existing = document.getElementById('grpgRescheduleModal');
    if (existing) existing.remove();

    var html = '<div class="modal fade" id="grpgRescheduleModal" tabindex="-1" aria-hidden="true">' +
      '<div class="modal-dialog modal-dialog-centered"><div class="modal-content grpg-modal">' +
      '<div class="modal-header"><h5 class="modal-title">RESCHEDULE</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div>' +
      '<div class="modal-body">' +
      '<div style="font-size:13px;color:var(--text-primary);margin-bottom:10px;">' + title + '</div>' +
      '<label class="form-label" style="font-size:12px;">NEW START TIME</label>' +
      '<input type="time" class="form-control" id="grpg-reschedule-time" value="09:00">' +
      '</div><div class="modal-footer">' +
      '<button type="button" class="btn-app btn-app-secondary" data-bs-dismiss="modal">Cancel</button>' +
      '<button type="button" class="btn-app btn-app-primary" id="grpg-reschedule-confirm">Reschedule</button>' +
      '</div></div></div></div>';
    document.body.insertAdjacentHTML('beforeend', html);

    var modal = new bootstrap.Modal(document.getElementById('grpgRescheduleModal'));
    modal.show();

    document.getElementById('grpgRescheduleModal').addEventListener('hidden.bs.modal', function () { this.remove(); });
    document.getElementById('grpg-reschedule-confirm').addEventListener('click', function () {
      var confirmBtn = this;
      var start = document.getElementById('grpg-reschedule-time').value;
      if (!start) {
        showNotification('warning', 'Incomplete', 'Pick a start time.');
        return;
      }
      var payload = { start_time: start, time_zone: browserTimezone() };
      if (duration > 0) payload.task_duration = duration;

      confirmBtn.disabled = true;
      fetch('/api/timetable/task/' + taskId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(function (res) {
        if (!res.ok) {
          return res.json().catch(function () { return {}; }).then(function (j) {
            throw new Error((j && j.msg) || 'Status ' + res.status);
          });
        }
        return res.json();
      }).then(function () {
        modal.hide();
        row.setAttribute('data-time-range', start);
        row.setAttribute('data-status', 'RESCHEDULED');
        var meta = row.querySelector('.grpg-mission-meta');
        var done = row.getAttribute('data-done') === 'true';
        if (meta && !done) {
          meta.innerHTML = start + ' <span class="grpg-done-label" style="color:var(--text-muted);">\u23F1 RESCHEDULED</span>';
        }
        row.classList.remove('grpg-mission-expanded-open');
        showNotification('info', 'Rescheduled', 'Mission moved to ' + start + '.');
      }).catch(function (err) {
        confirmBtn.disabled = false;
        showNotification('danger', 'Error', 'Could not reschedule: ' + err.message);
      });
    });
  }

  // ── ABANDON (reason modal → complete_activity skipped) ──
  function openAbandonModal(btn) {
    var row = resolveMissionRow(btn);
    var taskId = missionTaskId(row);
    if (!taskId) { showNotification('warning', 'No Mission', 'No active mission to abandon.'); return; }
    var titleEl = row.querySelector('.grpg-mission-title');
    var title = titleEl ? titleEl.textContent.trim() : 'Mission';

    var existing = document.getElementById('grpgAbandonModal');
    if (existing) existing.remove();

    var html = '<div class="modal fade" id="grpgAbandonModal" tabindex="-1" aria-hidden="true">' +
      '<div class="modal-dialog modal-dialog-centered"><div class="modal-content grpg-modal">' +
      '<div class="modal-header"><h5 class="modal-title">ABANDON MISSION</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div>' +
      '<div class="modal-body">' +
      '<div style="font-size:13px;color:var(--text-primary);margin-bottom:10px;">' + title + '</div>' +
      '<div class="alert alert-warning" style="font-size:0.85rem;">Abandoning results in EXP penalties and a judge review.</div>' +
      '<label class="form-label" style="font-size:12px;">REASON</label>' +
      '<textarea class="form-control" id="grpg-abandon-reason" rows="2" placeholder="Why are you abandoning this?"></textarea>' +
      '</div><div class="modal-footer">' +
      '<button type="button" class="btn-app btn-app-secondary" data-bs-dismiss="modal">Cancel</button>' +
      '<button type="button" class="btn-app btn-app-danger" id="grpg-abandon-confirm">Abandon</button>' +
      '</div></div></div></div>';
    document.body.insertAdjacentHTML('beforeend', html);

    var modal = new bootstrap.Modal(document.getElementById('grpgAbandonModal'));
    modal.show();

    document.getElementById('grpgAbandonModal').addEventListener('hidden.bs.modal', function () { this.remove(); });
    document.getElementById('grpg-abandon-confirm').addEventListener('click', function () {
      var confirmBtn = this;
      var reason = document.getElementById('grpg-abandon-reason').value.trim();
      if (!reason) {
        showNotification('warning', 'Incomplete', 'A reason is required to abandon.');
        return;
      }

      confirmBtn.disabled = true;
      fetch('/api/complete/complete_activity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timetable_entry_id: taskId,
          status: 'skipped',
          reason: reason,
          comment: ''
        })
      }).then(function (res) {
        if (res.status !== 201) {
          return res.json().catch(function () { return {}; }).then(function (j) {
            throw new Error((j && j.msg) || 'Status ' + res.status);
          });
        }
        return res.json();
      }).then(function (result) {
        modal.hide();
        row.setAttribute('data-status', 'ABANDONED');
        row.setAttribute('data-done', 'false');
        var meta = row.querySelector('.grpg-mission-meta');
        if (meta) meta.innerHTML = '<span class="grpg-done-label" style="color:var(--accent-danger);opacity:0.6;">\u2716 ABANDONED</span>';
        row.classList.remove('grpg-mission-expanded-open');

        var change = typeof result.exp_change === 'number' ? result.exp_change : 0;
        if (change) updateTopbarXP(change);
        showNotification(change >= 0 ? 'success' : 'warning', 'Mission Abandoned',
          change ? (change >= 0 ? 'Gained <strong>' + change + '</strong> XP' : 'Lost <strong>' + Math.abs(change) + '</strong> XP') : 'Recorded.');
      }).catch(function (err) {
        confirmBtn.disabled = false;
        showNotification('danger', 'Error', 'Could not abandon mission: ' + err.message);
      });
    });
  }

  // Mission action buttons (RESCHEDULE / ABANDON) → wired modals
  document.querySelectorAll('.grpg-mission-action').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var action = btn.getAttribute('data-action');
      if (action === 'reschedule') {
        openRescheduleModal(btn);
      } else if (action === 'abandon') {
        openAbandonModal(btn);
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
      var id = btn.getAttribute('data-review-id');
      var action = btn.getAttribute('data-action');
      var container = btn.closest('.grpg-panel');

      function finalize() {
        btn.disabled = true;
        btn.textContent = action === 'accept' ? 'ACCEPTED' : 'DISPUTED';
        var siblings = btn.closest('div').querySelectorAll('button');
        siblings.forEach(function (s) {
          if (s !== btn) s.disabled = true;
        });
        var penaltyRow = container.querySelector('.grpg-penalty-row');
        if (penaltyRow) penaltyRow.style.display = 'none';
      }

      if (action === 'accept') {
        fetch('/api/judge/' + id + '/accept', { method: 'POST' })
          .then(function (res) { if (!res.ok) throw new Error('Status ' + res.status); return res.json(); })
          .then(function () { finalize(); showNotification('success', 'System Judge', 'Verdict accepted.'); })
          .catch(function (e) { showNotification('danger', 'Error', 'Could not accept: ' + e.message); });
        return;
      }

      var reason = prompt('Why do you dispute this review?');
      if (!reason) return;
      fetch('/api/judge/' + id + '/dispute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reason })
      })
        .then(function (res) { if (!res.ok) throw new Error('Status ' + res.status); return res.json(); })
        .then(function (result) {
          var metrics = result.metrics || {};
          container.querySelectorAll('.grpg-metric-row').forEach(function (row) {
            var label = row.querySelector('span').textContent.toLowerCase();
            if (metrics[label] !== undefined) {
              row.querySelector('.grpg-bar-fill').style.width = metrics[label] + '%';
              row.querySelector('span:last-child').textContent = metrics[label] + '%';
            }
          });
          finalize();
          showNotification('warning', 'System Judge', 'Verdict re-judged. Status: DISPUTED.');
        })
        .catch(function (e) { showNotification('danger', 'Error', 'Could not dispute: ' + e.message); });
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