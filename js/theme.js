/**
 * Plateforme Technico-Commercial - Gestion Thème (Mode Clair / Mode Sombre)
 * Bouton Pill : [ ☀️ Mode ] / [ 🌙 Mode ]
 */

(function () {
  try {
    var savedTheme = localStorage.getItem('technico_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
  } catch (e) {
    console.warn('Erreur initialisation theme:', e);
  }
})();

function getAppTheme() {
  return document.documentElement.getAttribute('data-theme') || localStorage.getItem('technico_theme') || 'light';
}

function updateThemeToggleButtons(theme) {
  var btns = document.querySelectorAll('.theme-toggle-pill');
  btns.forEach(function (btn) {
    var iconSpan = btn.querySelector('.theme-icon') || btn.querySelector('#themeToggleIcon');
    var textSpan = btn.querySelector('.theme-label') || btn.querySelector('#themeToggleText');

    if (theme === 'dark') {
      if (iconSpan) iconSpan.textContent = '☀️';
      if (textSpan) textSpan.textContent = 'Mode';
      btn.setAttribute('title', 'Actuellement en Mode Sombre. Cliquer pour passer en Mode Clair');
      btn.classList.add('theme-dark-active');
    } else {
      if (iconSpan) iconSpan.textContent = '🌙';
      if (textSpan) textSpan.textContent = 'Mode';
      btn.setAttribute('title', 'Actuellement en Mode Clair. Cliquer pour passer en Mode Sombre');
      btn.classList.remove('theme-dark-active');
    }
  });
}

function toggleAppTheme() {
  var currentTheme = getAppTheme();
  var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  try {
    localStorage.setItem('technico_theme', newTheme);
  } catch (e) {
    console.warn('Impossible de sauvegarder le thème dans localStorage:', e);
  }
  updateThemeToggleButtons(newTheme);
}

// Initialisation dès que le DOM est prêt
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function () {
    updateThemeToggleButtons(getAppTheme());
  });
} else {
  updateThemeToggleButtons(getAppTheme());
}

// Synchronisation multi-onglets
window.addEventListener('storage', function (e) {
  if (e.key === 'technico_theme' && e.newValue) {
    document.documentElement.setAttribute('data-theme', e.newValue);
    updateThemeToggleButtons(e.newValue);
  }
});

