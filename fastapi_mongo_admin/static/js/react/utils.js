/**
 * Utility functions for React components
 * @module react/utils
 */

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML
 */
export function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

/**
 * Titleize a string (convert snake_case to Title Case)
 * @param {string} str - String to titleize
 * @returns {string} Titleized string
 */
export function titleize(str) {
  if (!str) return '';
  return String(str)
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Get API base URL from config or use default
 * @returns {string} API base URL
 */
export function getApiBase() {
  return (window.ADMIN_CONFIG && window.ADMIN_CONFIG.API_BASE) || '/admin';
}

/**
 * Format error message
 * @param {Error|string} error - Error object or message
 * @returns {string} Formatted error message
 */
export function formatError(error) {
  if (typeof error === 'string') return error;
  if (error && error.message) return error.message;
  return 'An unknown error occurred';
}

