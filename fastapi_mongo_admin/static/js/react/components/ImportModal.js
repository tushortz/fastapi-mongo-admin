/**
 * Import modal component
 * @module react/components/ImportModal
 */

import { importCollection } from '../services/api.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState } = React;

/**
 * Import modal component
 * @param {Object} props - Component props
 */
export function ImportModal({ collection, isOpen, onClose, onSuccess }) {
  const [format, setFormat] = useState('json');
  const [file, setFile] = useState(null);
  const [overwrite, setOverwrite] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState('');
  const t = useTranslation();

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setError('');
    // Auto-detect format from file extension
    if (selectedFile) {
      const ext = selectedFile.name.split('.').pop().toLowerCase();
      const formatMap = { json: 'json', csv: 'csv', html: 'html', xml: 'xml', yaml: 'yaml', yml: 'yaml', toml: 'toml' };
      if (formatMap[ext]) {
        setFormat(formatMap[ext]);
      }
    }
  };

  const handleImport = async () => {
    if (!file) {
      setError(t('import.selectFile'));
      return;
    }

    setImporting(true);
    setError('');
    try {
      await importCollection(collection, file, format, overwrite);
      onSuccess();
      onClose();
      setFile(null);
    } catch (err) {
      setError(err.message || t('import.importFailed'));
    } finally {
      setImporting(false);
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
          <h3 className="text-lg font-semibold">{t('import.title')}</h3>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('import.file')}</label>
            <input
              type="file"
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
              onChange={handleFileChange}
              accept=".json,.csv,.html,.xml,.yaml,.yml,.toml"
            />
            {file && (
              <p className="text-sm text-gray-600 mt-1">{t('import.selected')}: {file.name}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">{t('import.format')}</label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
              value={format}
              onChange={(e) => setFormat(e.target.value)}>
              {formats.map((f) => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={overwrite}
              onChange={(e) => setOverwrite(e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm text-gray-700">{t('import.overwrite')}</span>
          </label>
        </div>
        <div className="flex gap-3 justify-end mt-6">
          <button
            onClick={onClose}
            disabled={importing}
            className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
            {t('common.cancel')}
          </button>
          <button
            onClick={handleImport}
            disabled={importing || !file}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {importing ? t('common.importing') : t('common.import')}
          </button>
        </div>
      </div>
    </div>
  );
}
