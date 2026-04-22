(function () {
    "use strict";

    var STORAGE_KEY = "darkMode";
    var DARK_CLASS = "dark-mode";
    var root = document.documentElement; // <html> element — set before first paint by inline head script

    function applyTheme(isDark) {
        if (isDark) {
            root.classList.add(DARK_CLASS);
        } else {
            root.classList.remove(DARK_CLASS);
        }
        var btn = document.getElementById("darkModeToggle");
        if (btn) {
            btn.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
            btn.textContent = isDark ? "☀️" : "🌙";
        }
    }

    function toggleDarkMode() {
        var isDark = root.classList.contains(DARK_CLASS);
        var newState = !isDark;
        localStorage.setItem(STORAGE_KEY, newState ? "enabled" : "disabled");
        applyTheme(newState);
    }

    function initDarkMode() {
        var saved = localStorage.getItem(STORAGE_KEY);
        // Default is light mode for new users (saved === null)
        var isDark = saved === "enabled";
        // Class already applied by inline head script — just sync the button icon
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
