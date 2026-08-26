/**
 * Activities page — CRUD for activities and sub-activities
 */
document.addEventListener('DOMContentLoaded', function () {

    // ── Create Activity ──
    document.getElementById('create-activity-btn').addEventListener('click', function () {
        var name = document.getElementById('activity-name').value;
        if (!name) { showNotification('danger', 'Error', 'Activity name is required'); return; }

        fetch('/api/activities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        })
        .then(function (r) { return r.json(); })
        .then(function () {
            bootstrap.Modal.getInstance(document.getElementById('newActivityModal')).hide();
            window.location.reload();
        })
        .catch(function () { showNotification('danger', 'Error', 'Failed to create activity'); });
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
            document.querySelector('.activity-card[data-id="' + id + '"] .activity-name').textContent = name;
            showNotification('success', 'Updated', 'Activity updated');
        })
        .catch(function () { showNotification('danger', 'Error', 'Failed to update'); });
    });

    // ── Delete Activity ──
    document.querySelectorAll('.delete-activity-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = this.getAttribute('data-activity-id');
            var name = this.closest('.app-card').querySelector('.activity-name').textContent;
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
        var data = {
            activity_id: parseInt(document.getElementById('parent-activity-id').value),
            name: document.getElementById('subactivity-name').value,
            scheduled_time: parseInt(document.getElementById('scheduled-time').value),
            difficulty_multiplier: parseFloat(document.getElementById('difficulty-multiplier').value),
            base_exp: parseInt(document.getElementById('base-exp').value),
            attribute_weights: getAttributeWeights('')
        };
        if (!data.name || !data.scheduled_time) { showNotification('danger', 'Error', 'Name and time required'); return; }

        fetch('/api/subactivity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(function (r) { return r.json(); })
        .then(function () {
            bootstrap.Modal.getInstance(document.getElementById('newSubActivityModal')).hide();
            window.location.reload();
        })
        .catch(function () { showNotification('danger', 'Error', 'Failed to create sub-activity'); });
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
            updateWeightTotal('edit');
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
            var name = this.closest('tr').querySelector('td:first-child').textContent;
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
                document.querySelector('.activity-card[data-id="' + id + '"]').remove();
            } else {
                document.querySelector('tr[data-id="' + id + '"]').remove();
            }
            showNotification('success', 'Deleted', type.charAt(0).toUpperCase() + type.slice(1) + ' removed');
            if (type === 'activity' && document.querySelectorAll('.activity-card').length === 0) window.location.reload();
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
