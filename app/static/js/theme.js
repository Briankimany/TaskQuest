/**
 * Theme Manager — light/dark toggle within the default theme
 * Toggles data-scheme attribute on <html>
 * The theme-switcher.js handles switching between default/garden-rpg
 */
(function () {
  var SCHEME_KEY = 'scheme';
  var html = document.documentElement;
  var toggle = document.getElementById('themeToggle');
  if (!toggle) return;

  var iconLight = toggle.querySelector('.theme-icon-light');
  var iconDark = toggle.querySelector('.theme-icon-dark');

  function setScheme(scheme) {
    html.setAttribute('data-scheme', scheme);
    localStorage.setItem(SCHEME_KEY, scheme);
    if (scheme === 'dark') {
      iconLight.style.display = 'none';
      iconDark.style.display = '';
    } else {
      iconLight.style.display = '';
      iconDark.style.display = 'none';
    }
  }

  function init() {
    var saved = localStorage.getItem(SCHEME_KEY);
    if (saved) {
      setScheme(saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setScheme('dark');
    } else {
      setScheme('light');
    }
  }

  toggle.addEventListener('click', function () {
    var current = html.getAttribute('data-scheme') || 'light';
    setScheme(current === 'dark' ? 'light' : 'dark');
  });

  init();
})();
