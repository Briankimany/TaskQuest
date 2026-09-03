/**
 * Stats Garden RPG — attribute range toggle (7D/30D/90D).
 * Full data linkage to be wired when attribute history is tracked over time.
 */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.grpg-range-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var group = this.closest('[role="tablist"]');
      group.querySelectorAll('.grpg-range-btn').forEach(function (b) {
        b.setAttribute('aria-pressed', 'false');
      });
      this.setAttribute('aria-pressed', 'true');
    });
  });
});