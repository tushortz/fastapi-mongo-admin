/**
 * View document modal component
 * @module react/components/ViewModal
 */

import { getDocument, getSchema } from '../services/api.js';
import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect } = React;

/**
 * Check if dark mode is active
 */
function isDarkMode() {
  // Check for dark mode class on html or body
  if (document.documentElement.classList.contains('dark') ||
      document.body.classList.contains('dark')) {
    return true;
  }
  // Check system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return true;
  }
  return false;
}

/**
 * Simple JSON syntax highlighter with light/dark mode support
 */
function highlightJson(jsonString, darkMode = false) {
  if (!jsonString) return '';

  try {
    // Parse to validate JSON
    JSON.parse(jsonString);
  } catch {
    // If invalid JSON, return as plain text
    return jsonString;
  }

  // Highlight JSON syntax with colors for light or dark background
  return jsonString
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
      let cls;
      if (darkMode) {
        // Dark mode colors
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'text-blue-400 font-semibold'; // Key
          } else {
            cls = 'text-green-400'; // String value
          }
        } else if (/true|false/.test(match)) {
          cls = 'text-purple-400'; // Boolean
        } else if (/null/.test(match)) {
          cls = 'text-gray-500'; // Null
        } else if (/^-?\d/.test(match)) {
          cls = 'text-orange-400'; // Number
        } else {
          cls = 'text-gray-200'; // Default
        }
      } else {
        // Light mode colors
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'text-blue-600 font-semibold'; // Key
          } else {
            cls = 'text-green-600'; // String value
          }
        } else if (/true|false/.test(match)) {
          cls = 'text-purple-600'; // Boolean
        } else if (/null/.test(match)) {
          cls = 'text-gray-400'; // Null
        } else if (/^-?\d/.test(match)) {
          cls = 'text-orange-600'; // Number
        } else {
          cls = 'text-gray-800'; // Default
        }
      }
      return `<span class="${cls}">${match}</span>`;
    });
}

/**
 * View modal component
 * @param {Object} props - Component props
 */
