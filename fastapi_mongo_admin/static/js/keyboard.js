/**
 * Keyboard shortcuts handler
 * @module keyboard
 */

/**
 * Keyboard shortcuts manager
 */
export class KeyboardShortcuts {
  constructor() {
    this.shortcuts = new Map();
    this.init();
  }

  init() {
    document.addEventListener('keydown', (e) => {
      this.handleKeyPress(e);
    });
  }

  /**
   * Register a keyboard shortcut
   * @param {string} key - Key combination (e.g., 'ctrl+k', 'escape')
   * @param {Function} handler - Handler function
   * @param {string} description - Description for help menu
   */
  register(key, handler, description = '') {
    this.shortcuts.set(key, { handler, description });
  }

  /**
   * Handle key press
   * @param {KeyboardEvent} e - Keyboard event
   */
  handleKeyPress(e) {
    // Build key string
    const parts = [];
    if (e.ctrlKey || e.metaKey) parts.push('ctrl');
    if (e.altKey) parts.push('alt');
    if (e.shiftKey) parts.push('shift');
    parts.push(e.key.toLowerCase());

    const keyString = parts.join('+');

    // Check for exact match
    if (this.shortcuts.has(keyString)) {
      e.preventDefault();
      const { handler } = this.shortcuts.get(keyString);
      handler(e);
      return;
    }

    // Check for key-only match (if no modifiers)
    if (!e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
      if (this.shortcuts.has(e.key.toLowerCase())) {
        e.preventDefault();
        const { handler } = this.shortcuts.get(e.key.toLowerCase());
        handler(e);
      }
    }
  }

  /**
   * Get all registered shortcuts
   * @returns {Array} Array of shortcut objects
   */
  getAll() {
    return Array.from(this.shortcuts.entries()).map(([key, { description }]) => ({
      key,
      description,
    }));
  }
}

// Global keyboard shortcuts instance
export const keyboard = new KeyboardShortcuts();

// Register default shortcuts
keyboard.register('ctrl+k', () => {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.focus();
    searchInput.select();
  }
}, 'Focus search');

keyboard.register('ctrl+n', () => {
  if (typeof window.showCreateModal === 'function') {
    window.showCreateModal();
  }
}, 'Create new document');

keyboard.register('escape', () => {
  // Close any open modals
  const modals = document.querySelectorAll('[id$="-modal"]');
  modals.forEach(modal => {
    if (!modal.classList.contains('hidden')) {
      const closeFunc = modal.getAttribute('data-close-function');
      if (closeFunc && typeof window[closeFunc] === 'function') {
        window[closeFunc]();
      } else {
        modal.classList.add('hidden');
      }
    }
  });
}, 'Close modal/dialog');

keyboard.register('/', () => {
  // Only if not typing in an input
  if (document.activeElement?.tagName !== 'INPUT' &&
      document.activeElement?.tagName !== 'TEXTAREA') {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.focus();
    }
  }
}, 'Quick search');

