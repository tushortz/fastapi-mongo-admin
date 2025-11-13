/**
 * Bulk update modal component
 * @module react/components/BulkUpdateModal
 */

import { bulkUpdateDocuments, getSchema } from '../services/api.js';
import { useTranslation } from '../hooks/useTranslation.js';
import { titleize } from '../utils.js';

const { useState, useEffect } = React;

/**
 * Bulk update modal component
 * @param {Object} props - Component props
 */
export function BulkUpdateModal({ collection, documentIds, isOpen, onClose, onSuccess }) {
  const [schema, setSchema] = useState(null);
  const [updateData, setUpdateData] = useState({});
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');
  const [selectedField, setSelectedField] = useState('');
  const t = useTranslation();

  useEffect(() => {
    if (isOpen && collection) {
      loadSchema();
      setUpdateData({});
      setSelectedField('');
      setError('');
    }
  }, [isOpen, collection]);

  const loadSchema = async () => {
    if (!collection) return;
    try {
      const schemaData = await getSchema(collection);
      setSchema(schemaData);
    } catch (err) {
      setError(t('bulkUpdate.failedToLoadSchema') || 'Failed to load schema');
    }
  };

  const handleFieldChange = (fieldName, value) => {
    setUpdateData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleUpdate = async () => {
    if (Object.keys(updateData).length === 0) {
      setError(t('bulkUpdate.noFieldsSelected') || 'Please select at least one field to update');
      return;
    }

    setUpdating(true);
    setError('');

    try {
      // Build updates array: each document gets the same update data
      const updates = Array.from(documentIds).map(id => ({
        _id: id,
        data: updateData
      }));

      const result = await bulkUpdateDocuments(collection, updates);

      if (onSuccess) {
        onSuccess(result);
      }
      onClose();
      setUpdateData({});
    } catch (err) {
      setError(err.message || t('bulkUpdate.updateFailed') || 'Failed to update documents');
    } finally {
      setUpdating(false);
    }
  };

  const renderFieldInput = (fieldName, fieldInfo) => {
    const fieldType = (fieldInfo.type || '').toLowerCase();
    const fieldTypes = (fieldInfo.types || []).map(t => String(t).toLowerCase());
    const value = updateData[fieldName] ?? '';

    // Enum field - dropdown
    if (fieldInfo.enum && Array.isArray(fieldInfo.enum) && fieldInfo.enum.length > 0) {
      const sortedEnum = [...fieldInfo.enum].sort((a, b) => {
        return String(a).localeCompare(String(b));
      });

      return (
        <select
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}>
          <option value="">{t('common.select')}</option>
          {sortedEnum.map((enumValue) => (
            <option key={enumValue} value={String(enumValue)}>
              {titleize(String(enumValue))}
            </option>
          ))}
        </select>
      );
    }

    // Boolean field - dropdown
    if (fieldType === 'bool' || fieldType === 'boolean' || fieldTypes.includes('bool') || fieldTypes.includes('boolean')) {
      return (
        <select
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value === 'true')}>
          <option value="">{t('common.select')}</option>
          <option value="true">{t('common.true')}</option>
          <option value="false">{t('common.false')}</option>
        </select>
      );
    }

    // Date field
    if (fieldType === 'date' || fieldTypes.includes('date')) {
      return (
        <input
          type="date"
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        />
      );
    }

    // Datetime/Timestamp field
    if (fieldType === 'datetime' || fieldType === 'timestamp' || fieldTypes.includes('datetime') || fieldTypes.includes('timestamp')) {
      return (
        <input
          type="datetime-local"
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        />
      );
    }

    // Integer field
    if (fieldType === 'int' || fieldType === 'integer' || fieldTypes.includes('int') || fieldTypes.includes('integer')) {
      return (
        <input
          type="number"
          step="1"
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, parseInt(e.target.value) || 0)}
        />
      );
    }

    // Float/Double/Number field
    if (fieldType === 'float' || fieldType === 'double' || fieldType === 'number' ||
        fieldTypes.includes('float') || fieldTypes.includes('double') || fieldTypes.includes('number')) {
      return (
        <input
          type="number"
          step="0.01"
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, parseFloat(e.target.value) || 0)}
        />
      );
    }

    // Email field
    if (fieldName.toLowerCase() === 'email' || fieldType === 'email' || fieldType === 'email_str' ||
        fieldTypes.includes('email') || fieldTypes.includes('email_str')) {
      return (
        <input
          type="email"
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        />
      );
    }

    // Default: text input
    return (
      <input
        type="text"
        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        value={value}
        onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        placeholder={fieldInfo.example ? t('bulkUpdate.example', { example: fieldInfo.example }) : ''}
      />
    );
  };

  if (!isOpen) return null;

  const availableFields = schema && schema.fields ? Object.keys(schema.fields).filter(f => f !== '_id') : [];

  return (
    <div
      className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div
        className="bg-white dark:bg-gray-800 p-8 rounded-lg max-w-2xl w-11/12 max-h-screen overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold dark:text-white">
            {t('bulkUpdate.title') || 'Bulk Update Documents'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-2xl">
            ×
          </button>
        </div>

        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            {t('bulkUpdate.info') || `Updating ${documentIds.size} document(s). All selected documents will be updated with the same values.`}
          </p>
        </div>

        {error && (
          <div className="p-4 rounded mb-5 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">{error}</div>
        )}

        {schema && schema.fields ? (
          <div className="space-y-4">
            {availableFields.map((fieldName) => {
              const fieldInfo = schema.fields[fieldName];
              return (
                <div key={fieldName}>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    {titleize(fieldName)}
                    {fieldInfo.nullable === false && (
                      <span className="text-red-500 ml-1">*</span>
                    )}
                  </label>
                  {renderFieldInput(fieldName, fieldInfo)}
                  {fieldInfo.example && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {t('common.example')}: {fieldInfo.example}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-10 text-gray-500 dark:text-gray-400">
            {t('bulkUpdate.loadingSchema') || 'Loading schema...'}
          </div>
        )}

        <div className="flex gap-3 justify-end mt-6">
          <button
            onClick={onClose}
            disabled={updating}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">
            {t('common.cancel') || 'Cancel'}
          </button>
          <button
            onClick={handleUpdate}
            disabled={updating || Object.keys(updateData).length === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
            {updating ? (t('bulkUpdate.updating') || 'Updating...') : (t('bulkUpdate.update') || 'Update')}
          </button>
        </div>
      </div>
    </div>
  );
}

