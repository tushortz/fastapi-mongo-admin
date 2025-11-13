/**
 * Language selector component
 * @module react/components/LanguageSelector
 */

import { getCurrentLanguage, setLanguage, SUPPORTED_LANGUAGES, onLanguageChange } from '../i18n/i18n.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect } = React;

/**
 * Language selector component
 * @param {Object} props - Component props
 */
export function LanguageSelector() {
  const [currentLang, setCurrentLang] = useState(getCurrentLanguage());
  const t = useTranslation();

  useEffect(() => {
    // Subscribe to language changes
    const unsubscribe = onLanguageChange((lang) => {
      setCurrentLang(lang);
    });

    return () => unsubscribe();
  }, []);

  const handleLanguageChange = (e) => {
    const newLang = e.target.value;
    setLanguage(newLang);
    // Force a page reload to ensure all components update
    window.location.reload();
  };

  return (
    <select
      value={currentLang}
      onChange={handleLanguageChange}
      className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
      title={t('common.selectLanguage')}>
      {Object.entries(SUPPORTED_LANGUAGES).map(([code, name]) => (
        <option key={code} value={code}>
          {name}
        </option>
      ))}
    </select>
  );
}

