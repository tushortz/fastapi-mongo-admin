/**
 * React hook for translations
 * @module react/hooks/useTranslation
 */

import { t, getCurrentLanguage, onLanguageChange } from '../i18n/i18n.js';

const { useState, useEffect } = React;

/**
 * Hook to use translations in React components
 * @returns {Function} Translation function
 */
export function useTranslation() {
  const [lang, setLang] = useState(getCurrentLanguage());

  useEffect(() => {
    const unsubscribe = onLanguageChange((newLang) => {
      setLang(newLang);
    });
    return () => unsubscribe();
  }, []);

  return t;
}

