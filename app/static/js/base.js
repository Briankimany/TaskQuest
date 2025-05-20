
// Enable Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            html: true
        });
    });
});

// Notification function
function showNotification(type, title, message, duration = 5000) {
    const container = document.getElementById('notification-container');
    const id = 'notification-' + Date.now();
    
    const html = `
        <div id="${id}" class="notification toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    
    setTimeout(() => {
        const notification = document.getElementById(id);
        if (notification) {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 500);
        }
    }, duration);
}

// Reusable confirmation function
async function showConfirmation(message, title = 'Confirm Action') {
return new Promise((resolve) => {
    // Set modal content
    document.getElementById('confirmationModalTitle').textContent = title;
    document.getElementById('confirmationModalBody').innerHTML = message;
    
    // Clear previous listeners
    const confirmBtn = document.getElementById('confirmationModalConfirm');
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    
    // Create new listener
    const handler = () => {
    modal.hide();
    resolve(true);
    };
    confirmBtn.addEventListener('click', handler, { once: true });
    
    // Show modal
    modal.show();
    
    // Handle dismissal
    document.getElementById('confirmationModal').addEventListener('hidden.bs.modal', () => {
    confirmBtn.removeEventListener('click', handler);
    resolve(false);
    }, { once: true });
});
}
