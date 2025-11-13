/**
 * Schema view component
 * @module react/components/SchemaView
 */

import { getSchema } from '../services/api.js';
import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect } = React;

/**
 * Check if dark mode is active
 */
function isDarkMode() {
  if (document.documentElement.classList.contains('dark') ||
    document.body.classList.contains('dark')) {
    return true;
  }
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return true;
  }
  return false;
}

/**
 * Schema view component
 * @param {Object} props - Component props
 */
export function SchemaView({ collection }) {
  const [viewMode, setViewMode] = useState('formatted'); // 'formatted' or 'json'
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(isDarkMode());
  const t = useTranslation();

  useEffect(() => {
    if (!collection) return;

    setLoading(true);
    setError('');
    setDarkMode(isDarkMode());
    getSchema(collection)
      .then(data => {
        setSchema(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message || t('schema.failedToLoad'));
        setLoading(false);
      });
  }, [collection]);

  // Listen for dark mode changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => setDarkMode(isDarkMode());
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-white rounded-lg shadow">
        <div className="text-center text-gray-400">{t('schema.loadingSchema')}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-white rounded-lg shadow">
        <div className="p-4 rounded bg-red-100 text-red-800">{error}</div>
      </div>
    );
  }

  const renderFormattedView = () => {
    if (!schema) return null;

    const fields = schema.fields || {};
    const fieldEntries = Array.isArray(fields)
      ? fields.map((f, i) => [typeof f === 'string' ? f : (f.name || `field_${i}`), f])
      : Object.entries(fields);

    return (
      <div className="space-y-4">
        {schema.collection && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-500 uppercase mb-2">{t('schema.collection')}</h4>
            <p className="text-base text-gray-800">{schema.collection}</p>
          </div>
        )}

        {fieldEntries.length > 0 ? (
          <div>
            <h4 className="text-sm font-semibold text-gray-500 uppercase mb-4">{t('schema.fields')}</h4>
            <div className="space-y-4">
              {fieldEntries.map(([fieldName, fieldInfo]) => {
                const field = typeof fieldInfo === 'object' ? fieldInfo : { type: fieldInfo };
                const fieldType = (field.type || 'string').toLowerCase();
                const isRequired = !field.nullable;

                return (
                  <div key={fieldName} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <h5 className="text-base font-semibold text-gray-800">
                        {titleize(fieldName)}
                        {isRequired && <span className="text-red-500 ml-2">*</span>}
                      </h5>
                      <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                        {fieldType}
                      </span>
                    </div>

                    <div className="mt-3 space-y-2 text-sm">
                      {field.description && (
                        <div>
                          <span className="font-medium text-gray-600">{t('common.description')}: </span>
                          <span className="text-gray-700">{field.description}</span>
                        </div>
                      )}

                      {field.example !== undefined && (
                        <div>
                          <span className="font-medium text-gray-600">{t('common.example')}: </span>
                          <span className="text-gray-700 font-mono bg-white px-2 py-1 rounded">
                            {typeof field.example === 'object'
                              ? JSON.stringify(field.example)
                              : String(field.example)}
                          </span>
                        </div>
                      )}

                      {field.enum && Array.isArray(field.enum) && field.enum.length > 0 && (
                        <div>
                          <span className="font-medium text-gray-600">{t('common.allowedValues')}: </span>
                          <div className="mt-1 flex flex-wrap gap-2">
                            {field.enum.map((val, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                                {String(val)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex gap-4 text-xs text-gray-500">
                        <span>{t('schema.required')}: {isRequired ? t('common.yes') : t('common.no')}</span>
                        {field.default !== undefined && (
                          <span>{t('schema.default')}: <span className="font-mono">{String(field.default)}</span></span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
              {t('schema.noFields')}
          </div>
        )}
      </div>
    );
  };

  const renderJsonView = () => {
    if (!schema) return null;

    const jsonString = JSON.stringify(schema, null, 2);

    return (
      <div className="relative border border-gray-300 rounded overflow-hidden">
        <pre
          className="p-4 overflow-x-auto text-sm whitespace-pre"
          style={{
            backgroundColor: darkMode ? '#1e293b' : '#ffffff',
            color: darkMode ? '#e2e8f0' : '#1f2937',
            margin: 0,
            fontFamily: '"Hasklig", "Menlo", "Ubuntu Mono", "Consolas", "Monaco", "Courier New", monospace'
          }}>
          {jsonString}
        </pre>
      </div>
    );
  };

  return (
    <div className="h-full w-full flex flex-col bg-white rounded-lg shadow overflow-hidden">
      <div className="flex justify-between items-center p-5 border-b border-gray-200">
        <h3 className="text-lg font-semibold">{t('schema.title')}</h3>
        <div className="flex items-center gap-3">
          <div className="flex border border-gray-300 rounded overflow-hidden">
            <button
              type="button"
              onClick={() => setViewMode('formatted')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'formatted'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}>
              {t('schema.formatted')}
            </button>
            <button
              type="button"
              onClick={() => setViewMode('json')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${viewMode === 'json'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}>
              {t('schema.json')}
            </button>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-auto p-5">
        {viewMode === 'formatted' ? renderFormattedView() : renderJsonView()}
      </div>
    </div>
  );
}
