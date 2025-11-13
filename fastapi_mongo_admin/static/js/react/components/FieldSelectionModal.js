/**
 * Field selection modal component
 * @module react/components/FieldSelectionModal
 */

import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect } = React;

/**
 * Field selection modal component
 * @param {Object} props - Component props
 */
export function FieldSelectionModal({ isOpen, fields = [], selectedFields = [], onClose, onApply }) {
  const [localSelected, setLocalSelected] = useState(new Set(selectedFields));
  const t = useTranslation();

  useEffect(() => {
    if (isOpen) {
      setLocalSelected(new Set(selectedFields));
    }
  }, [isOpen, selectedFields]);

  if (!isOpen) return null;

  const toggleField = (field) => {
    const newSelected = new Set(localSelected);
    if (newSelected.has(field)) {
      newSelected.delete(field);
    } else {
      newSelected.add(field);
    }
    setLocalSelected(newSelected);
  };

  const selectAll = () => {
    setLocalSelected(new Set(fields));
  };

  const deselectAll = () => {
    setLocalSelected(new Set());
  };

  const handleApply = () => {
    onApply(Array.from(localSelected));
    onClose();
  };

  return (
    <div
      className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div
        className="bg-white p-6 rounded-lg max-w-md w-11/12 max-h-screen overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">{t('fieldSelection.title')}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl">
            ×
          </button>
        </div>
        <div className="mb-4 flex gap-2">
          <button
            onClick={selectAll}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded">
            {t('fieldSelection.selectAll')}
          </button>
          <button
            onClick={deselectAll}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded">
            {t('fieldSelection.deselectAll')}
          </button>
        </div>
        <div className="max-h-96 overflow-y-auto mb-4">
          {fields.length === 0 ? (
            <p className="text-gray-500 text-sm">{t('fieldSelection.noFields')}</p>
          ) : (
            [...fields].sort((a, b) => {
              const aStr = String(a).toLowerCase();
              const bStr = String(b).toLowerCase();
              return aStr.localeCompare(bStr);
            }).map((field) => (
              <label
                key={field}
                className="flex items-center p-2 hover:bg-gray-50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={localSelected.has(field)}
                  onChange={() => toggleField(field)}
                  className="mr-2"
                />
                <span className="text-sm">{field}</span>
              </label>
            ))
          )}
        </div>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50">
            {t('common.cancel')}
          </button>
          <button
            onClick={handleApply}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
            {t('common.apply')}
          </button>
        </div>
      </div>
    </div>
  );
}
