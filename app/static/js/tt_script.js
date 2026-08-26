/**
 * Timetable — TaskScheduler class for CRUD on timetables
 */
class TaskScheduler {
    constructor() {
        this.currentDate = new Date();
        this.initElements();
        this.initEventListeners();
        this.loadTimetable();
        this.loadSuggestedTasks();
    }

    initElements() {
        this.elements = {
            datePicker: document.getElementById('date-picker'),
            taskGrid: document.getElementById('task-grid'),
            addTaskBtn: document.getElementById('add-task-btn'),
            newDayBtn: document.getElementById('new-day-btn'),
            taskModal: document.getElementById('task-modal'),
            taskForm: document.getElementById('task-form'),
            modalTitle: document.getElementById('modal-title'),
            cancelBtn: document.getElementById('cancel-btn'),
            description: document.getElementById('task-description'),
            activitySelect: document.getElementById('activity-select'),
            subActivitySelect: document.getElementById('sub-activity'),
            startTime: document.getElementById('start-time'),
            duration: document.getElementById('duration'),
            isCyclic: document.getElementById('is-cyclic'),
            weekdayGroup: document.getElementById('weekday-group'),
            weekday: document.getElementById('weekday'),
            addBuffer: document.getElementById('add-buffer')
        };
    }

    initEventListeners() {
        this.elements.datePicker.addEventListener('change', (e) => {
            this.currentDate = new Date(e.target.value);
            this.loadTimetable();
        });
        this.elements.newDayBtn.addEventListener('click', () => this.createTimetable());
        this.elements.addTaskBtn.addEventListener('click', () => this.openTaskModal());
        this.elements.cancelBtn.addEventListener('click', () => this.closeModal());
        this.elements.taskForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        this.elements.isCyclic.addEventListener('change', () => {
            this.elements.weekdayGroup.style.display =
                this.elements.isCyclic.checked ? 'block' : 'none';
        });
    }

    async loadTimetable() {
        try {
            var dateStr = this.formatDate(this.currentDate);
            this.elements.datePicker.value = dateStr;
            var response = await fetch('/api/timetable/info/' + dateStr + '?days=1');
            if (!response.ok) throw new Error('Failed to load timetable');
            var data = await response.json();
            this.renderTasks(data.schedule[dateStr] || []);
        } catch (error) {
            showNotification('danger', 'Error', error.message);
        }
    }

    renderTasks(tasks) {
        this.elements.taskGrid.innerHTML = '';
        tasks.forEach(task => {
            var card = document.createElement('div');
            card.className = 'task-card';
            card.dataset.taskId = task.id;
            var startTime = task.start_time.substring(0, 5);
            var endTime = task.end_time.substring(0, 5);
            card.innerHTML =
                '<div class="task-header"><h3>' + task.activity_name + '</h3>' +
                '<span class="task-time">' + startTime + ' - ' + endTime + '</span></div>' +
                (task.base_exp ? '<p style="font-size:0.85rem;color:var(--text-muted)">EXP: ' + task.base_exp + '</p>' : '') +
                '<div class="task-actions">' +
                '<button class="btn-app btn-app-secondary btn-app-sm edit-btn">Edit</button>' +
                '<button class="btn-app btn-app-danger btn-app-sm delete-btn">Delete</button></div>';
            card.querySelector('.edit-btn').addEventListener('click', () => this.openEditModal(task));
            card.querySelector('.delete-btn').addEventListener('click', () => this.deleteTask(task.id));
            this.elements.taskGrid.appendChild(card);
        });
    }

    async loadSuggestedTasks() {
        try {
            var response = await fetch('/api/timetable/scheduling/tasks');
            if (!response.ok) throw new Error('Failed to load tasks');
            var data = await response.json();
            var activities = [...data.suggested_activities, ...data.new_activities];
            this.populateActivityDropdown(activities, true);
            this.populateSubActivityDropdown(data.suggested_sub_activities);
            if (activities.length > 0) {
                this.elements.activitySelect.value = activities[0].id;
                await this.loadSubActivities(activities[0].id);
            }
            this.elements.activitySelect.addEventListener('change', (e) => this.loadSubActivities(e.target.value));
        } catch (error) {
            showNotification('danger', 'Error', error.message);
        }
    }

    populateActivityDropdown(activities, clear) {
        if (clear) this.elements.activitySelect.innerHTML = '';
        activities.forEach(function (a) {
            var opt = document.createElement('option');
            opt.value = a.id;
            opt.textContent = a.name;
            this.elements.activitySelect.appendChild(opt);
        }.bind(this));
    }

    populateSubActivityDropdown(subActivities) {
        this.elements.subActivitySelect.innerHTML = '';
        subActivities.forEach(function (sa) {
            var opt = document.createElement('option');
            opt.value = sa.id;
            opt.textContent = sa.name;
            this.elements.subActivitySelect.appendChild(opt);
        }.bind(this));
    }

