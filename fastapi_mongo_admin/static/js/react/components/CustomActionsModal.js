/**
 * Custom actions modal component
 * @module react/components/CustomActionsModal
 */

import { useTranslation } from '../hooks/useTranslation.js';

const { useState } = React;

/**
 * Custom actions modal for defining and executing custom bulk operations
 * @param {Object} props - Component props
 */
export function CustomActionsModal({ collection, documentIds, isOpen, onClose, onExecute }) {
  const [actionType, setActionType] = useState('update_field');
  const [fieldName, setFieldName] = useState('');
  const [fieldValue, setFieldValue] = useState('');
  const [customQuery, setCustomQuery] = useState('');
  const [error, setError] = useState('');
  const t = useTranslation();

  if (!isOpen) return null;

  const handleExecute = () => {
    setError('');

    if (actionType === 'update_field') {
      if (!fieldName || !fieldValue) {
        setError(t('customActions.fieldRequired') || 'Field name and value are required');
        return;
      }
      // Create update operations for each document
      const updates = Array.from(documentIds).map(id => ({
        _id: id,
        data: { [fieldName]: fieldValue }
      }));
      onExecute(updates);
    } else if (actionType === 'custom_query') {
      if (!customQuery) {
        setError(t('customActions.queryRequired') || 'Custom query is required');
        return;
      }
      try {
        const query = JSON.parse(customQuery);
        // For custom queries, we'll need to apply them differently
        // This is a placeholder - actual implementation would depend on backend support
        onExecute({ type: 'custom_query', query });
      } catch (e) {
        setError(t('customActions.invalidJson') || 'Invalid JSON query');
        return;
      }
    }

    onClose();
  };

  return (
    <div
      className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div
        className="bg-white p-8 rounded-lg max-w-2xl w-11/12 max-h-screen overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold text-gray-900">
            {t('customActions.title') || 'Custom Action'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl">
            ×
          </button>
        </div>

        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-blue-800">
            {t('customActions.info', { count: documentIds.size }) || `This action will be applied to ${documentIds.size} selected document(s).`}
          </p>
        </div>

        {error && (
          <div className="p-4 rounded mb-5 bg-red-100 text-red-800">{error}</div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('customActions.actionType') || 'Action Type'}
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white text-gray-900"
              value={actionType}
              onChange={(e) => setActionType(e.target.value)}>
              <option value="update_field">{t('customActions.updateField') || 'Update Field'}</option>
              <option value="custom_query">{t('customActions.customQuery') || 'Custom Query'}</option>
            </select>
          </div>

          {actionType === 'update_field' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('customActions.fieldName') || 'Field Name'}
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white text-gray-900"
                  value={fieldName}
                  onChange={(e) => setFieldName(e.target.value)}
                  placeholder={t('bulkUpdate.example', { example: 'status' }) || 'e.g., status'}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('customActions.fieldValue') || 'Field Value'}
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white text-gray-900"
                  value={fieldValue}
                  onChange={(e) => setFieldValue(e.target.value)}
                  placeholder={t('bulkUpdate.example', { example: 'active' }) || 'e.g., active'}
                />
              </div>
            </>
          )}

          {actionType === 'custom_query' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('customActions.mongoQuery') || 'MongoDB Query (JSON)'}
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white text-gray-900 font-mono"
                rows={6}
                value={customQuery}
                onChange={(e) => setCustomQuery(e.target.value)}
                placeholder='{"status": "active"}'
              />
              <p className="text-xs text-gray-500 mt-1">
                {t('customActions.queryHint') || 'Enter a MongoDB query object in JSON format'}
              </p>
            </div>
          )}
        </div>

        <div className="flex gap-3 justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50">
            {t('common.cancel') || 'Cancel'}
          </button>
          <button
            onClick={handleExecute}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
            {t('customActions.execute') || 'Execute'}
          </button>
        </div>
      </div>
    </div>
  );
}

