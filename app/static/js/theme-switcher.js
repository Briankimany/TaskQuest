/**
 * Theme Switcher — switches between "default" and "garden-rpg" themes
 * Reads/writes localStorage 'theme' key, sets data-theme on <html>
 * Also sets a cookie so the server can read the theme preference
 */
(function () {
  var THEME_KEY = 'theme';
  var html = document.documentElement;
  var switcher = document.getElementById('themeSwitcher');
  if (!switcher) return;

  function setCookie(name, value, days) {
    var d = new Date();
    d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = name + '=' + value + ';expires=' + d.toUTCString() + ';path=/';
  }

  function getCookie(name) {
    var v = document.cookie.match('(^|;)\\s*' + name + '=([^;]*)');
    return v ? v[2] : null;
  }

  function setTheme(theme) {
    html.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    setCookie('app_theme', theme, 365);

    // Update switcher selection
    switcher.value = theme;

    // Show/hide light/dark toggle based on theme
    var lightDarkToggle = document.getElementById('themeToggle');
    if (lightDarkToggle) {
      lightDarkToggle.style.display = theme === 'default' ? '' : 'none';
    }

    // If switching to default, ensure a color scheme is set
    if (theme === 'default') {
      var scheme = localStorage.getItem('scheme') || 'light';
      html.setAttribute('data-scheme', scheme);
    }
  }

  function init() {
    var saved = localStorage.getItem(THEME_KEY) || getCookie('app_theme') || 'default';
    setTheme(saved);

    switcher.addEventListener('change', function () {
      setTheme(this.value);
      // Reload to apply theme across the app (especially for dashboard route)
      window.location.reload();
    });
  }

  init();
})();
