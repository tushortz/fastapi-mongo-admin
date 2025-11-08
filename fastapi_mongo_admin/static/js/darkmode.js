// Dark mode management
// Wait for Store to be available
(function() {
  function initDarkMode() {
    // Check if Store is available
    if (typeof window.Store === 'undefined') {
      // Retry after a short delay
      setTimeout(initDarkMode, 10);
      return;
    }

    // Initialize dark mode store - default to light mode
    const darkMode = new window.Store(localStorage.getItem('darkMode') === 'true');

    function toggleDarkMode() {
      // Toggle the dark mode state
      darkMode.value = !darkMode.value;
      localStorage.setItem('darkMode', darkMode.value.toString());
      updateDarkMode();
    }

    function updateDarkMode() {
      const html = document.documentElement;
      const body = document.body;
      const toggleIcon = document.getElementById('dark-mode-toggle');
      const toggleIconHeader = document.getElementById('dark-mode-toggle-header');
      const themeStylesheet = document.getElementById('theme-stylesheet');

      // Remove dark class from both html and body to ensure clean state
      html.classList.remove('dark');
      body.classList.remove('dark');

      if (darkMode.value) {
        // Add dark class to html element (Tailwind looks for it here)
        html.classList.add('dark');
        body.classList.add('dark');

        // Switch to dark mode CSS
        if (themeStylesheet) {
          themeStylesheet.href = 'css/darkmode.css';
        }

        if (toggleIcon) toggleIcon.textContent = '☀️';
        if (toggleIconHeader) toggleIconHeader.textContent = '☀️';
      } else {
        // Ensure dark class is removed from both
        html.classList.remove('dark');
        body.classList.remove('dark');

        // Switch to light mode CSS
        if (themeStylesheet) {
          themeStylesheet.href = 'css/lightmode.css';
        }

        if (toggleIcon) toggleIcon.textContent = '🌙';
        if (toggleIconHeader) toggleIconHeader.textContent = '🌙';
      }

      // Force a reflow to ensure Tailwind processes the change
      void html.offsetWidth;

      // Force Tailwind CDN to refresh styles if available
      if (typeof tailwind !== 'undefined' && tailwind.refresh) {
        try {
          tailwind.refresh();
        } catch (e) {
          // Tailwind CDN might not support refresh
        }
      }
    }

    // Subscribe to dark mode changes
    darkMode.subscribe(() => updateDarkMode());

    // Initialize dark mode on page load
    // Use setTimeout to ensure DOM is ready
    setTimeout(() => {
      updateDarkMode();
    }, 0);

    // Expose functions globally for onclick handlers and DOMContentLoaded
    window.toggleDarkMode = toggleDarkMode;
    window.updateDarkMode = updateDarkMode;
    window.darkMode = darkMode; // Expose darkMode store for debugging if needed
  }

  // Start initialization
  initDarkMode();
})();
