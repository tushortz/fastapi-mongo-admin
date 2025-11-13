/**
 * Export modal component
 * @module react/components/ExportModal
 */

import { exportCollection } from '../services/api.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState } = React;

/**
 * Export modal component
 * @param {Object} props - Component props
 */
export function ExportModal({ collection, isOpen, onClose }) {
  const [format, setFormat] = useState('json');
  const [query, setQuery] = useState('');
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const t = useTranslation();

  if (!isOpen) return null;

  const handleExport = async () => {
    setExporting(true);
    setError('');
    try {
      await exportCollection(collection, format, query || null);
      onClose();
    } catch (err) {
      setError(err.message || t('export.exportFailed'));
    } finally {
      setExporting(false);
    }
  };

  const formats = [
    { value: 'json', label: 'JSON' },
    { value: 'csv', label: 'CSV' },
    { value: 'html', label: 'HTML' },
    { value: 'xml', label: 'XML' },
    { value: 'yaml', label: 'YAML' },
    { value: 'toml', label: 'TOML' },
  ];

  return (
    <div
      className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div
        className="bg-white p-6 rounded-lg max-w-md w-11/12"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">{t('export.title')}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl">
            ×
          </button>
        </div>
        {error && (
          <div className="mb-4 p-3 rounded bg-red-100 text-red-800 text-sm">{error}</div>
        )}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('export.format')}</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={format}
              onChange={(e) => setFormat(e.target.value)}>
              {formats.map((f) => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('export.query')}</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('export.queryPlaceholder')}
            />
          </div>
        </div>
        <div className="flex gap-3 justify-end mt-6">
          <button
            onClick={onClose}
            disabled={exporting}
            className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
            {t('common.cancel')}
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {exporting ? t('common.exporting') : t('common.export')}
          </button>
        </div>
      </div>
    </div>
  );
}
