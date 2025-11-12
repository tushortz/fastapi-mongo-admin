/**
 * Utility functions for admin dashboard
 * @module utils
 */

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

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
 * Client-side cache for API responses
 */
export class ApiCache {
    constructor(ttl = 60000) {
        this.cache = new Map();
        this.ttl = ttl;
    }

    /**
     * Get cached response
     * @param {string} key - Cache key
     * @returns {*} Cached data or null
     */
    get(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        if (Date.now() - cached.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Set cache entry
     * @param {string} key - Cache key
     * @param {*} data - Data to cache
     */
    set(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * Clear cache
     * @param {string} pattern - Optional pattern to match keys
     */
    clear(pattern = null) {
        if (!pattern) {
            this.cache.clear();
            return;
        }

        for (const key of this.cache.keys()) {
            if (key.includes(pattern)) {
                this.cache.delete(key);
            }
        }
    }

    /**
     * Get cache statistics
     * @returns {Object} Cache stats
     */
    getStats() {
        const now = Date.now();
        let valid = 0;
        let expired = 0;

        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp < this.ttl) {
                valid++;
            } else {
                expired++;
            }
        }

        return {
            total: this.cache.size,
            valid,
            expired
        };
    }
}

/**
 * Batch multiple API calls
 * @param {Array<Promise>} promises - Array of promises to batch
 * @returns {Promise<Array>} Array of results
 */
export async function batchApiCalls(promises) {
    return Promise.all(promises);
}

/**
 * Format error message for display
 * @param {Error|string} error - Error object or message
 * @returns {string} Formatted error message
 */
export function formatError(error) {
    if (typeof error === 'string') return error;
    if (error?.detail) return error.detail;
    if (error?.message) return error.message;
    return 'An unknown error occurred';
}

/**
 * Format number with thousand separators
 * @param {number|string} num - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
export function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || num === '') return '';
    const number = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(number)) return '';

    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(number);
}

/**
 * Format currency value
 * @param {number|string} amount - Amount to format
 * @param {string} currency - Currency code (default: USD)
 * @param {string} locale - Locale code (default: en-US)
 * @returns {string} Formatted currency string
 */
export function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
    if (amount === null || amount === undefined || amount === '') return '';
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (isNaN(num)) return '';

    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency
    }).format(num);
}

/**
 * Parse formatted number string back to number
 * @param {string} formatted - Formatted number string (may include commas, currency symbols)
 * @returns {number} Parsed number or NaN
 */
export function parseFormattedNumber(formatted) {
    if (!formatted) return NaN;
    // Remove currency symbols, spaces, and thousand separators
    const cleaned = String(formatted)
        .replace(/[^\d.-]/g, '')
        .replace(/,/g, '');
    return parseFloat(cleaned);
}

/**
 * Validate number input
 * @param {string|number} value - Value to validate
 * @param {Object} options - Validation options
 * @param {number} options.min - Minimum value
 * @param {number} options.max - Maximum value
 * @param {number} options.step - Step increment
 * @param {boolean} options.required - Whether field is required
 * @returns {Object} Validation result with isValid and message
 */
export function validateNumber(value, options = {}) {
    const { min, max, step, required = false } = options;

    if (value === '' || value === null || value === undefined) {
        if (required) {
            return { isValid: false, message: 'This field is required' };
        }
        return { isValid: true, message: '' };
    }

    const num = typeof value === 'string' ? parseFloat(value) : value;

    if (isNaN(num)) {
        return { isValid: false, message: 'Please enter a valid number' };
    }

    if (min !== undefined && num < min) {
        return { isValid: false, message: `Value must be at least ${min}` };
    }

    if (max !== undefined && num > max) {
        return { isValid: false, message: `Value must be at most ${max}` };
    }

    if (step !== undefined && step > 0) {
        const remainder = (num % step);
        const tolerance = step / 1000; // Small tolerance for floating point
        if (remainder > tolerance && (step - remainder) > tolerance) {
            return { isValid: false, message: `Value must be a multiple of ${step}` };
        }
    }

    return { isValid: true, message: '' };
}

/**
 * Enhance number input field with formatting and validation
 * @param {HTMLInputElement} input - Number input element
 * @param {Object} options - Enhancement options
 * @param {boolean} options.formatOnBlur - Format value on blur (default: true)
 * @param {boolean} options.showCurrency - Show currency symbol (default: false)
 * @param {string} options.currency - Currency code (default: USD)
 * @param {number} options.min - Minimum value
 * @param {number} options.max - Maximum value
 * @param {number} options.step - Step increment
 */
export function enhanceNumberInput(input, options = {}) {
    const {
        formatOnBlur = true,
        showCurrency = false,
        currency = 'USD',
        min,
        max,
        step
    } = options;

    // Add validation attributes
    if (min !== undefined) input.setAttribute('min', min);
    if (max !== undefined) input.setAttribute('max', max);
    if (step !== undefined) input.setAttribute('step', step);

    // Format on blur
    if (formatOnBlur) {
        input.addEventListener('blur', () => {
            const value = input.value;
            if (value && !isNaN(parseFloat(value))) {
                const num = parseFloat(value);

                // Apply min/max constraints
                let constrainedValue = num;
                if (min !== undefined && num < min) constrainedValue = min;
                if (max !== undefined && num > max) constrainedValue = max;

                // Round to step if specified
                if (step !== undefined && step > 0) {
                    constrainedValue = Math.round(constrainedValue / step) * step;
                }

                // Format display
                if (showCurrency) {
                    input.value = formatCurrency(constrainedValue, currency);
                } else {
                    // Determine decimal places from step
                    const decimals = step && step < 1
                        ? Math.abs(Math.log10(step))
                        : (input.step && parseFloat(input.step) < 1
                            ? Math.abs(Math.log10(parseFloat(input.step)))
                            : 2);
                    input.value = formatNumber(constrainedValue, decimals);
                }
            }
        });

        // Clear formatting on focus for easier editing
        input.addEventListener('focus', () => {
            const value = input.value;
            if (value) {
                const num = parseFormattedNumber(value);
                if (!isNaN(num)) {
                    input.value = num.toString();
                }
            }
        });
    }

    // Real-time validation
    input.addEventListener('input', () => {
        const value = input.value;
        const validation = validateNumber(value, { min, max, step, required: input.required });

        // Update visual feedback
        if (value && !validation.isValid) {
            input.classList.add('border-red-500');
            input.classList.remove('border-gray-300');
            input.setAttribute('title', validation.message);
        } else {
            input.classList.remove('border-red-500');
            input.classList.add('border-gray-300');
            input.removeAttribute('title');
        }
    });
}

