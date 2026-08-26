/**
 * Theme Manager — light/dark toggle via data-theme attribute
 * Persists preference in localStorage
 */
(function () {
  const STORAGE_KEY = 'app-theme';
  const html = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const iconLight = toggle.querySelector('.theme-icon-light');
  const iconDark = toggle.querySelector('.theme-icon-dark');

  function setTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    if (theme === 'dark') {
      iconLight.style.display = 'none';
      iconDark.style.display = '';
    } else {
      iconLight.style.display = '';
      iconDark.style.display = 'none';
    }
  }

  function init() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      setTheme(saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    } else {
      setTheme('light');
    }
  }

  toggle.addEventListener('click', function () {
    const current = html.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
  });

  init();
})();
