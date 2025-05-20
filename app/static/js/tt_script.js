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
        themeSwitcher: document.getElementById('theme-switcher'),
        
        // Modal elements
        taskModal: document.getElementById('task-modal'),
        taskForm: document.getElementById('task-form'),
        modalTitle: document.getElementById('modal-title'),
        cancelBtn: document.getElementById('cancel-btn'),
        
        // Form elements
        description:document.getElementById('task-description'),
        taskId: document.getElementById('task-id'),
        activitySelect: document.getElementById('activity-select'), // New element
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
      // Date navigation
      this.elements.datePicker.addEventListener('change', (e) => {
        this.currentDate = new Date(e.target.value);
        this.loadTimetable();
      });
      
      // New day
      this.elements.newDayBtn.addEventListener('click', () => this.createTimetable());
      
      // Add task
      this.elements.addTaskBtn.addEventListener('click', () => this.openTaskModal());

      
      // Modal actions
      this.elements.cancelBtn.addEventListener('click', () => this.closeModal());
      this.elements.taskForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
      
      // Cyclic checkbox
      this.elements.isCyclic.addEventListener('change', () => {
        this.elements.weekdayGroup.style.display = 
          this.elements.isCyclic.checked ? 'block' : 'none';
      });
    }
  
    async loadTimetable() {
      try {
        const dateStr = this.formatDate(this.currentDate);
        this.elements.datePicker.value = dateStr;
        
        const response = await fetch(`/api/timetable/info/${dateStr}?days=1`);
        if (!response.ok) throw new Error('Failed to load timetable');
        
        const data = await response.json();
  
        this.renderTasks(data.schedule[dateStr] || []);
      } catch (error) {
        showNotification(error.msg, 'error');
      }
    }
  
    renderTasks(tasks) {
      this.elements.taskGrid.innerHTML = '';
      
      tasks.forEach(task => {
        const taskCard = document.createElement('div');
        taskCard.className = 'task-card';
        taskCard.dataset.taskId = task.id;
        
        const startTime = task.start_time.substring(0, 5);
        const endTime = task.end_time.substring(0, 5);
        
        taskCard.innerHTML = `
          <div class="task-header">
            <h3>${task.activity_name}</h3>
            <span class="task-time">${startTime} - ${endTime}</span>
          </div>
          ${task.base_exp ? `<p>EXP: ${task.base_exp}</p>` : ''}
          <div class="task-actions">
            <button class="btn btn-secondary edit-btn">Edit</button>
            <button class="btn btn-danger delete-btn">Delete</button>
          </div>
        `;
        
        taskCard.querySelector('.edit-btn').addEventListener('click', () => this.openEditModal(task));
        taskCard.querySelector('.delete-btn').addEventListener('click', () => this.deleteTask(task.id));
        
        this.elements.taskGrid.appendChild(taskCard);
      });
    }
  
    async loadSuggestedTasks() {
      try {
        const response = await fetch('/api/timetable/scheduling/tasks');
        if (!response.ok) throw new Error('Failed to load suggested tasks');
        
        const data = await response.json();
      
    
  
        const activities = [...data.suggested_activities, ...data.new_activities];
        this.populateActivityDropdown(activities ,true);
    
   
        this.populateSubActivityDropdown(data.suggested_sub_activities);
    
       
        if (activities.length > 0) {
          this.elements.activitySelect.value = activities[0].id;
          await this.loadSubActivities(activities[0].id);
        }
    
      
        this.elements.activitySelect.addEventListener('change', (e) => this.loadSubActivities(e.target.value));
      } catch (error) {

        showNotification(error.msg, 'error');
      }
    }
  
  
    populateActivityDropdown(activities,create_blank_element=false) {
      if (create_blank_element){
        this.elements.activitySelect.innerHTML = '';
      }

      activities.forEach(activity => {
        const option = document.createElement('option');
        option.value = activity.id;
        option.textContent = activity.name;
        this.elements.activitySelect.appendChild(option);
      });
    }
  
    populateSubActivityDropdown(subActivities) {
      this.elements.subActivitySelect.innerHTML = '';
      
      subActivities.forEach(subActivity => {
        const option = document.createElement('option');
        option.value = subActivity.id;
        option.textContent = subActivity.name;
        this.elements.subActivitySelect.appendChild(option);
      });
    }


    async loadSubActivities(activityId) {
      try {
        const response = await fetch(`/api/activities?id=${activityId}`);
        if (!response.ok) throw new Error('Failed to load sub-activities');
        
        const data = await response.json();
      
        let allSubActivities = []; 

        data.activities.forEach(sub => {
          allSubActivities.push(sub.sub_activities); 
        });
        
        this.populateSubActivityDropdown(allSubActivities.flat());
      } catch (error) {
        showNotification(error.msg, 'error');
      }
    }
  
    openTaskModal(task = null) {
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
  
    closeModal() {
      this.elements.taskModal.style.display = 'none';
    }
    openEditModal(task) {
        this.elements.modalTitle.textContent = 'Edit Task';
        this.elements.taskForm.dataset.taskId = task.id;
        
        // Populate form with task data
        this.elements.subActivitySelect.value = task.sub_activity_id || '';
        this.elements.startTime.value = task.start_time.substring(0, 5);
        
        // Calculate duration from start/end times if not provided
        if (!task.task_duration && task.start_time && task.end_time) {
          const start = new Date(`2000-01-01T${task.start_time}`);
          const end = new Date(`2000-01-01T${task.end_time}`);
          this.elements.duration.value = Math.round((end - start) / (1000 * 60));
        } else {
          this.elements.duration.value = task.task_duration || '';
        }
        
        // Handle cyclic tasks
        if (task.cyclic) {
          this.elements.isCyclic.checked = true;
          this.elements.weekdayGroup.style.display = 'block';
          this.elements.weekday.value = task.weekday || 
            this.getWeekdayFromDate(this.currentDate);
        } else {
          this.elements.isCyclic.checked = false;
          this.elements.weekdayGroup.style.display = 'none';
        }
        
        // Open modal
        this.elements.taskModal.style.display = 'flex';
      }
    
    
    async handleFormSubmit(e) {
      e.preventDefault();
      
      const taskData = {
        sub_activity_id: parseInt(this.elements.subActivitySelect.value),
        date: this.formatDate(this.currentDate),
        start_time: this.elements.startTime.value,
        time_zone: "Africa/Nairobi",
        task_duration: this.elements.duration.value ? parseInt(this.elements.duration.value) : null,
        cyclic: this.elements.isCyclic.checked,
        weekday: this.elements.isCyclic.checked ? parseInt(this.elements.weekday.value) : null,
        create_buffer: this.elements.addBuffer.checked,
        description : this.elements.description.value,
      };
      
      try {
        if (this.elements.taskForm.dataset.taskId) {
          await this.updateTask(this.elements.taskForm.dataset.taskId, taskData);
        } else {
          await this.createTask(taskData);
        }
        
        this.closeModal();
        this.loadTimetable();
        showNotification('success','Saved','Task saved successfully');
      } catch (error) {
   
        showNotification('error', 'Error', error.message);
      }
    }
  
    async createTimetable() {
      try {
        const dateStr = this.formatDate(this.currentDate);
        const response = await fetch('/api/timetable/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ date: dateStr })
        });
        
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.msg);
        }
        
        this.loadTimetable();
        showNotification('success','Created','New timetable created');
      } catch (error) {
        showNotification('error', 'Error', error.message);
      }
    }
  
    async createTask(taskData) {
      const response = await fetch('/api/timetable/task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.msg);
      }
    }
  
    async updateTask(taskId, taskData) {
      const response = await fetch(`/api/timetable/task/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.msg);
      }
    }
  
    async deleteTask(taskId) {
      // const confirmed1 = await showConfirmation('Are you sure you want to delete this task?', 'Delete Task?');
      // get user confirmation

      const confirmed = confirm("Are you sure you want to delete this task?","Delete task");
      
      if (!confirmed) return;
      
      try {
        const response = await fetch(`/api/timetable/task/${taskId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          const error = await response.json();

          throw new Error(error.msg);
        }
        
        this.loadTimetable();
        showNotification('success','Delted','Task deleted');
      } catch (error) {
        showNotification('error', 'Error', error.message);
     
      }
    }
  
    formatDate(date) {
      return date.toISOString().split('T')[0];
    }
  
  }
  
  // Initialize the app
  document.addEventListener('DOMContentLoaded', () => {
    new TaskScheduler();
  });