    async loadSubActivities(activityId) {
        try {
            var response = await fetch('/api/activities?id=' + activityId);
            if (!response.ok) throw new Error('Failed to load sub-activities');
            var data = await response.json();
            var all = [];
            data.activities.forEach(function (sub) { all.push(sub.sub_activities); });
            this.populateSubActivityDropdown(all.flat());
        } catch (error) {
            showNotification('danger', 'Error', error.message);
        }
    }

    openTaskModal(task) {
        this.elements.modalTitle.textContent = task ? 'Edit Task' : 'Add New Task';
        this.elements.taskForm.dataset.taskId = task ? task.id : '';
        if (task) {
            this.elements.subActivitySelect.value = task.sub_activity_id || '';
            this.elements.startTime.value = task.start_time.substring(0, 5);
            this.elements.duration.value = task.task_duration || '';
            if (task.cyclic) {
                this.elements.isCyclic.checked = true;
                this.elements.weekdayGroup.style.display = 'block';
                this.elements.weekday.value = task.weekday || 1;
            } else {
                this.elements.isCyclic.checked = false;
                this.elements.weekdayGroup.style.display = 'none';
            }
        } else {
            this.elements.taskForm.reset();
            this.elements.weekdayGroup.style.display = 'none';
        }
        this.elements.taskModal.style.display = 'flex';
    }

    openEditModal(task) {
        this.elements.modalTitle.textContent = 'Edit Task';
        this.elements.taskForm.dataset.taskId = task.id;
        this.elements.subActivitySelect.value = task.sub_activity_id || '';
        this.elements.startTime.value = task.start_time.substring(0, 5);
        if (!task.task_duration && task.start_time && task.end_time) {
            var start = new Date('2000-01-01T' + task.start_time);
            var end = new Date('2000-01-01T' + task.end_time);
            this.elements.duration.value = Math.round((end - start) / 60000);
        } else {
            this.elements.duration.value = task.task_duration || '';
        }
        if (task.cyclic) {
            this.elements.isCyclic.checked = true;
            this.elements.weekdayGroup.style.display = 'block';
            this.elements.weekday.value = task.weekday || this.getWeekdayFromDate(this.currentDate);
        } else {
            this.elements.isCyclic.checked = false;
            this.elements.weekdayGroup.style.display = 'none';
        }
        this.elements.taskModal.style.display = 'flex';
    }

    closeModal() {
        this.elements.taskModal.style.display = 'none';
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        var taskData = {
            sub_activity_id: parseInt(this.elements.subActivitySelect.value),
            date: this.formatDate(this.currentDate),
            start_time: this.elements.startTime.value,
            time_zone: 'Africa/Nairobi',
            task_duration: this.elements.duration.value ? parseInt(this.elements.duration.value) : null,
            cyclic: this.elements.isCyclic.checked,
            weekday: this.elements.isCyclic.checked ? parseInt(this.elements.weekday.value) : null,
            create_buffer: this.elements.addBuffer.checked,
            description: this.elements.description.value
        };
        try {
            if (this.elements.taskForm.dataset.taskId) {
                await this.updateTask(this.elements.taskForm.dataset.taskId, taskData);
            } else {
                await this.createTask(taskData);
            }
            this.closeModal();
            this.loadTimetable();
            showNotification('success', 'Saved', 'Task saved successfully');
        } catch (error) {
            showNotification('danger', 'Error', error.message);
        }
    }

    async createTimetable() {
        try {
            var dateStr = this.formatDate(this.currentDate);
            var response = await fetch('/api/timetable/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: dateStr })
            });
            if (!response.ok) { var err = await response.json(); throw new Error(err.msg); }
            this.loadTimetable();
            showNotification('success', 'Created', 'New timetable created');
        } catch (error) {
            showNotification('danger', 'Error', error.message);
        }
    }

    async createTask(taskData) {
        var response = await fetch('/api/timetable/task', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        if (!response.ok) { var err = await response.json(); throw new Error(err.msg); }
    }

    async updateTask(taskId, taskData) {
        var response = await fetch('/api/timetable/task/' + taskId, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        if (!response.ok) { var err = await response.json(); throw new Error(err.msg); }
    }

    async deleteTask(taskId) {
        var confirmed = await showConfirmation('Delete this task?', 'Delete Task');
        if (!confirmed) return;
        try {
            var response = await fetch('/api/timetable/task/' + taskId, { method: 'DELETE' });
            if (!response.ok) { var err = await response.json(); throw new Error(err.msg); }
            this.loadTimetable();
            showNotification('success', 'Deleted', 'Task removed');
        } catch (error) {
            showNotification('danger', 'Error', error.message);
        }
    }

    getWeekdayFromDate(date) {
        var day = date.getDay();
        return day === 0 ? 7 : day;
    }

    formatDate(date) {
        return date.toISOString().split('T')[0];
    }
}

document.addEventListener('DOMContentLoaded', function () {
    new TaskScheduler();
});
