
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            html: true
        });
    });

    // Task completion handlers
    const completeButtons = document.querySelectorAll('.complete-btn');
    const partialButtons = document.querySelectorAll('.partial-btn');
    const skipButtons = document.querySelectorAll('.skip-btn');
    
    // Function to show completion modal
    function showCompletionModal(taskId) {
        const now = new Date();
        const formattedTime = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}T${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

        const modalHtml = `
            <div class="modal fade" id="completeModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Complete Task</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="completed-on" class="form-label">Completion Time</label>
                                <input type="datetime-local" class="form-control" id="completed-on" 
                                    value="${formattedTime}" required>
                            </div>
                            <div class="mb-3">
                                <label for="complete-comment" class="form-label">Comments</label>
                                <textarea class="form-control" id="complete-comment" rows="3" required></textarea>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirm-complete">Submit</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('completeModal'));
        modal.show();

        document.getElementById('confirm-complete').addEventListener('click', function() {
            const completedOn = document.getElementById('completed-on').value;
            const comment = document.getElementById('complete-comment').value;

            if (!completedOn || !comment) {
                alert('Both fields are required');
                return;
            }

            completeTask(taskId, 'completed', null,null,completedOn,comment);
            modal.hide();
            
            document.getElementById('completeModal').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
        });
    }

    // Updated event listeners
    completeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const taskId = this.getAttribute('data-id');
            showCompletionModal(taskId);
        });
    });

    
    partialButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const taskId = this.getAttribute('data-id');
            showPartialCompletionModal(taskId);
        });
    });
    
    skipButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const taskId = this.getAttribute('data-id');
            showSkipModal(taskId);
        });
    });
    
    // Completion modal
    function showPartialCompletionModal(taskId) {
        // Create modal for partial completion time input
        const now = new Date();
        const formattedTime = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}T${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

        const modalHtml = `
            <div class="modal fade" id="partialModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Partial Completion</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="completed-on" class="form-label">Completion Time</label>
                                <input type="datetime-local" class="form-control" id="completed-on" 
                                    value="${formattedTime}" required>
                            </div>
                            <div class="mb-3">
                                <label for="actual-time" class="form-label">Time Spent (minutes)</label>
                                <input type="number" class="form-control" id="actual-time" min="1" required>
                            </div>
                            <div class="mb-3">
                                <label for="reason" class="form-label">Reason</label>
                                <textarea class="form-control" id="reason" rows="3"></textarea>
                            </div>
                            <div class="mb-3">
                                <label for="comment" class="form-label">Comments</label>
                                <textarea class="form-control" id="comment" rows="3"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="confirm-partial">Submit</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            const modal = new bootstrap.Modal(document.getElementById('partialModal'));
            modal.show();
            
            document.getElementById('confirm-partial').addEventListener('click', function() {
                const completedOn = document.getElementById('completed-on').value;
                const actualTime = document.getElementById('actual-time').value;
                const comment = document.getElementById('comment').value;
                const reason = document.getElementById('reason').value;

                if (!completedOn || !actualTime || !reason) {
                    alert('All fields are required');
                    return;
                }

                completeTask(taskId, 'partial', actualTime, reason, completedOn,comment);
                modal.hide();
                
                document.getElementById('partialModal').addEventListener('hidden.bs.modal', function() {
                    this.remove();
            });
        });
    }

    
    function showSkipModal(taskId) {
        // Create modal for skip reason
        const modalHtml = `
            <div class="modal fade" id="skipModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Skip Task</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle"></i> Skipping will result in EXP penalties.
                            </div>
                            <div class="mb-3">
                                <label for="skip-reason" class="form-label">Reason for skipping</label>
                                <textarea class="form-control" id="skip-reason" rows="2"></textarea>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-danger" id="confirm-skip">Skip Task</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = new bootstrap.Modal(document.getElementById('skipModal'));
        modal.show();
        const now = new Date();
        const formattedTime = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}T${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

        document.getElementById('confirm-skip').addEventListener('click', function() {
            const reason = document.getElementById('skip-reason').value;
            completeTask(taskId, 'skipped', null, reason,completedOn=formattedTime);
            modal.hide();
            
            // Remove the modal from DOM after hiding
            document.getElementById('skipModal').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
        });
    }
    
    async function completeTask(taskId, status, actualTime = null, reason = null,completedOn=null,comment=null) {

    const data = {
        timetable_entry_id: taskId,
        status: status,
        completed_on: completedOn,
        comment:comment
    };
    
    if (actualTime) {
        data.actual_time_taken = parseInt(actualTime);
    }
    
    if (reason) {
        data.reason = reason;
    }
    
    try {
        const response = await fetch('/api/complete/complete_activity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        // Only proceed if we get a 201 (Created) response
        if (response.status !== 201) {
            throw new Error(`Server responded with status ${response.status}`);
        }

        const responseData = await response.json();
 
        
        // Update UI to reflect completion
        const taskElement = document.querySelector(`.scheduled-task[data-id="${taskId}"]`);
        
        if (status === 'completed') {
            taskElement.classList.remove('pending', 'overdue');
            taskElement.classList.add('completed');
        } else if (status === 'partial') {
            taskElement.classList.remove('pending', 'overdue');
            taskElement.classList.add('pending');  // Use a different class if you have one for partial
        } else {
            taskElement.classList.remove('pending', 'completed');
            taskElement.classList.add('overdue');
        }
        
        // Update buttons
        const buttonsContainer = taskElement.querySelector('div > div:last-child');
        buttonsContainer.innerHTML = `
            <span class="badge bg-${status === 'completed' ? 'success' : (status === 'partial' ? 'warning' : 'danger')}">
                ${status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        `;
        
        // Show notification for EXP gain/loss
        const expChange = responseData.exp_change;
        const expMessage = expChange >= 0 ? 
            `Gained <strong>${expChange}</strong> EXP!` : 
            `Lost <strong>${Math.abs(expChange)}</strong> EXP!`;
        
        const notificationType = expChange >= 0 ? 'success' : 'danger';
        const notificationTitle = status === 'completed' ? 'Task Completed!' : 
                                 (status === 'partial' ? 'Partial Completion' : 'Task Skipped');
        
        showNotification(notificationType, notificationTitle, expMessage);
        
        // Handle level up
        if (responseData.level_up) {
            setTimeout(() => {
                showNotification('warning', 'Level Up!', `You've reached level ${responseData.level}!`, 10000);
                
                // Add animation to level display
                const levelElement = document.querySelector('h2.mb-0');
                levelElement.textContent = `Level ${responseData.level}`;
                levelElement.classList.add('pulse');
                setTimeout(() => {
                    levelElement.classList.remove('pulse');
                }, 2000);
            }, 1000);
        }
        
        // Update stats display
        updateStats();

    } catch (error) {
        console.error('Error:', error);
        showNotification('danger', 'Error', 'Failed to update task status. Please try again.');
    }
}
    // Function to update stats via API
    function updateStats() {
        fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Update level and EXP
            document.querySelector('h2.mb-0').textContent = `Level ${data.user.level}`;
            
            // Update attributes
            document.querySelector('.col-6:nth-child(1)').innerHTML = `
                <span class="attribute-badge INT-bg" data-bs-toggle="tooltip" title="Intelligence: Affects learning and cognitive tasks">INT</span>
                ${data.user.INT}
            `;
            document.querySelector('.col-6:nth-child(2)').innerHTML = `
                <span class="attribute-badge STA-bg" data-bs-toggle="tooltip" title="Stamina: Affects physical endurance and health">STA</span>
                ${data.user.STA}
            `;
            document.querySelector('.col-6:nth-child(3)').innerHTML = `
                <span class="attribute-badge FCS-bg" data-bs-toggle="tooltip" title="Focus: Affects concentration and attention to detail">FCS</span>
                ${data.user.FCS}
            `;
            document.querySelector('.col-6:nth-child(4)').innerHTML = `
                <span class="attribute-badge CHA-bg" data-bs-toggle="tooltip" title="Charisma: Affects social skills and interactions">CHA</span>
                ${data.user.CHA}
            `;
            document.querySelector('.col-6:nth-child(5)').innerHTML = `
                <span class="attribute-badge DSC-bg" data-bs-toggle="tooltip" title="Discipline: Affects consistency and habit formation">DSC</span>
                ${data.user.DSC}
            `;
            
            // Update discipline factor
            const dcpPercentage = (data.dcp * 100).toFixed(0);
            const progressBar = document.querySelector('.progress-bar.bg-info');
            progressBar.style.width = `${dcpPercentage}%`;
            progressBar.textContent = `${dcpPercentage}%`;
            
            // Reinitialize tooltips
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl, {
                    html: true
                });
            });
        })
        .catch(error => {
            console.error('Error updating stats:', error);
        });
    }

    function showNotification(type, title, message, duration=5000) {
        const notification = document.createElement('div');
        notification.className = `toast align-items-center text-white bg-${type} border-0 position-fixed top-0 end-0 m-3`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');
        notification.setAttribute('aria-atomic', 'true');
        notification.style.zIndex = '99999';

        notification.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        const toast = new bootstrap.Toast(notification, {
            autohide: true,
            delay: duration
        });
        toast.show();
        
        notification.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    }

    const finalizeDayBtn = document.getElementById('finalizeDayBtn');
    
    finalizeDayBtn.addEventListener('click', async function() {
        const confirmationMessage = `
          <h6>Finalizing today will:</h6>
          <ul>
            <li>Sum all EXP gained from completed tasks</li>
            <li>Lock today's schedule (no modifications allowed)</li>
            <li>Calculate your daily discipline factor</li>
            <li>Check for level progression</li>
          </ul>
          <div class="alert alert-warning mt-3">
            <i class="fas fa-exclamation-triangle me-2"></i>
            This action cannot be undone!
          </div>
        `;
        
        const confirmed = await showConfirmation(confirmationMessage, 'Finalize Today?');
        if (!confirmed) return;
        
        // Proceed with finalization
        try {
          const today = new Date().toISOString().split('T')[0];
          const response = await fetch('/api/completiuhe/finalize_day', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date: today })
          });
          
          if (response.status === 200) {
            const result = await response.json();
            showNotification('success', 'Day Finalized!', `
              Total EXP: ${result.new_total_exp}<br>
              Level: ${result.level}${result.level_up ? ' (Level Up!)' : ''}
            `);
            updateStats();
          } else {
            const error = await response.json();
            showNotification('danger', 'Error', error.msg || 'Failed to finalize day');
          }
        } catch (error) {
          console.error('Error:', error);
          showNotification('danger', 'Error', 'Network error - please try again');
        }
      });
  });


