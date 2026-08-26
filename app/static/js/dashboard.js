/**
 * Dashboard — task completion, modals, day finalization
 */
document.addEventListener('DOMContentLoaded', function () {

    // ── Tooltips ──
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el, { html: true });
    });

    // ── Completion modals ──
    document.querySelectorAll('.complete-btn').forEach(function (btn) {
        btn.addEventListener('click', function () { showCompletionModal(this.getAttribute('data-id')); });
    });
    document.querySelectorAll('.partial-btn').forEach(function (btn) {
        btn.addEventListener('click', function () { showPartialModal(this.getAttribute('data-id')); });
    });
    document.querySelectorAll('.skip-btn').forEach(function (btn) {
        btn.addEventListener('click', function () { showSkipModal(this.getAttribute('data-id')); });
    });

    function nowFormatted() {
        var n = new Date();
        return n.getFullYear() + '-' +
            String(n.getMonth() + 1).padStart(2, '0') + '-' +
            String(n.getDate()).padStart(2, '0') + 'T' +
            String(n.getHours()).padStart(2, '0') + ':' +
            String(n.getMinutes()).padStart(2, '0');
    }

    function showCompletionModal(taskId) {
        var html = '<div class="modal fade" id="completeModal" tabindex="-1" aria-hidden="true">' +
            '<div class="modal-dialog"><div class="modal-content">' +
            '<div class="modal-header"><h5 class="modal-title">Complete Task</h5>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>' +
            '<div class="modal-body">' +
            '<div class="mb-3"><label class="form-label">Completion Time</label>' +
            '<input type="datetime-local" class="form-control" id="completed-on" value="' + nowFormatted() + '" required></div>' +
            '<div class="mb-3"><label class="form-label">Comments</label>' +
            '<textarea class="form-control" id="complete-comment" rows="3" required></textarea></div>' +
            '</div><div class="modal-footer">' +
            '<button type="button" class="btn-app btn-app-secondary" data-bs-dismiss="modal">Cancel</button>' +
            '<button type="button" class="btn-app btn-app-primary" id="confirm-complete">Submit</button>' +
            '</div></div></div></div>';

        document.body.insertAdjacentHTML('beforeend', html);
        var modal = new bootstrap.Modal(document.getElementById('completeModal'));
        modal.show();

        document.getElementById('confirm-complete').addEventListener('click', function () {
            var time = document.getElementById('completed-on').value;
            var comment = document.getElementById('complete-comment').value;
            if (!time || !comment) { alert('Both fields required'); return; }
            completeTask(taskId, 'completed', null, null, time, comment);
            modal.hide();
            document.getElementById('completeModal').addEventListener('hidden.bs.modal', function () { this.remove(); });
        });
    }

    function showPartialModal(taskId) {
        var html = '<div class="modal fade" id="partialModal" tabindex="-1" aria-hidden="true">' +
            '<div class="modal-dialog"><div class="modal-content">' +
            '<div class="modal-header"><h5 class="modal-title">Partial Completion</h5>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>' +
            '<div class="modal-body">' +
            '<div class="mb-3"><label class="form-label">Completion Time</label>' +
            '<input type="datetime-local" class="form-control" id="completed-on" value="' + nowFormatted() + '" required></div>' +
            '<div class="mb-3"><label class="form-label">Time Spent (minutes)</label>' +
            '<input type="number" class="form-control" id="actual-time" min="1" required></div>' +
            '<div class="mb-3"><label class="form-label">Reason</label>' +
            '<textarea class="form-control" id="reason" rows="2" required></textarea></div>' +
            '<div class="mb-3"><label class="form-label">Comments</label>' +
            '<textarea class="form-control" id="comment" rows="2"></textarea></div>' +
            '</div><div class="modal-footer">' +
            '<button type="button" class="btn-app btn-app-secondary" data-bs-dismiss="modal">Cancel</button>' +
            '<button type="button" class="btn-app btn-app-primary" id="confirm-partial">Submit</button>' +
            '</div></div></div></div>';

        document.body.insertAdjacentHTML('beforeend', html);
        var modal = new bootstrap.Modal(document.getElementById('partialModal'));
        modal.show();

        document.getElementById('confirm-partial').addEventListener('click', function () {
            var time = document.getElementById('completed-on').value;
            var actual = document.getElementById('actual-time').value;
            var reason = document.getElementById('reason').value;
            var comment = document.getElementById('comment').value;
            if (!time || !actual || !reason) { alert('All fields required'); return; }
            completeTask(taskId, 'partial', actual, reason, time, comment);
            modal.hide();
            document.getElementById('partialModal').addEventListener('hidden.bs.modal', function () { this.remove(); });
        });
    }

    function showSkipModal(taskId) {
        var html = '<div class="modal fade" id="skipModal" tabindex="-1" aria-hidden="true">' +
            '<div class="modal-dialog"><div class="modal-content">' +
            '<div class="modal-header"><h5 class="modal-title">Skip Task</h5>' +
            '<button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>' +
            '<div class="modal-body">' +
            '<div class="alert alert-warning" style="font-size:0.85rem">Skipping will result in EXP penalties.</div>' +
            '<div class="mb-3"><label class="form-label">Reason for skipping</label>' +
            '<textarea class="form-control" id="skip-reason" rows="2"></textarea></div>' +
            '</div><div class="modal-footer">' +
            '<button type="button" class="btn-app btn-app-secondary" data-bs-dismiss="modal">Cancel</button>' +
            '<button type="button" class="btn-app btn-app-danger" id="confirm-skip">Skip Task</button>' +
            '</div></div></div></div>';

        document.body.insertAdjacentHTML('beforeend', html);
        var modal = new bootstrap.Modal(document.getElementById('skipModal'));
        modal.show();

        document.getElementById('confirm-skip').addEventListener('click', function () {
            completeTask(taskId, 'skipped', null, document.getElementById('skip-reason').value, nowFormatted());
            modal.hide();
            document.getElementById('skipModal').addEventListener('hidden.bs.modal', function () { this.remove(); });
        });
    }

    // ── API: complete task ──
    async function completeTask(taskId, status, actualTime, reason, completedOn, comment) {
        var data = {
            timetable_entry_id: taskId,
            status: status,
            completed_on: completedOn,
            comment: comment || ''
        };
        if (actualTime) data.actual_time_taken = parseInt(actualTime);
        if (reason) data.reason = reason;

        try {
            var response = await fetch('/api/complete/complete_activity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (response.status !== 201) throw new Error('Status ' + response.status);
            var result = await response.json();

            var el = document.querySelector('.task-item[data-id="' + taskId + '"]');
            el.className = 'task-item ' + (status === 'completed' ? 'completed' : status === 'skipped' ? 'skipped' : 'pending');

            var actionsEl = el.querySelector('.task-actions');
            actionsEl.innerHTML = '<span class="status-badge status-' + status + '">' + status.charAt(0).toUpperCase() + status.slice(1) + '</span>';

            var expMsg = result.exp_change >= 0
                ? 'Gained <strong>' + result.exp_change + '</strong> EXP!'
                : 'Lost <strong>' + Math.abs(result.exp_change) + '</strong> EXP!';
            showNotification(result.exp_change >= 0 ? 'success' : 'danger',
                status === 'completed' ? 'Task Completed' : status === 'partial' ? 'Partial' : 'Skipped', expMsg);

            if (result.level_up) {
                setTimeout(function () {
                    showNotification('info', 'Level Up!', 'You reached level ' + result.level + '!');
                    document.querySelector('.stat-big-number').textContent = result.level;
                    document.querySelector('.stat-big-number').classList.add('pulse');
                    setTimeout(function () { document.querySelector('.stat-big-number').classList.remove('pulse'); }, 2000);
                }, 1000);
            }
            updateStats();
        } catch (err) {
            console.error(err);
            showNotification('danger', 'Error', 'Failed to update task status.');
        }
    }

    // ── API: refresh stats ──
    function updateStats() {
        fetch('/api/stats')
        .then(function (r) { return r.json(); })
        .then(function (data) {
            document.querySelector('.stat-big-number').textContent = data.user.level;
            var attrs = ['INT', 'STA', 'FCS', 'CHA', 'DSC'];
            var vals = [data.user.INT, data.user.STA, data.user.FCS, data.user.CHA, data.user.DSC];
            document.querySelectorAll('.attr-item').forEach(function (item, i) {
                item.querySelector('.attr-value').textContent = vals[i];
            });
            var dcpPct = (data.dcp * 100).toFixed(0);
            var bars = document.querySelectorAll('.progress-app .bar');
            if (bars.length > 1) {
                bars[1].style.width = dcpPct + '%';
            }
        })
        .catch(function (err) { console.error('Stats update error:', err); });
    }

    // ── Finalize Day ──
    document.getElementById('finalizeDayBtn').addEventListener('click', async function () {
        var msg = '<h6>Finalizing today will:</h6><ul>' +
            '<li>Sum all EXP from completed tasks</li>' +
            '<li>Lock today\'s schedule</li>' +
            '<li>Calculate your daily discipline factor</li>' +
            '</ul>' +
            '<div class="alert alert-warning mt-3" style="font-size:0.85rem">This action cannot be undone!</div>';

        var confirmed = await showConfirmation(msg, 'Finalize Today?');
        if (!confirmed) return;

        try {
            var today = new Date().toISOString().split('T')[0];
            var response = await fetch('/api/complete/finalize_day', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: today })
            });
            if (response.status === 200) {
                var result = await response.json();
                showNotification('success', 'Day Finalized',
                    'Total EXP: ' + result.new_total_exp + '<br>Level: ' + result.level + (result.level_up ? ' (Level Up!)' : ''));
                updateStats();
            } else {
                var error = await response.json();
                showNotification('danger', 'Error', error.msg || 'Failed to finalize');
            }
        } catch (err) {
            console.error(err);
            showNotification('danger', 'Error', 'Network error');
        }
    });
});
