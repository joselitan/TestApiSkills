(function () {
    "use strict";

    var STORAGE_KEY = "darkMode";
    var DARK_CLASS = "dark-mode";

    function applyTheme(isDark) {
        if (isDark) {
            document.body.classList.add(DARK_CLASS);
        } else {
            document.body.classList.remove(DARK_CLASS);
        }
        var btn = document.getElementById("darkModeToggle");
        if (btn) {
            btn.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
            btn.textContent = isDark ? "☀️" : "🌙";
        }
    }

    function toggleDarkMode() {
        var isDark = document.body.classList.contains(DARK_CLASS);
        var newState = !isDark;
        localStorage.setItem(STORAGE_KEY, newState ? "enabled" : "disabled");
        applyTheme(newState);
    }

    function initDarkMode() {
        var saved = localStorage.getItem(STORAGE_KEY);
        // Default is light mode for new users (saved === null)
        var isDark = saved === "enabled";
        applyTheme(isDark);

        var btn = document.getElementById("darkModeToggle");
        if (btn) {
            btn.addEventListener("click", toggleDarkMode);
        }
    }

    // Run as soon as DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initDarkMode);
    } else {
        initDarkMode();
    }
})();
