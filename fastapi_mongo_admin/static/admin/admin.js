(function () {
  "use strict";

  var COOKIE_MAX_AGE = 60 * 60 * 24 * 365;
  var html = document.documentElement;

  function setCookie(name, value) {
    document.cookie =
      name + "=" + encodeURIComponent(value) +
      ";path=/;max-age=" + COOKIE_MAX_AGE + ";SameSite=Lax";
  }

  function applyTheme(theme) {
    if (theme !== "light" && theme !== "dark") {
      return;
    }
    html.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("admin_theme", theme);
    } catch (e) {
      /* ignore */
    }
    setCookie("admin_theme", theme);
  }

  function initTheme() {
    var stored = null;
    try {
      stored = localStorage.getItem("admin_theme");
    } catch (e) {
      /* ignore */
    }
    var serverTheme = html.getAttribute("data-theme") || "light";
    if (stored && (stored === "light" || stored === "dark") && stored !== serverTheme) {
      applyTheme(stored);
    }
  }

  function initThemeToggle() {
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) {
      return;
    }
    toggle.addEventListener("click", function () {
      var current = html.getAttribute("data-theme") || "light";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }

  function initFiltersPanel() {
    var details = document.querySelector(".filters-details");
    if (!details) {
      return;
    }
    if (window.matchMedia("(max-width: 768px)").matches) {
      details.removeAttribute("open");
    }
  }

  initTheme();
  document.addEventListener("DOMContentLoaded", function () {
    initThemeToggle();
    initFiltersPanel();
  });
})();
