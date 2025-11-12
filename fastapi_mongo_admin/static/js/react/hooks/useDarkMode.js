/**
 * Custom hook for dark mode management
 * @module react/hooks/useDarkMode
 */

const { useState, useEffect } = React;

/**
 * Hook to manage dark mode state
 * @returns {[boolean, Function]} Dark mode state and toggle function
 */
export function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('darkMode') === 'true';
  });

  useEffect(() => {
    const html = document.documentElement;
    const themeStylesheet = document.getElementById('theme-stylesheet');

    if (darkMode) {
      html.classList.add('dark');
      if (themeStylesheet) {
        themeStylesheet.href = 'css/darkmode.css';
      }
    } else {
      html.classList.remove('dark');
      if (themeStylesheet) {
        themeStylesheet.href = 'css/lightmode.css';
      }
    }

    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(prev => !prev);

  return [darkMode, toggleDarkMode];
}

