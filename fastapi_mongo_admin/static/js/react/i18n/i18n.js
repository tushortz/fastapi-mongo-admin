/**
 * Internationalization (i18n) service
 * @module react/i18n/i18n
 */

// Import all translation files statically
import enTranslations from './translations/en.js';
import frTranslations from './translations/fr.js';
import ruTranslations from './translations/ru.js';
import esTranslations from './translations/es.js';
import ptTranslations from './translations/pt.js';
import chTranslations from './translations/ch.js';
import itTranslations from './translations/it.js';
import deTranslations from './translations/de.js';

// Supported languages
export const SUPPORTED_LANGUAGES = {
    en: 'English',
    fr: 'Français',
    ru: 'Русский',
    es: 'Español',
    pt: 'Português',
    ch: '中文',
    it: 'Italiano',
    de: 'Deutsch',
};

// Translation map
const translationMap = {
    en: enTranslations.default || enTranslations,
    fr: frTranslations.default || frTranslations,
    ru: ruTranslations.default || ruTranslations,
    es: esTranslations.default || esTranslations,
    pt: ptTranslations.default || ptTranslations,
    ch: chTranslations.default || chTranslations,
    it: itTranslations.default || itTranslations,
    de: deTranslations.default || deTranslations,
};

// Default language
const DEFAULT_LANGUAGE = 'en';

// Language code mapping (browser language codes to our supported codes)
const LANGUAGE_MAP = {
    'en': 'en',
    'en-US': 'en',
    'en-GB': 'en',
    'fr': 'fr',
    'fr-FR': 'fr',
    'fr-CA': 'fr',
    'ru': 'ru',
    'ru-RU': 'ru',
    'es': 'es',
    'es-ES': 'es',
    'es-MX': 'es',
    'pt': 'pt',
    'pt-BR': 'pt',
    'pt-PT': 'pt',
    'zh': 'ch',
    'zh-CN': 'ch',
    'zh-TW': 'ch',
    'zh-Hans': 'ch',
    'zh-Hant': 'ch',
    'it': 'it',
    'it-IT': 'it',
    'de': 'de',
    'de-DE': 'de',
    'de-AT': 'de',
    'de-CH': 'de',
};

// Current language state
let currentLanguage = DEFAULT_LANGUAGE;
let translations = {};
const listeners = new Set();

/**
 * Detect browser language and map it to a supported language code
 * @returns {string} Supported language code or default
 */
function detectBrowserLanguage() {
    if (typeof window === 'undefined' || !navigator) {
        return DEFAULT_LANGUAGE;
    }

    // Try navigator.language first (most specific)
    const browserLang = navigator.language || navigator.userLanguage;
    if (browserLang) {
        // Check direct match
        if (LANGUAGE_MAP[browserLang]) {
            return LANGUAGE_MAP[browserLang];
        }

        // Check language code only (e.g., 'en' from 'en-US')
        const langCode = browserLang.split('-')[0].toLowerCase();
        if (LANGUAGE_MAP[langCode]) {
            return LANGUAGE_MAP[langCode];
        }

        // Check if any supported language starts with the browser language
        for (const [browserCode, supportedCode] of Object.entries(LANGUAGE_MAP)) {
            if (browserCode.startsWith(langCode) || langCode.startsWith(browserCode.split('-')[0])) {
                return supportedCode;
            }
        }
    }

    // Try navigator.languages array (user's preferred languages)
    if (navigator.languages && Array.isArray(navigator.languages)) {
        for (const lang of navigator.languages) {
            const langCode = lang.split('-')[0].toLowerCase();
            if (LANGUAGE_MAP[langCode] || LANGUAGE_MAP[lang]) {
                return LANGUAGE_MAP[lang] || LANGUAGE_MAP[langCode];
            }
        }
    }

    return DEFAULT_LANGUAGE;
}

/**
 * Load translations for a specific language
 * @param {string} lang - Language code
 * @returns {Object} Translations object
 */
function loadTranslations(lang) {
    if (translationMap[lang]) {
        return translationMap[lang];
    }
    console.warn(`Failed to load translations for ${lang}, falling back to English`);
    return translationMap[DEFAULT_LANGUAGE] || {};
}

/**
 * Initialize i18n with a language
 * @param {string} lang - Language code (optional, overrides all other sources)
 */
export function initI18n(lang = null) {
    let langToUse = DEFAULT_LANGUAGE;

    if (lang) {
        // Explicitly provided language takes precedence
        langToUse = lang;
    } else {
        // Check localStorage first (user's saved preference)
        const savedLang = localStorage.getItem('app_language');
        if (savedLang && SUPPORTED_LANGUAGES[savedLang]) {
            langToUse = savedLang;
        } else {
            // No saved preference, detect from browser
            const browserLang = detectBrowserLanguage();
            langToUse = browserLang;
        }
    }

    // Validate language
    if (!SUPPORTED_LANGUAGES[langToUse]) {
        console.warn(`Invalid language code: ${langToUse}, falling back to ${DEFAULT_LANGUAGE}`);
        langToUse = DEFAULT_LANGUAGE;
    }

    currentLanguage = langToUse;

    // Load translations
    translations = loadTranslations(currentLanguage);

    // Store preference in localStorage (only if not explicitly provided, to preserve user choice)
    if (!lang) {
        localStorage.setItem('app_language', currentLanguage);
    }

    // Notify listeners
    listeners.forEach(listener => listener(currentLanguage));
}

/**
 * Get current language
 * @returns {string} Current language code
 */
export function getCurrentLanguage() {
    return currentLanguage;
}

/**
 * Set language
 * @param {string} lang - Language code
 */
export function setLanguage(lang) {
    if (!SUPPORTED_LANGUAGES[lang]) {
        console.warn(`Unsupported language: ${lang}`);
        return;
    }

    currentLanguage = lang;
    translations = loadTranslations(lang);
    localStorage.setItem('app_language', lang);

    // Notify listeners
    listeners.forEach(listener => listener(lang));
}

/**
 * Translate a key with optional parameters
 * @param {string} key - Translation key (supports dot notation, e.g., 'common.save')
 * @param {Object} params - Optional parameters for interpolation
 * @returns {string} Translated string
 */
export function t(key, params = {}) {
    if (!key) return '';

    // Support dot notation for nested keys
    const keys = key.split('.');
    let value = translations;

    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            // Fallback to key if translation not found
            console.warn(`Translation missing for key: ${key}`);
            return key;
        }
    }

    // If value is not a string, return the key
    if (typeof value !== 'string') {
        return key;
    }

    // Simple parameter interpolation: {{paramName}}
    return value.replace(/\{\{(\w+)\}\}/g, (match, paramName) => {
        return params[paramName] !== undefined ? String(params[paramName]) : match;
    });
}

/**
 * Subscribe to language changes
 * @param {Function} callback - Callback function
 * @returns {Function} Unsubscribe function
 */
export function onLanguageChange(callback) {
    listeners.add(callback);
    return () => listeners.delete(callback);
}

// Initialize on load
if (typeof window !== 'undefined') {
    initI18n();
}