export function ViewModal({ collection, documentId, isOpen, onClose }) {
  const [document, setDocument] = useState(null);
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState('formatted'); // 'formatted' or 'json'
  const [darkMode, setDarkMode] = useState(isDarkMode());
  const t = useTranslation();

  useEffect(() => {
    if (isOpen && documentId) {
      loadDocument();
      loadSchema();
      setViewMode('formatted'); // Reset to formatted view when opening
      setDarkMode(isDarkMode());
    } else {
      setDocument(null);
      setSchema(null);
      setError('');
    }
  }, [isOpen, documentId, collection]);

  // Listen for dark mode changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => setDarkMode(isDarkMode());
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const loadDocument = async () => {
    if (!collection || !documentId) return;
    setLoading(true);
    setError('');
    try {
      const doc = await getDocument(collection, documentId);
      setDocument(doc);
    } catch (err) {
      setError(err.message || t('view.failedToLoad'));
    } finally {
      setLoading(false);
    }
  };

  const loadSchema = async () => {
    if (!collection) return;
    try {
      const schemaData = await getSchema(collection);
      setSchema(schemaData);
    } catch (err) {
      // Schema loading failed, continue without schema
    }
  };

  /**
   * Get a consistent color for an enum value
   * @param {string} value - Enum value
   * @returns {string} Tailwind CSS color class
   */
  const getEnumColor = (value) => {
    const colors = [
      'bg-blue-100 text-blue-800',
      'bg-green-100 text-green-800',
      'bg-yellow-100 text-yellow-800',
      'bg-red-100 text-red-800',
      'bg-purple-100 text-purple-800',
      'bg-pink-100 text-pink-800',
      'bg-indigo-100 text-indigo-800',
      'bg-teal-100 text-teal-800',
      'bg-orange-100 text-orange-800',
      'bg-cyan-100 text-cyan-800',
    ];
    // Use a simple hash to get consistent color for same value
    let hash = 0;
    const str = String(value);
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  /**
   * Check if a field is an enum field
   * @param {string} field - Field name
   * @returns {boolean} True if field is an enum
   */
  const isEnumField = (field) => {
    if (!schema || !schema.fields || !schema.fields[field]) {
      return false;
    }
    const fieldInfo = schema.fields[field];
    return fieldInfo.enum && Array.isArray(fieldInfo.enum) && fieldInfo.enum.length > 0;
  };

  const renderValue = (value, fieldName = null, depth = 0) => {
    if (value === null) {
      return <span className="text-gray-400 italic">null</span>;
    }
    if (value === undefined) {
      return <span className="text-gray-400 italic">undefined</span>;
    }

    // Check if this is an enum field and render as label
    if (fieldName && isEnumField(fieldName) && typeof value === 'string') {
      const enumValue = String(value);
      return (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEnumColor(enumValue)}`}>
          {titleize(enumValue)}
        </span>
      );
    }

    if (typeof value === 'boolean') {
      return <span className="text-blue-600">{String(value)}</span>;
    }
    if (typeof value === 'number') {
      return <span className="text-green-600">{value}</span>;
    }
    if (typeof value === 'string') {
      return <span className="text-gray-800">{value}</span>;
    }
    if (Array.isArray(value)) {
      return (
        <div className="ml-4 border-l-2 border-gray-200 pl-3">
          {value.map((item, idx) => (
            <div key={idx} className="mb-2">
              <span className="text-gray-500 text-sm">[{idx}]</span>
              <span className="ml-2">{renderValue(item, null, depth + 1)}</span>
            </div>
          ))}
        </div>
      );
    }
    if (typeof value === 'object') {
      return (
        <div className="ml-4 border-l-2 border-gray-200 pl-3 mt-1">
          {Object.entries(value).map(([key, val]) => (
            <div key={key} className="mb-2">
              <span className="font-semibold text-gray-700">{titleize(key)}:</span>
              <span className="ml-2">{renderValue(val, key, depth + 1)}</span>
            </div>
          ))}
        </div>
      );
    }
    return <span>{String(value)}</span>;
  };

  const renderFormattedView = () => {
    if (!document) return null;

    return (
      <div className="bg-gray-50 rounded-lg p-5">
        {Object.entries(document).map(([key, value]) => (
          <div key={key} className="mb-4 pb-4 border-b border-gray-200 last:border-b-0">
            <div className="font-semibold text-gray-700 mb-1">{titleize(key)}</div>
            <div className="text-sm text-gray-800">{renderValue(value, key)}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderJsonView = () => {
    if (!document) return null;

    const jsonString = JSON.stringify(document, null, 2);

    return (
      <div className="relative border border-gray-300 rounded overflow-hidden">
        <pre
          className="p-4 overflow-x-auto text-sm whitespace-pre"
          style={{
            backgroundColor: darkMode ? '#1e293b' : '#ffffff',
            color: darkMode ? '#e2e8f0' : '#1f2937',
            margin: 0,
            fontFamily: '"Hasklig", "Menlo", "Ubuntu Mono", "Consolas", "Monaco", "Courier New", monospace'
          }}
          dangerouslySetInnerHTML={{ __html: highlightJson(jsonString, darkMode) }}
        />
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div
        className="bg-white p-8 rounded-lg max-w-4xl w-11/12 max-h-screen overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">{t('view.title')}</h2>
          <div className="flex items-center gap-3">
            <div className="flex border border-gray-300 rounded overflow-hidden">
              <button
                onClick={() => setViewMode('formatted')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  viewMode === 'formatted'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}>
                {t('view.formatted')}
              </button>
              <button
                onClick={() => setViewMode('json')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  viewMode === 'json'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}>
                {t('view.json')}
              </button>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl">
              ×
            </button>
          </div>
        </div>
        {loading && (
          <div className="text-center py-10 text-gray-500">{t('view.loading')}</div>
        )}
        {error && (
          <div className="p-4 rounded mb-5 bg-red-100 text-red-800">{error}</div>
        )}
        {document && (
          <div>
            {viewMode === 'formatted' ? renderFormattedView() : renderJsonView()}
          </div>
        )}
      </div>
    </div>
  );
}
