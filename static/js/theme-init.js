/**
 * Early theme initializer.
 * Runs synchronously in <head> to prevent Flash of Unstyled Content (FOUC).
 */
(function () {
    function applySavedTheme() {
        if (localStorage.getItem('theme') === 'light') {
            document.documentElement.classList.add('light-mode');
        } else {
            document.documentElement.classList.remove('light-mode');
        }
    }
    applySavedTheme();
    // Ensure theme persists when navigating via browser Back/Forward cache
    window.addEventListener('pageshow', applySavedTheme);
})();

