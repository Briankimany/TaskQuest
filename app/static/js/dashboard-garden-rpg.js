/**
 * Dashboard Garden RPG — region interactions, mission completion,
 * reschedule/abandon modals, XP chart, day/night, activity feed.
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

  // ── Record completion (click the mission row → popup → backend) ──
  document.addEventListener('click', function (e) {
    var row = e.target.closest('.grpg-mission-row');
    if (!row) return;
    if (e.target.closest('a, button, input, textarea, select')) return;
    if (row.getAttribute('data-done') === 'true') return;
    openCompletionModal(row);
  }, true);

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var row = e.target;
    if (!row || !row.classList || !row.classList.contains('grpg-mission-row')) return;
    e.preventDefault();
    if (row.getAttribute('data-done') === 'true') return;
    openCompletionModal(row);
  });

  function openCompletionModal(row) {
    var taskId = missionTaskId(row);
    if (!taskId) { showNotification('warning', 'No Mission', 'No mission entry to record.'); return; }
    var titleEl = row.querySelector('.grpg-mission-title');
    var title = titleEl ? titleEl.textContent.trim() : 'Mission';
    var statusEl = row.querySelector('.grpg-mission-status');
    var xp = parseInt(statusEl ? statusEl.getAttribute('data-xp') : '') || 0;
    var duration = parseInt(row.getAttribute('data-duration')) || 0;
    var region = row.getAttribute('data-target-region');

    var existing = document.getElementById('grpgCompleteModal');
    if (existing) existing.remove();

    var html = '<div class="modal fade" id="grpgCompleteModal" tabindex="-1" aria-hidden="true">' +
      '<div class="modal-dialog modal-dialog-centered"><div class="modal-content grpg-modal">' +
      '<div class="modal-header"><h5 class="modal-title">RECORD COMPLETION</h5>' +
      '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div>' +
      '<div class="modal-body">' +
      '<div style="font-size:13px;color:var(--text-primary);margin-bottom:2px;">' + title + '</div>' +
      '<div style="font-size:12px;color:var(--text-secondary);margin-bottom:12px;">' +
        (xp > 0 ? '<span style="color:var(--accent-fcs);">+' + xp + ' XP</span>&nbsp;&middot;&nbsp;' : '') +
        '<span style="color:var(--accent-amber);">' + regionLabel(region) + '</span></div>' +
      '<label class="form-label" style="font-size:12px;">STATUS</label>' +
      '<div class="grpg-complete-status" id="grpg-complete-status">' +
        '<button type="button" class="grpg-status-option grpg-status-option-active" data-value="completed">Completed</button>' +
        '<button type="button" class="grpg-status-option" data-value="partial">Partial</button>' +
        '<button type="button" class="grpg-status-option" data-value="skipped">Skipped</button>' +
      '</div>' +
      '<label class="form-label" style="font-size:12px;margin-top:10px;">COMPLETION TIME</label>' +
      '<input type="datetime-local" class="form-control" id="grpg-complete-at" value="' + nowFormatted() + '" style="background:var(--panel-solid);color:var(--text-primary);">' +
      '<label class="form-label" style="font-size:12px;margin-top:10px;">TIME SPENT (MINUTES)</label>' +
      '<input type="number" class="form-control" id="grpg-complete-time" min="0" step="5" placeholder="Estimate in minutes"' +
        (duration > 0 ? ' value="' + duration + '"' : '') + ' style="background:var(--panel-solid);color:var(--text-primary);">' +
      '<label class="form-label" style="font-size:12px;margin-top:10px;">REASON <span id="grpg-complete-reason-hint" style="color:var(--accent-danger);">(optional)</span></label>' +
      '<textarea class="form-control" id="grpg-complete-reason" rows="2" placeholder="Spilled your coffee on the keyboard, got caught in traffic\u2026"></textarea>' +
      '<div id="grpg-complete-aid" style="margin-top:10px;padding:8px 10px;border:1px solid var(--border-hairline);border-radius:6px;' +
        'font-size:11px;color:var(--text-muted);line-height:1.4;">' +
        'The <strong style="color:var(--text-primary);">AI Judge</strong> will evaluate this entry against your reason and time spent, ' +
        'ruling on validity, responsibility and consistency. Penalties apply for skipped or unproven work.</div>' +
      '</div><div class="modal-footer">' +
      '<button type="button" class="btn-app btn-app-secondary" data-bs-dismiss="modal">Cancel</button>' +
      '<button type="button" class="btn-app btn-app-primary" id="grpg-complete-confirm">Submit</button>' +
      '</div></div></div></div>';
    document.body.insertAdjacentHTML('beforeend', html);

    var modal = new bootstrap.Modal(document.getElementById('grpgCompleteModal'));
    modal.show();
    var status = 'completed';
    var statusWrap = document.getElementById('grpg-complete-status');
    var reasonHint = document.getElementById('grpg-complete-reason-hint');
    var completionAt = document.getElementById('grpg-complete-at');

    document.getElementById('grpgCompleteModal').addEventListener('hidden.bs.modal', function () { this.remove(); });
    statusWrap.addEventListener('click', function (e) {
      var opt = e.target.closest('.grpg-status-option');
      if (!opt) return;
      status = opt.getAttribute('data-value');
      statusWrap.querySelectorAll('.grpg-status-option').forEach(function (b) {
        b.classList.toggle('grpg-status-option-active', b === opt);
      });
      var skipped = status === 'skipped';
      reasonHint.textContent = skipped || status === 'partial' ? '(required)' : '(optional)';
      reasonHint.style.color = skipped || status === 'partial' ? 'var(--accent-danger)' : 'var(--text-muted)';
      completionAt.disabled = skipped;
      completionAt.style.opacity = skipped ? '0.5' : '';
    });

    document.getElementById('grpg-complete-confirm').addEventListener('click', function () {
      var confirmBtn = this;
      var reason = document.getElementById('grpg-complete-reason').value.trim();
      if (status !== 'completed' && !reason) {
        showNotification('warning', 'Incomplete', 'A reason is required for ' + status + ' entries.');
        return;
      }
      var timeInput = document.getElementById('grpg-complete-time').value;
      var minutes = timeInput ? parseInt(timeInput, 10) : null;
      var payload = {
        timetable_entry_id: taskId,
        status: status,
        reason: reason,
        comment: ''
      };
      if (status !== 'skipped') {
        payload.completed_on = document.getElementById('grpg-complete-at').value;
      }
      if (minutes && minutes > 0) payload.actual_time_taken = minutes;

      confirmBtn.disabled = true;
      fetch('/api/complete/complete_activity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).then(function (res) {
        if (res.status !== 201) {
          return res.json().catch(function () { return {}; }).then(function (j) {
            throw new Error((j && j.msg) || 'Status ' + res.status);
          });
        }
        return res.json();
      }).then(function (result) {
        modal.hide();
        var change = typeof result.exp_change === 'number' ? result.exp_change : (status === 'completed' ? xp : 0);
        if (change) updateTopbarXP(change);
        var heading = 'Mission Recorded';
        var body = change ? (change >= 0 ? 'Gained <strong>' + change + '</strong> XP!' : 'Lost <strong>' + Math.abs(change) + '</strong> XP') : 'Recorded.';
        if (status === 'completed') heading = 'Mission Complete';
        else if (status === 'partial') heading = 'Partial Completion';
        else if (status === 'skipped') heading = 'Mission Skipped';
        showNotification(change >= 0 ? 'success' : 'warning', heading, body);
        reconcileCards();
      }).catch(function (err) {
        confirmBtn.disabled = false;
        showNotification('danger', 'Error', 'Could not record completion: ' + err.message);
      });
    });
  }

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
          meta.innerHTML = start + ' <span class="grpg-done-label" style="color:var(--text-muted);">RESCHEDULED</span>';
        }
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
        if (meta) meta.innerHTML = '<span class="grpg-done-label" style="color:var(--accent-danger);opacity:0.6;">ABANDONED</span>';
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
    var cyan = style.getPropertyValue('--cyan').trim() || '#1CAED5';
    var cyanMuted = style.getPropertyValue('--cyan-muted').trim() || '#147A96';
    var cyanBright = style.getPropertyValue('--cyan-bright').trim() || '#31D2F2';
    var gridColor = 'rgba(110,150,160,0.10)';

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

    // Highest value drives the "today/current" bright bar accent
    var peak = 0;
    for (var i = 0; i < barCount; i++) {
      var pv = Math.min(data[i], MAX_XP);
      if (pv > peak) peak = pv;
    }

    function renderFrame(p) {
      ctx.clearRect(0, 0, w, h);
      drawGridAndLabels();
      ctx.shadowColor = 'rgba(49,210,242,0.30)';

      for (var i = 0; i < barCount; i++) {
        // clamp above fixed max
        var value = Math.min(data[i], MAX_XP);
        var barHeight = (value / MAX_XP) * plotH;
        barHeight = barHeight * p; // animate height, not position

        // edge-to-edge: first bar starts at gutter, last ends at w
        var x = gutter + i * slot + (slot - barWidth) / 2;
        var y = plotBottom - barHeight;

        ctx.shadowBlur = 5;
        ctx.fillStyle = value <= 0 ? cyanMuted : (value >= peak ? cyanBright : cyan);
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

  // ── Missions: collapse/expand the whole card with the left chevron ──
  var missionsCollapse = document.getElementById('grpg-missions-collapse');
  if (missionsCollapse) {
    missionsCollapse.addEventListener('click', function () {
      var body = document.getElementById('grpg-missions-body');
      var collapsed = !body || body.getAttribute('data-collapsed') !== 'true';
      if (body) body.setAttribute('data-collapsed', collapsed ? 'true' : 'false');
      this.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
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
            var xpColor = (a.xp || 0) >= 0 ? 'var(--accent-fcs)' : 'var(--accent-danger)';
            var attrColor = 'var(--accent-' + (a.color || 'amber') + ')';
            var xpText = (a.xp >= 0 ? '+' : '') + a.xp;
            html += '<div style="display:flex;align-items:center;gap:8px;font-size:12px;">' +
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
          row.setAttribute('data-color', m.color || '');
          row.setAttribute('data-status-override', m.status_override || '');
          var done = (m.status === 'COMPLETED' || m.status === 'COMPLETED_LATE' || m.status === 'PARTIAL');
          row.setAttribute('data-done', done ? 'true' : 'false');
          row.classList.toggle('grpg-mission-partial', m.status === 'PARTIAL');
          row.setAttribute('data-time-range', m.deadline || '');
          var rowColor = m.status_override ? 'var(--accent-red)' : 'var(--accent-' + (m.color || 'amber') + ')';
          row.style.setProperty('--mission-color', rowColor);
          var statusBtn = row.querySelector('.grpg-mission-status');
          if (statusBtn) {
            statusBtn.style.setProperty('--tag-color', rowColor);
            statusBtn.setAttribute('data-done', done ? 'true' : 'false');
            statusBtn.classList.toggle('grpg-mission-completed', m.status === 'COMPLETED');
            statusBtn.classList.toggle('grpg-mission-late', m.status === 'COMPLETED_LATE');
            statusBtn.textContent = '';
          }
          var meta = row.querySelector('.grpg-mission-meta');
          if (meta) {
            var label = '';
            if (m.status === 'COMPLETED') label = '<span class="grpg-done-label">DONE</span>';
            else if (m.status === 'PARTIAL') label = '<span class="grpg-done-label" style="color:var(--accent-amber);">PARTIAL</span>';
            else if (m.status === 'COMPLETED_LATE') label = '<span class="grpg-done-label" style="color:var(--accent-danger);">LATE</span>';
            else if (m.status === 'MISSED') label = '<span class="grpg-done-label" style="color:var(--accent-danger);">MISSED</span>';
            else if (m.status === 'LOCKED') label = '<span class="grpg-done-label" style="opacity:0.5;">LOCKED</span>';
            else if (m.status === 'ABANDONED') label = '<span class="grpg-done-label" style="color:var(--accent-danger);opacity:0.6;">ABANDONED</span>';
            else if (m.status === 'RESCHEDULED') label = '<span class="grpg-done-label" style="color:var(--text-muted);">RESCHEDULED</span>';
            else label = (m.deadline || '') + (m.countdown ? ' \u00B7 ' + m.countdown : '');
            meta.innerHTML = label;
          }
        });
        // Re-sort rows to match the server's time-of-day order: next mission
        // first, earliest-started last (tasks drift downward as time passes).
        var listEl = document.getElementById('grpg-missions-list');
        if (listEl) {
          var ordered = [];
          missions.forEach(function (m) {
            var el = listEl.querySelector('[data-mission-id="' + m.id + '"]');
            if (el && ordered.indexOf(el) === -1) ordered.push(el);
          });
          card.querySelectorAll('.grpg-mission-row').forEach(function (r) {
            if (ordered.indexOf(r) === -1) ordered.push(r);
          });
          ordered.forEach(function (el) { listEl.appendChild(el); });
        }
      }).catch(function () {});
  }

  function cap(s) {
    return s ? (s.charAt(0).toUpperCase() + s.slice(1)) : s;
  }

  function reconcileCards() {
    reconcileActivity();
    reconcileMissions();
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