/**
 * Base utilities — tooltips, notifications, confirmation modal
 * No jQuery dependency
 */
document.addEventListener('DOMContentLoaded', function () {

  // ── Bootstrap Tooltips ──
  var tooltipTriggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggers.forEach(function (el) {
    new bootstrap.Tooltip(el, { html: true });
  });

});

/**
 * Show a toast notification
 * @param {'success'|'danger'|'warning'|'info'} type
 * @param {string} title
 * @param {string} message — supports HTML
 * @param {number} duration — ms, default 5000
 */
function showNotification(type, title, message, duration) {
  if (duration === undefined) duration = 5000;
  var container = document.getElementById('notification-container');
  var id = 'notif-' + Date.now();

  var icons = {
    success: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
    danger: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
    warning: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    info: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
  };

  var html = '<div id="' + id + '" class="notification ' + type + '">' +
    '<div class="notification-icon">' + (icons[type] || icons.info) + '</div>' +
    '<div class="notification-content">' +
      '<div class="notification-title">' + title + '</div>' +
      '<div class="notification-message">' + message + '</div>' +
    '</div>' +
    '<button class="notification-close" onclick="this.parentElement.remove()" aria-label="Close">&times;</button>' +
  '</div>';

  container.insertAdjacentHTML('beforeend', html);

  setTimeout(function () {
    var el = document.getElementById(id);
    if (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateX(20px)';
      el.style.transition = '0.3s ease';
      setTimeout(function () { el.remove(); }, 300);
    }
  }, duration);
}

/**
 * Show confirmation modal
 * @param {string} message — supports HTML
 * @param {string} title
 * @returns {Promise<boolean>}
 */
async function showConfirmation(message, title) {
  if (title === undefined) title = 'Confirm Action';
  return new Promise(function (resolve) {
    document.getElementById('confirmationModalTitle').textContent = title;
    document.getElementById('confirmationModalBody').innerHTML = message;

    var confirmBtn = document.getElementById('confirmationModalConfirm');
    var modalEl = document.getElementById('confirmationModal');
    var modal = new bootstrap.Modal(modalEl);

    function onConfirm() {
      modal.hide();
      cleanup();
      resolve(true);
    }

    function onDismiss() {
      cleanup();
      resolve(false);
    }

    function cleanup() {
      confirmBtn.removeEventListener('click', onConfirm);
      modalEl.removeEventListener('hidden.bs.modal', onDismiss);
    }

    confirmBtn.addEventListener('click', onConfirm);
    modalEl.addEventListener('hidden.bs.modal', onDismiss, { once: true });

    modal.show();
  });
}
