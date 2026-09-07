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
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.grpg-mission-status');
    if (!btn) return;
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
      var change = typeof result.exp_change === 'number' ? result.exp_change : xp;
      updateTopbarXP(change);
      showNotification(change >= 0 ? 'success' : 'warning', 'Mission Complete',
        change >= 0 ? 'Gained <strong>' + change + '</strong> XP!' : 'Lost <strong>' + Math.abs(change) + '</strong> XP!');
      reconcileCards();
    }).catch(function (err) {
      btn.disabled = false;
      showNotification('danger', 'Error', 'Could not complete mission: ' + err.message);
    });
  }, true);

  // Toggle expanded mission detail when the row (not a button) is clicked
  document.addEventListener('click', function (e) {
    var row = e.target.closest('.grpg-mission-row');
    if (!row) return;
    if (e.target.closest('button')) return; // let button handlers deal with their own actions
    row.classList.toggle('grpg-mission-expanded-open');
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
        reconcileCards();
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
        reconcileCards();
      }).catch(function (err) {
        confirmBtn.disabled = false;
        showNotification('danger', 'Error', 'Could not abandon mission: ' + err.message);
      });
    });
  }

  // ── Mission action buttons (RESCHEDULE / ABANDON) → wired modals ──
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.grpg-mission-action');
    if (!btn) return;
    e.stopPropagation();
    var action = btn.getAttribute('data-action');
    if (action === 'reschedule') {
      openRescheduleModal(btn);
    } else if (action === 'abandon') {
      openAbandonModal(btn);
    }
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

  // ── Judge Review Actions (accept / dispute) — delegated ──
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-review-id]');
    if (!btn) return;
    var id = btn.getAttribute('data-review-id');
    var action = btn.getAttribute('data-action');
    var container = btn.closest('.grpg-panel');

    if (action === 'accept') {
      btn.disabled = true;
      fetch('/api/judge/' + id + '/accept', { method: 'POST' })
        .then(function (res) { if (!res.ok) throw new Error('Status ' + res.status); return res.json(); })
        .then(function () {
          showNotification('success', 'System Judge', 'Verdict accepted.');
          reconcileJudge();
        })
        .catch(function (e2) {
          btn.disabled = false;
          showNotification('danger', 'Error', 'Could not accept: ' + e2.message);
        });
      return;
    }

    if (action === 'dispute') {
      var reason = prompt('Why do you dispute this review?');
      if (!reason) return;
      btn.disabled = true;
      fetch('/api/judge/' + id + '/dispute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reason })
      })
        .then(function (res) { if (!res.ok) throw new Error('Status ' + res.status); return res.json(); })
        .then(function () {
          showNotification('warning', 'System Judge', 'Verdict re-judged. Status: DISPUTED.');
          reconcileJudge();
        })
        .catch(function (e2) {
          btn.disabled = false;
          showNotification('danger', 'Error', 'Could not dispute: ' + e2.message);
        });
      return;
    }
  });

  // ── Judge inline "View Log" metrics toggle ──
  var judgeToggle = document.getElementById('grpg-judge-toggle');
  if (judgeToggle) {
    judgeToggle.addEventListener('click', function () {
      var metrics = document.getElementById('grpg-judge-metrics');
      if (!metrics) return;
      var isOpen = !metrics.hasAttribute('hidden');
      metrics.hidden = isOpen;
      this.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
      this.textContent = isOpen ? 'View Log' : 'Hide Log';
    });
  }

  // ── Missions: "View All (N)" in-place toggle ──
  function applyMissionsCollapse(card) {
    var rows = card.querySelectorAll('.grpg-mission-row');
    var toggle = document.getElementById('grpg-missions-toggle');
    if (!toggle) return;
    var expanded = toggle.getAttribute('data-expanded') === 'true';
    rows.forEach(function (r, idx) {
      r.classList.toggle('grpg-missions-hidden-row', idx >= 3 && !expanded);
    });
    var total = rows.length;
    toggle.style.display = total > 3 ? 'block' : 'none';
    toggle.textContent = expanded ? 'SHOW TOP 3 \u2227' : ('VIEW ALL (' + total + ') \u2228');
  }

  var missionsToggle = document.getElementById('grpg-missions-toggle');
  if (missionsToggle) {
    missionsToggle.addEventListener('click', function () {
      var expanded = this.getAttribute('data-expanded') === 'true';
      this.setAttribute('data-expanded', expanded ? 'false' : 'true');
      applyMissionsCollapse(document.getElementById('grpg-missions-card'));
    });
  }

  // ── Client-side reconciliation (fetch JSON feeds, patch DOM in place) ──
  function reconcileActivity() {
    fetch('/api/activity/recent', { headers: { 'Accept': 'application/json' } })
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (data) {
        if (!data) return;
        var listEl = document.getElementById('grpg-activity-list');
        if (!listEl) return;
        var acts = data.activity || [];
        var html = '';
        if (!acts.length) {
          html = '<div id="grpg-activity-empty" style="text-align:center;padding:16px 0;color:var(--text-muted);font-size:12px;">No activity yet today</div>';
        } else {
          acts.slice(0, 4).forEach(function (a) {
            var stColor = a.status === 'DONE' ? 'var(--accent-active)' : (a.status === 'LATE' ? 'var(--accent-warning)' : 'var(--accent-danger)');
            var xpColor = (a.xp || 0) >= 0 ? 'var(--accent-fcs)' : 'var(--accent-danger)';
            var attrColor = 'var(--accent-' + (a.attr || 'int') + ')';
            var xpText = (a.xp >= 0 ? '+' : '') + a.xp;
            html += '<div style="display:flex;align-items:center;gap:8px;font-size:12px;">' +
              '<span style="flex-shrink:0;width:44px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.03em;color:' + stColor + ';">' + a.status + '</span>' +
              '<span style="flex:1;color:var(--text-primary);">' + a.name + '</span>' +
              '<span style="font-size:10px;color:var(--text-secondary);">' + (a.time || '') + '</span>' +
              '<span style="font-family:var(--font-mono);font-weight:600;color:' + xpColor + ';">' + xpText + '</span>' +
              '<span style="font-size:10px;color:' + attrColor + ';">\u2192 ' + cap(a.target_region) + '</span></div>';
          });
        }
        listEl.innerHTML = html;
      }).catch(function () {});
  }

  function reconcileMissions() {
    fetch('/api/missions/today', { headers: { 'Accept': 'application/json' } })
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (data) {
        if (!data) return;
        var card = document.getElementById('grpg-missions-card');
        if (!card) return;
        var countEl = document.getElementById('grpg-missions-count');
        if (countEl) countEl.textContent = data.total;
        // Update per-row status flags + meta in place without a full re-render,
        // so expanded/open and collapse state are preserved.
        var missions = data.missions || [];
        var rows = card.querySelectorAll('.grpg-mission-row');
        rows.forEach(function (row) {
          var id = row.getAttribute('data-mission-id');
          var m = null;
          for (var i = 0; i < missions.length; i++) {
            if (missions[i].id === id) { m = missions[i]; break; }
          }
          if (!m) return;
          row.setAttribute('data-status', m.status);
          var done = (m.status === 'COMPLETED' || m.status === 'COMPLETED_LATE');
          row.setAttribute('data-done', done ? 'true' : 'false');
          row.setAttribute('data-time-range', m.deadline || '');
          var statusBtn = row.querySelector('.grpg-mission-status');
          if (statusBtn) {
            statusBtn.setAttribute('aria-pressed', done ? 'true' : 'false');
            statusBtn.classList.toggle('grpg-mission-completed', m.status === 'COMPLETED');
            statusBtn.classList.toggle('grpg-mission-late', m.status === 'COMPLETED_LATE');
            var sym = m.status === 'COMPLETED' ? '\u2713' : (m.status === 'COMPLETED_LATE' ? '\u23F0' : (m.status === 'MISSED' ? '\u2717' : ''));
            statusBtn.textContent = sym;
          }
          var meta = row.querySelector('.grpg-mission-meta');
          if (meta) {
            var label = '';
            if (m.status === 'COMPLETED') label = '<span class="grpg-done-label">\u2713 DONE</span>';
            else if (m.status === 'COMPLETED_LATE') label = '<span class="grpg-done-label" style="color:var(--accent-warning);">\u23F0 LATE</span>';
            else if (m.status === 'MISSED') label = '<span class="grpg-done-label" style="color:var(--accent-danger);">\u2717 MISSED</span>';
            else if (m.status === 'LOCKED') label = '<span class="grpg-done-label" style="opacity:0.5;">\u1F512 LOCKED</span>';
            else if (m.status === 'ABANDONED') label = '<span class="grpg-done-label" style="color:var(--accent-danger);opacity:0.6;">\u2716 ABANDONED</span>';
            else if (m.status === 'RESCHEDULED') label = '<span class="grpg-done-label" style="color:var(--text-muted);">\u23F1 RESCHEDULED</span>';
            else label = (m.deadline || '') + (m.countdown ? ' \u00B7 ' + m.countdown : '');
            meta.innerHTML = label;
          }
        });
        applyMissionsCollapse(card);
      }).catch(function () {});
  }

  function reconcileJudge() {
    fetch('/api/system-judge/latest', { headers: { 'Accept': 'application/json' } })
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (data) {
        if (!data) return;
        var card = document.getElementById('grpg-judge-card');
        if (!card) return;
        var missedPill = card.querySelector('.grpg-danger-pill');
        if (data.missed_count) {
          if (missedPill) missedPill.textContent = data.missed_count + ' missed';
          else {
            var hdr = card.querySelector('.grpg-panel-header');
            var span = document.createElement('span');
            span.className = 'grpg-danger-pill';
            span.title = 'Missed tasks';
            span.textContent = data.missed_count + ' missed';
            if (hdr) hdr.insertBefore(span, hdr.querySelector('#grpg-judge-toggle'));
          }
        } else if (missedPill) {
          missedPill.remove();
        }
        var review = data.review;
        var titleEl = card.querySelector('.grpg-judge-review-title');
        var reasonEl = card.querySelector('#grpg-judge-reason');
        var metricsEl = document.getElementById('grpg-judge-metrics');
        var toggleBtn = document.getElementById('grpg-judge-toggle');
        if (!review || !review.id) {
          if (titleEl) titleEl.innerHTML = 'No reviews yet \u00B7 you\'re clear.';
          var existingReason = card.querySelector('#grpg-judge-reason');
          if (existingReason) existingReason.remove();
          if (metricsEl) metricsEl.hidden = true;
          if (toggleBtn) toggleBtn.hidden = true;
          var actionBar = card.querySelector('#grpg-judge-actions');
          if (actionBar) actionBar.remove();
          return;
        }
        if (toggleBtn && toggleBtn.hidden) toggleBtn.hidden = false;

        var badge = '';
        if (review.status === 'COMPLETED_LATE') badge = ' <span class="grpg-danger-pill" style="color:var(--accent-warning);">\u23F0 LATE</span>';
        else if (review.status === 'MISSED') badge = ' <span class="grpg-danger-pill">\u2717 MISSED</span>';
        if (titleEl) titleEl.innerHTML = (review.task || '') + badge;

        // Update reason text
        var reason = review.user_reason || '';
        if (reason) {
          if (!reasonEl) {
            reasonEl = document.createElement('p');
            reasonEl.id = 'grpg-judge-reason';
            reasonEl.style.cssText = 'font-size:10px;color:var(--text-muted);margin:4px 0 8px;font-style:italic;';
            if (titleEl) titleEl.parentNode.insertBefore(reasonEl, titleEl.nextSibling);
          }
          reasonEl.textContent = '\u201C' + reason + '\u201D';
        } else if (reasonEl) {
          reasonEl.remove();
        }

        // Update metrics if visible
        if (metricsEl && review.metrics) {
          var order = ['validity', 'responsibility', 'consistency'];
          var titles = { 'validity': 'Validity', 'responsibility': 'Responsibility', 'consistency': 'Consistency' };
          order.forEach(function (key) {
            var val = (review.metrics && review.metrics[key]) ? review.metrics[key] : 0;
            var rows = metricsEl.querySelectorAll('.grpg-metric-row');
            rows.forEach(function (rw) {
              var label = rw.querySelector('span').textContent;
              if (label === titles[key]) {
                rw.querySelector('.grpg-bar-fill').style.width = val + '%';
                var last = rw.querySelector('span:last-child');
                if (last) last.textContent = val + '%';
              }
            });
          });
          var penaltyRow = metricsEl.querySelector('.grpg-penalty-row .grpg-penalty-value');
          if (penaltyRow) penaltyRow.textContent = (review.penalty || 0) + ' XP';
        }

        // Action bar (accept/dispute) — only for PENDING
        var actionBar = card.querySelector('#grpg-judge-actions');
        if (actionBar) actionBar.remove();
        if (review.review_status === 'PENDING') {
          actionBar = document.createElement('div');
          actionBar.id = 'grpg-judge-actions';
          actionBar.style.cssText = 'display:flex;gap:8px;margin-top:8px;';
          actionBar.innerHTML = '<button class="grpg-solid-btn" style="flex:1;" data-review-id="' + review.id + '" data-action="accept">ACCEPT</button>' +
            '<button class="grpg-ghost-btn" style="flex:1;" data-review-id="' + review.id + '" data-action="dispute">DISPUTE</button>';
          var openLogBtn = card.querySelector('a.grpg-ghost-btn');
          if (openLogBtn) card.insertBefore(actionBar, openLogBtn);
          else card.appendChild(actionBar);
        } else {
          var statusLine = document.createElement('p');
          statusLine.style.cssText = 'font-size:10px;color:var(--text-muted);margin-top:8px;text-align:center;';
          statusLine.textContent = review.review_status;
          var openLogBtn2 = card.querySelector('a.grpg-ghost-btn');
          if (openLogBtn2) card.insertBefore(statusLine, openLogBtn2);
          else card.appendChild(statusLine);
        }
      }).catch(function () {});
  }

  function cap(s) {
    return s ? (s.charAt(0).toUpperCase() + s.slice(1)) : s;
  }

  function reconcileCards() {
    reconcileActivity();
    reconcileMissions();
    reconcileJudge();
  }

  reconcileCards();

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