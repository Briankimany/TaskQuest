/**
 * Activities page — CRUD for activities and sub-activities
 */
document.addEventListener('DOMContentLoaded', function () {

    // ── Collapse / Expand (persisted per group) ──
    function groupKey(groupEl) {
        return 'activities.group.' + groupEl.getAttribute('data-group-name') + '.expanded';
    }

    function syncHeight(groupEl) {
        var body = groupEl.querySelector('.act-group-body');
        if (groupEl.classList.contains('is-expanded')) {
            body.style.maxHeight = body.scrollHeight + 'px';
        } else {
            body.style.maxHeight = '0px';
        }
    }

    function toggleGroup(groupEl) {
        var expanded = groupEl.classList.toggle('is-expanded');
        localStorage.setItem(groupKey(groupEl), expanded ? 'true' : 'false');
        groupEl.querySelector('.act-group-header').setAttribute('aria-expanded', expanded ? 'true' : 'false');
        syncHeight(groupEl);
    }

    document.querySelectorAll('.act-group').forEach(function (groupEl) {
        var header = groupEl.querySelector('.act-group-header');
        if (localStorage.getItem(groupKey(groupEl)) === 'true') {
            groupEl.classList.add('is-expanded');
            header.setAttribute('aria-expanded', 'true');
        }
        header.addEventListener('click', function (e) {
            if (e.target.closest('.actions')) return;
            toggleGroup(groupEl);
        });
        header.addEventListener('keydown', function (e) {
            if (e.target.closest('.actions')) return;
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleGroup(groupEl);
            }
        });
        syncHeight(groupEl);
    });

    // ── Create Activity ──
    document.getElementById('create-activity-btn').addEventListener('click', function () {
        var name = document.getElementById('activity-name').value.trim();
        if (!name) { showNotification('danger', 'Error', 'Activity name is required'); return; }
        if (name.length > 64) { showNotification('danger', 'Error', 'Name must be 64 characters or fewer'); return; }

        fetch('/api/activities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
            if (!res.ok) throw new Error(res.data.msg || 'Failed to create activity');
            bootstrap.Modal.getInstance(document.getElementById('newActivityModal')).hide();
            window.location.reload();
        })
        .catch(function (e) { showNotification('danger', 'Error', e.message); });
    });

    // ── Edit Activity ──
    document.querySelectorAll('.edit-activity-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('edit-activity-id').value = this.getAttribute('data-activity-id');
            document.getElementById('edit-activity-name').value = this.getAttribute('data-activity-name');
            new bootstrap.Modal(document.getElementById('editActivityModal')).show();
        });
    });

    // ── Update Activity ──
    document.getElementById('update-activity-btn').addEventListener('click', function () {
        var id = document.getElementById('edit-activity-id').value;
        var name = document.getElementById('edit-activity-name').value;
        if (!name) { showNotification('danger', 'Error', 'Activity name is required'); return; }

        fetch('/api/activity/' + id, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        })
        .then(function (r) { return r.json(); })
        .then(function () {
            bootstrap.Modal.getInstance(document.getElementById('editActivityModal')).hide();
            document.querySelector('.act-group[data-id="' + id + '"] .name').textContent = name;
            showNotification('success', 'Updated', 'Activity updated');
        })
        .catch(function () { showNotification('danger', 'Error', 'Failed to update'); });
    });

    // ── Delete Activity ──
    document.querySelectorAll('.delete-activity-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = this.getAttribute('data-activity-id');
            var name = this.closest('.act-group').querySelector('.name').textContent;
            document.getElementById('delete-item-id').value = id;
            document.getElementById('delete-item-type').value = 'activity';
            document.getElementById('delete-item-name').textContent = '"' + name + '"';
            new bootstrap.Modal(document.getElementById('deleteConfirmModal')).show();
        });
    });

    // ── Add Sub-Activity ──
    document.querySelectorAll('.add-subactivity-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('parent-activity-id').value = this.getAttribute('data-activity-id');
            new bootstrap.Modal(document.getElementById('newSubActivityModal')).show();
        });
    });

    // ── Create Sub-Activity ──
    document.getElementById('create-subactivity-btn').addEventListener('click', function () {
        var name = document.getElementById('subactivity-name').value.trim();
        var scheduledTime = parseInt(document.getElementById('scheduled-time').value);
        var baseExp = parseInt(document.getElementById('base-exp').value);
        var difficulty = parseFloat(document.getElementById('difficulty-multiplier').value);
        if (!name) { showNotification('danger', 'Error', 'Name is required'); return; }
        if (!scheduledTime || scheduledTime < 1) { showNotification('danger', 'Error', 'Scheduled time must be a positive number of minutes'); return; }
        var data = {
            activity_id: parseInt(document.getElementById('parent-activity-id').value),
            name: name,
            scheduled_time: scheduledTime,
            difficulty_multiplier: isNaN(difficulty) ? 1.0 : difficulty,
            base_exp: isNaN(baseExp) ? 100 : baseExp,
            attribute_weights: getAttributeWeights('')
        };

        fetch('/api/subactivity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
            if (!res.ok) throw new Error(res.data.msg || 'Failed to create sub-activity');
            bootstrap.Modal.getInstance(document.getElementById('newSubActivityModal')).hide();
            window.location.reload();
        })
        .catch(function (e) { showNotification('danger', 'Error', e.message); });
    });

    // ── Edit Sub-Activity ──
    document.querySelectorAll('.edit-subactivity-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var d = this.dataset;
            document.getElementById('edit-subactivity-id').value = d.id;
            document.getElementById('edit-subactivity-name').value = d.name;
            document.getElementById('edit-scheduled-time').value = d.time;
            document.getElementById('edit-difficulty-multiplier').value = d.difficulty;
            document.getElementById('edit-base-exp').value = d.exp;
            var attrs = JSON.parse(d.attributes);
            document.getElementById('edit-int-weight').value = attrs.INT || 0.2;
            document.getElementById('edit-sta-weight').value = attrs.STA || 0.2;
            document.getElementById('edit-fcs-weight').value = attrs.FCS || 0.2;
            document.getElementById('edit-cha-weight').value = attrs.CHA || 0.2;
            document.getElementById('edit-dsc-weight').value = attrs.DSC || 0.2;
            updateWeightTotal('edit-');
            new bootstrap.Modal(document.getElementById('editSubActivityModal')).show();
        });
    });

    // ── Update Sub-Activity ──
    document.getElementById('update-subactivity-btn').addEventListener('click', function () {
        var id = document.getElementById('edit-subactivity-id').value;
        var data = {
            name: document.getElementById('edit-subactivity-name').value,
            scheduled_time: parseInt(document.getElementById('edit-scheduled-time').value),
            difficulty_multiplier: parseFloat(document.getElementById('edit-difficulty-multiplier').value),
            base_exp: parseInt(document.getElementById('edit-base-exp').value),
            attribute_weights: getAttributeWeights('edit-')
        };
        if (!data.name || !data.scheduled_time) { showNotification('danger', 'Error', 'Name and time required'); return; }

        fetch('/api/subactivity/' + id, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(function (r) { return r.json(); })
        .then(function () {
            bootstrap.Modal.getInstance(document.getElementById('editSubActivityModal')).hide();
            window.location.reload();
        })
        .catch(function () { showNotification('danger', 'Error', 'Failed to update'); });
    });

    // ── Delete Sub-Activity ──
    document.querySelectorAll('.delete-subactivity-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = this.getAttribute('data-id');
            var name = this.closest('.act-row').querySelector('.name').textContent;
            document.getElementById('delete-item-id').value = id;
            document.getElementById('delete-item-type').value = 'subactivity';
            document.getElementById('delete-item-name').textContent = '"' + name + '"';
            new bootstrap.Modal(document.getElementById('deleteConfirmModal')).show();
        });
    });

    // ── Confirm Delete ──
    document.getElementById('confirm-delete-btn').addEventListener('click', function () {
        var id = document.getElementById('delete-item-id').value;
        var type = document.getElementById('delete-item-type').value;
        var url = type === 'activity' ? '/api/activity/' + id : '/api/subactivity/' + id;

        fetch(url, { method: 'DELETE' })
        .then(function (r) {
            if (!r.ok) throw new Error();
            bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal')).hide();
            if (type === 'activity') {
                document.querySelector('.act-group[data-id="' + id + '"]').remove();
            } else {
                document.querySelector('.act-row[data-id="' + id + '"]').remove();
            }
            showNotification('success', 'Deleted', type.charAt(0).toUpperCase() + type.slice(1) + ' removed');
            if (type === 'activity' && document.querySelectorAll('.act-group').length === 0) window.location.reload();
        })
        .catch(function () { showNotification('danger', 'Error', 'Failed to delete'); });
    });

    // ── Weight helpers ──
    function getAttributeWeights(prefix) {
        return {
            INT: parseFloat(document.getElementById(prefix + 'int-weight').value),
            STA: parseFloat(document.getElementById(prefix + 'sta-weight').value),
            FCS: parseFloat(document.getElementById(prefix + 'fcs-weight').value),
            CHA: parseFloat(document.getElementById(prefix + 'cha-weight').value),
            DSC: parseFloat(document.getElementById(prefix + 'dsc-weight').value)
        };
    }

    function updateWeightTotal(prefix) {
        var ids = ['int-weight', 'sta-weight', 'fcs-weight', 'cha-weight', 'dsc-weight'].map(function (id) {
            return prefix + id;
        });
        var total = ids.reduce(function (sum, id) { return sum + (parseFloat(document.getElementById(id).value) || 0); }, 0);
        var barId = prefix ? 'edit-weight-progress-bar' : 'weight-progress-bar';
        var labelId = prefix ? 'edit-weight-total' : 'weight-total';
        var bar = document.getElementById(barId);
        bar.style.width = Math.min(total * 100, 100) + '%';
        bar.className = 'bar' + (total < 0.9 || total > 1.1 ? ' bar-danger' : '');
        document.getElementById(labelId).textContent = 'Total: ' + total.toFixed(1) + ' (Recommended: 1.0)';
    }

    document.querySelectorAll('.attribute-weight').forEach(function (el) {
        el.addEventListener('input', function () { updateWeightTotal(''); });
    });
    document.querySelectorAll('.edit-attribute-weight').forEach(function (el) {
        el.addEventListener('input', function () { updateWeightTotal('edit-'); });
    });
});
