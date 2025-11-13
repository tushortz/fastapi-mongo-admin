/**
 * Edit document modal component
 * @module react/components/EditModal
 */

import { updateDocument, getDocument, getSchema, uploadFile } from '../services/api.js';
import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';
import { toast } from '../../toast.js';

const { useState, useEffect } = React;

const FIELDS_PER_PAGE = 5;

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
 * Enhanced JSON syntax highlighter with light/dark mode support
 */
function highlightJson(jsonString, darkMode = false) {
  if (!jsonString) return '';

  // Escape HTML to prevent XSS
  const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  };

  // Try to format and validate JSON
  let formattedJson = jsonString;
  try {
    const parsed = JSON.parse(jsonString);
    formattedJson = JSON.stringify(parsed, null, 2);
  } catch {
    // If invalid JSON, still try to highlight what we can
    formattedJson = jsonString;
  }

  // Escape HTML first
  let highlighted = escapeHtml(formattedJson);

  // Color scheme based on mode
  const colors = darkMode ? {
    key: 'text-blue-300 font-semibold',
    string: 'text-green-300',
    number: 'text-orange-300',
    boolean: 'text-purple-300',
    null: 'text-gray-400',
    bracket: 'text-white',
    default: 'text-white'
  } : {
    key: 'text-blue-600 font-semibold',
    string: 'text-green-600',
    number: 'text-orange-600',
    boolean: 'text-purple-600',
    null: 'text-gray-400',
    bracket: 'text-gray-600',
    default: 'text-gray-800'
  };

  // Process JSON character by character to avoid conflicts
  const parts = [];
  let i = 0;
  let inString = false;
  let stringStart = -1;
  let escapeNext = false;
  let currentString = '';

  while (i < highlighted.length) {
    const char = highlighted[i];

    if (escapeNext) {
      if (inString) {
        currentString += char;
      } else {
        parts.push(`<span class="${colors.default}">${char}</span>`);
      }
      escapeNext = false;
      i++;
      continue;
    }

    if (char === '\\' && inString) {
      escapeNext = true;
      currentString += char;
      i++;
      continue;
    }

    if (char === '"' && !escapeNext) {
      if (!inString) {
        // Start of string
        stringStart = i;
        inString = true;
        currentString = char;
      } else {
        // End of string
        currentString += char;
        // Check if followed by colon (key) or not (value)
        const afterString = highlighted.substring(i + 1).trim();
        const isKey = afterString.startsWith(':');
        const color = isKey ? colors.key : colors.string;
        parts.push(`<span class="${color}">${currentString}</span>`);
        inString = false;
        stringStart = -1;
        currentString = '';
      }
      i++;
      continue;
    }

    if (inString) {
      // Inside string - accumulate characters
      currentString += char;
      i++;
      continue;
    }

    // Outside strings, highlight other tokens
    if (char.match(/[{}[\]]/)) {
      parts.push(`<span class="${colors.bracket}">${char}</span>`);
      i++;
      continue;
    }

    // Check for numbers
    if (char.match(/[\d-]/)) {
      const numberMatch = highlighted.substring(i).match(/^-?\d+\.?\d*(?:[eE][+-]?\d+)?/);
      if (numberMatch) {
        parts.push(`<span class="${colors.number}">${numberMatch[0]}</span>`);
        i += numberMatch[0].length;
        continue;
      }
    }

    // Check for booleans and null
    const remaining = highlighted.substring(i);
    if (remaining.startsWith('true')) {
      parts.push(`<span class="${colors.boolean}">true</span>`);
      i += 4;
      continue;
    }
    if (remaining.startsWith('false')) {
      parts.push(`<span class="${colors.boolean}">false</span>`);
      i += 5;
      continue;
    }
    if (remaining.startsWith('null')) {
      parts.push(`<span class="${colors.null}">null</span>`);
      i += 4;
      continue;
    }

    // Regular character - add with default color
    parts.push(`<span class="${colors.default}">${char}</span>`);
    i++;
  }

  // If we ended in a string, add the remaining part
  if (inString && currentString) {
    parts.push(`<span class="${colors.string}">${currentString}</span>`);
  }

  return parts.join('');
}

/**
 * Edit modal component
 * @param {Object} props - Component props
 */
export function EditModal({ collection, documentId, isOpen, onClose, onSuccess }) {
  const [editMode, setEditMode] = useState('form'); // 'form' or 'json'
  const [schema, setSchema] = useState(null);
  const [formData, setFormData] = useState({});
  const [jsonData, setJsonData] = useState('{}');
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(isDarkMode());
  const [uploadingFiles, setUploadingFiles] = useState({});
  const t = useTranslation();

  useEffect(() => {
    if (isOpen && documentId && collection) {
      loadDocument();
      loadSchema();
      setEditMode('form');
      setCurrentPage(0);
      setError('');
      setDarkMode(isDarkMode());
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
    setLoadingDoc(true);
    setError('');
    try {
      const doc = await getDocument(collection, documentId);
      setFormData(doc);
      setJsonData(JSON.stringify(doc, null, 2));
    } catch (err) {
      setError(err.message || 'Failed to load document');
    } finally {
      setLoadingDoc(false);
    }
  };

  const loadSchema = async () => {
    if (!collection) return;
    setLoadingSchema(true);
    try {
      const schemaData = await getSchema(collection);
      setSchema(schemaData);
    } catch (err) {
      // Schema loading failed, continue without schema
    } finally {
      setLoadingSchema(false);
    }
  };

  if (!isOpen) return null;

  // Convert schema fields object to array
  const fieldsObj = schema?.fields || {};
  const fields = Array.isArray(fieldsObj)
    ? fieldsObj
    : Object.entries(fieldsObj).map(([name, fieldInfo]) => ({
      name,
      ...fieldInfo
    }));

  const totalPages = Math.ceil(fields.length / FIELDS_PER_PAGE);
  const startIndex = currentPage * FIELDS_PER_PAGE;
  const endIndex = startIndex + FIELDS_PER_PAGE;
  const currentFields = fields.slice(startIndex, endIndex);

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
    // Also update JSON data
    const updated = { ...formData, [fieldName]: value };
    setJsonData(JSON.stringify(updated, null, 2));
    setError('');
  };

  const handleJsonChange = (value) => {
    setJsonData(value);
    try {
      const parsed = JSON.parse(value);
      setFormData(parsed);
      setError('');
    } catch {
      // Invalid JSON, but allow editing
    }
  };

  const convertValue = (value, fieldInfo) => {
    if (value === '' || value === null || value === undefined) {
      return fieldInfo.nullable ? null : undefined;
    }

    const fieldType = (fieldInfo.type || '').toLowerCase();

    // Handle enum - return as string
    if (fieldInfo.enum && Array.isArray(fieldInfo.enum)) {
      return String(value);
    }

    // Handle boolean
    if (fieldType === 'bool' || fieldType === 'boolean') {
      return value === 'true' || value === true || value === 'True';
    }

    // Handle numbers
    if (fieldType === 'int' || fieldType === 'integer') {
      return parseInt(value, 10);
    }
    if (fieldType === 'float' || fieldType === 'double' || fieldType === 'number') {
      return parseFloat(value);
    }

    // Handle dates - return ISO date string (YYYY-MM-DD)
    if (fieldType === 'date') {
      return new Date(value).toISOString().split('T')[0];
    }

    // Handle datetime/timestamp - return full ISO datetime string
    if (fieldType === 'datetime' || fieldType === 'timestamp') {
      const date = new Date(value);
      return date.toISOString();
    }

    // Handle list/array - ensure it's an array
    if (fieldType === 'list' || fieldType === 'array') {
      try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed)) {
          return parsed;
        }
        return [parsed];
      } catch {
        if (typeof value === 'string' && value.includes(',')) {
          return value.split(',').map(item => item.trim()).filter(item => item);
        }
        return value ? [value] : [];
      }
    }

    // Handle complex types (object, dict) - try to parse as JSON
    if (fieldType === 'dict' || fieldType === 'object') {
      try {
        return JSON.parse(value);
      } catch {
        return value;
      }
    }

    // Default: return as string
    return String(value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let data;
      if (editMode === 'json') {
        // Validate JSON before attempting to submit
        try {
          data = JSON.parse(jsonData);
        } catch (parseError) {
          setError('Invalid JSON format. Please check your JSON syntax and try again.');
          setLoading(false);
          return;
        }

        // Additional validation: ensure data is an object
        if (typeof data !== 'object' || data === null || Array.isArray(data)) {
          setError('JSON must be a valid object (not an array or primitive value).');
          setLoading(false);
          return;
        }
      } else {
        // Convert form data to proper types
        data = {};
        fields.forEach(field => {
          const fieldName = field.name || field;
          const value = formData[fieldName];
          if (value !== undefined && value !== '') {
            data[fieldName] = convertValue(value, field);
          } else if (!field.nullable && field.example !== undefined && field.example !== null) {
            data[fieldName] = field.example;
          }
        });
      }

      // Remove _id from update data
      delete data._id;
      await updateDocument(collection, documentId, data);

      // Show success alert
      toast.success(t('edit.documentUpdated'));

      onSuccess();
      onClose();
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON format. Please check your JSON syntax and try again.');
      } else {
        setError(err.message || 'Failed to update document');
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Generate field ID from field name
   * @param {string} fieldName - Field name
   * @returns {string} Field ID in format id_fieldname
   */
  const getFieldId = (fieldName) => {
    return `id_${fieldName}`;
  };

  /**
   * Check if a field is likely a file/image field
   * @param {string} fieldName - Field name
   * @param {string} fieldType - Field type
   * @returns {boolean} True if field is likely a file/image field
   */
  const isFileField = (fieldName, fieldType) => {
    const fieldNameLower = fieldName.toLowerCase();
    const fileKeywords = ['image', 'photo', 'picture', 'avatar', 'file', 'attachment', 'upload', 'url', 'path', 'link'];
    return fileKeywords.some(keyword => fieldNameLower.includes(keyword)) ||
      (fieldType === 'str' || fieldType === 'string') && (fieldNameLower.includes('url') || fieldNameLower.includes('path'));
  };

  /**
   * Handle file upload
   * @param {string} fieldName - Field name
   * @param {File} file - File to upload
   */
  const handleFileUpload = async (fieldName, file) => {
    if (!file) return;

    setUploadingFiles(prev => ({ ...prev, [fieldName]: true }));
    try {
      const result = await uploadFile(file, collection);
      handleFieldChange(fieldName, result.url);
    } catch (err) {
      setError(err.message || t('edit.failedToUploadFile') || 'Failed to upload file');
    } finally {
      setUploadingFiles(prev => ({ ...prev, [fieldName]: false }));
    }
  };

  // Reuse renderFieldInput from CreateModal logic
  const renderFieldInput = (field) => {
    const fieldName = field.name || field;
    const fieldId = getFieldId(fieldName);
    const fieldType = (field.type || '').toLowerCase();
    const value = formData[fieldName] || '';
    const isRequired = !field.nullable;
    const isReadonly = field.readonly === true;

    // Enum field - dropdown
    if (field.enum && Array.isArray(field.enum) && field.enum.length > 0) {
      const sortedEnum = [...field.enum].sort((a, b) => {
        const aStr = String(a).toLowerCase();
        const bStr = String(b).toLowerCase();
        return aStr.localeCompare(bStr);
      });

      return (
        <select
          id={fieldId}
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          required={isRequired}>
          <option value="">{t('create.select')}</option>
          {sortedEnum.map((enumValue) => (
            <option key={enumValue} value={String(enumValue)}>
              {titleize(String(enumValue))}
            </option>
          ))}
        </select>
      );
    }

    // Boolean field
    if (fieldType === 'bool' || fieldType === 'boolean') {
      return (
        <select
          id={fieldId}
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          required={isRequired}
          disabled={isReadonly}>
          <option value="">{t('create.select')}</option>
          <option value="true">{t('common.true')}</option>
          <option value="false">{t('common.false')}</option>
        </select>
      );
    }

    // Date field - use date input
    if (fieldType === 'date') {
      const dateValue = value ? (value.includes('T') ? value.split('T')[0] : value) : '';
      return (
        <input
          id={fieldId}
          type="date"
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={dateValue}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          required={isRequired}
          readOnly={isReadonly}
          disabled={isReadonly}
        />
      );
    }

    // Datetime/timestamp field - use datetime-local input
    if (fieldType === 'datetime' || fieldType === 'timestamp') {
      let datetimeValue = '';
      if (value) {
        try {
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            datetimeValue = `${year}-${month}-${day}T${hours}:${minutes}`;
          }
        } catch (e) {
          datetimeValue = value;
        }
      }

      return (
        <input
          id={fieldId}
          type="datetime-local"
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={datetimeValue}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          required={isRequired}
          readOnly={isReadonly}
          disabled={isReadonly}
        />
      );
    }

    // Integer fields - use number input
    if (fieldType === 'int' || fieldType === 'integer') {
      const constraints = field.constraints || {};
      const min = constraints.ge !== undefined ? constraints.ge : constraints.gt !== undefined ? constraints.gt + 1 : undefined;
      const max = constraints.le !== undefined ? constraints.le : constraints.lt !== undefined ? constraints.lt - 1 : undefined;

      return (
        <input
          id={fieldId}
          type="number"
          step="1"
          min={min}
          max={max}
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={field.example !== undefined && field.example !== null ? String(field.example) : ''}
          required={isRequired}
          readOnly={isReadonly}
          disabled={isReadonly}
        />
      );
    }

    // Float fields - use number input with step of 2
    if (fieldType === 'float' || fieldType === 'double' || fieldType === 'number') {
      const constraints = field.constraints || {};
      const min = constraints.ge !== undefined ? constraints.ge : constraints.gt !== undefined ? constraints.gt : undefined;
      const max = constraints.le !== undefined ? constraints.le : constraints.lt !== undefined ? constraints.lt : undefined;

      return (
        <input
          id={fieldId}
          type="number"
          step="0.01"
          min={min}
          max={max}
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={field.example !== undefined && field.example !== null ? String(field.example) : ''}
          required={isRequired}
          readOnly={isReadonly}
          disabled={isReadonly}
        />
      );
    }

    // List/Array fields - render as tags
    if (fieldType === 'list' || fieldType === 'array') {
      let currentValues = [];
      if (value) {
        if (Array.isArray(value)) {
          currentValues = value;
        } else if (typeof value === 'string') {
          try {
            const parsed = JSON.parse(value);
            currentValues = Array.isArray(parsed) ? parsed : [parsed];
          } catch {
            currentValues = value.split(',').map(item => item.trim()).filter(item => item);
          }
        } else {
          currentValues = [value];
        }
      }

      const handleRemoveTag = (indexToRemove) => {
        const newValues = currentValues.filter((_, index) => index !== indexToRemove);
        handleFieldChange(fieldName, newValues);
      };

      const handleAddTag = (newValue) => {
        if (newValue && !currentValues.includes(newValue)) {
          handleFieldChange(fieldName, [...currentValues, newValue]);
        }
      };

      if (field.enum && Array.isArray(field.enum) && field.enum.length > 0) {
        // Use dropdown with enum values + tags display
        const sortedEnum = [...field.enum].sort((a, b) => {
          const aStr = String(a).toLowerCase();
          const bStr = String(b).toLowerCase();
          return aStr.localeCompare(bStr);
        });

        const availableOptions = sortedEnum.filter(opt => !currentValues.includes(String(opt)));

        return (
          <div>
            {/* Display current tags */}
            <div className="flex flex-wrap gap-2 mb-2 min-h-[2.5rem] p-2 border rounded">
              {currentValues.length === 0 ? (
                <span className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>{t('common.noItems')}</span>
              ) : (
                currentValues.map((val, index) => (
                  <span
                    key={index}
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${darkMode
                      ? 'bg-blue-900 text-blue-200'
                      : 'bg-blue-100 text-blue-800'
                      }`}>
                    <span>{titleize(String(val))}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(index)}
                      className={`ml-1 focus:outline-none ${darkMode
                        ? 'text-blue-300 hover:text-blue-100'
                        : 'text-blue-600 hover:text-blue-800'
                        }`}>
                      ×
                    </button>
                  </span>
                ))
              )}
            </div>
            {/* Dropdown to add new items */}
            {availableOptions.length > 0 && (
              <select
                id={`${fieldId}_add`}
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
                value=""
                onChange={(e) => {
                  if (e.target.value) {
                    handleAddTag(e.target.value);
                    e.target.value = '';
                  }
                }}>
                <option value="">{t('common.addItem')}</option>
                {availableOptions.map((enumValue) => (
                  <option key={enumValue} value={String(enumValue)}>
                    {titleize(String(enumValue))}
                  </option>
                ))}
              </select>
            )}
          </div>
        );
      } else {
        // Free-form array with text input + tags display
        return (
          <div>
            {/* Display current tags */}
            <div className="flex flex-wrap gap-2 mb-2 min-h-[2.5rem] p-2 border rounded">
              {currentValues.length === 0 ? (
                <span className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>{t('common.noItemsAdded')}</span>
              ) : (
                currentValues.map((val, index) => (
                  <span
                    key={index}
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${darkMode
                      ? 'bg-blue-900 text-blue-200'
                      : 'bg-blue-100 text-blue-800'
                      }`}>
                    <span>{String(val)}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(index)}
                      className={`ml-1 focus:outline-none ${darkMode
                        ? 'text-blue-300 hover:text-blue-100'
                        : 'text-blue-600 hover:text-blue-800'
                        }`}>
                      ×
                    </button>
                  </span>
                ))
              )}
            </div>
            {/* Input to add new items */}
            <div className="flex gap-2">
              <input
                id={`${fieldId}_add`}
                type="text"
                className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    const newItem = e.target.value.trim();
                    if (newItem) {
                      handleAddTag(newItem);
                      e.target.value = '';
                    }
                  }
                }}
                placeholder={t('common.enterItem')}
              />
              <button
                type="button"
                onClick={(e) => {
                  const input = e.target.previousElementSibling;
                  if (input && input.tagName === 'INPUT') {
                    const newItem = input.value.trim();
                    if (newItem) {
                      handleAddTag(newItem);
                      input.value = '';
                    }
                  }
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                Add
              </button>
            </div>
          </div>
        );
      }
    }

    // Complex types (object, dict) - textarea for JSON
    if (fieldType === 'dict' || fieldType === 'object') {
      const jsonValue = typeof value === 'string' ? value : JSON.stringify(value || field.example || {}, null, 2);
      return (
        <textarea
          id={fieldId}
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm font-mono ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          rows={4}
          value={jsonValue}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={field.example !== undefined && field.example !== null ? JSON.stringify(field.example, null, 2) : '{}'}
          required={isRequired}
          readOnly={isReadonly}
          disabled={isReadonly}
        />
      );
    }

    // File/Image upload field
    if (isFileField(fieldName, fieldType)) {
      const isImage = fieldName.toLowerCase().includes('image') ||
        fieldName.toLowerCase().includes('photo') ||
        fieldName.toLowerCase().includes('picture') ||
        fieldName.toLowerCase().includes('avatar');
      const fileUrl = value;
      const isUploading = uploadingFiles[fieldName];

      return (
        <div>
          {fileUrl && (
            <div className="mb-2">
              {isImage ? (
                <img
                  src={fileUrl}
                  alt={fieldName}
                  className="max-w-full h-32 object-contain border border-gray-300 rounded"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              ) : (
                <a
                  href={fileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline">
                  {fileUrl}
                </a>
              )}
            </div>
          )}
          <div className="flex gap-2">
            <input
              id={fieldId}
              type="file"
              accept={isImage ? "image/*" : "*/*"}
              className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleFileUpload(fieldName, file);
                }
              }}
              disabled={isUploading}
            />
            {fileUrl && (
              <button
                type="button"
                onClick={() => handleFieldChange(fieldName, '')}
                className="px-3 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700">
                {t('common.remove') || 'Remove'}
              </button>
            )}
          </div>
          {isUploading && (
            <p className="text-sm text-gray-500 mt-1">{t('edit.uploading') || 'Uploading...'}</p>
          )}
        </div>
      );
    }

    // Email field
    const fieldNameLower = fieldName.toLowerCase();
    if (fieldNameLower === 'email' || fieldType === 'email' || fieldType === 'email_str') {
      return (
        <input
          id={fieldId}
          type="email"
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={field.example !== undefined && field.example !== null ? String(field.example) : 'example@email.com'}
          required={isRequired}
        />
      );
    }

    // Default: text input
    const constraints = field.constraints || {};
    const minLength = constraints.min_length;
    const maxLength = constraints.max_length;
    const pattern = constraints.pattern;

    return (
      <input
        id={fieldId}
        type="text"
        minLength={minLength}
        maxLength={maxLength}
        pattern={pattern}
        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
        value={value}
        onChange={(e) => handleFieldChange(fieldName, e.target.value)}
        placeholder={field.example !== undefined ? String(field.example) : ''}
        required={isRequired}
      />
    );
  };

  return (
    <div
      className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div
        className="bg-white p-8 rounded-lg max-w-4xl w-11/12 max-h-screen overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">{t('edit.title')}</h2>
          <div className="flex items-center gap-3">
            <div className="flex border border-gray-300 rounded overflow-hidden">
              <button
                type="button"
                onClick={() => setEditMode('form')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${editMode === 'form'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}>
                {t('edit.form')}
              </button>
              <button
                type="button"
                onClick={() => setEditMode('json')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${editMode === 'json'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}>
                {t('edit.json')}
              </button>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl">
              ×
            </button>
          </div>
        </div>

        {loadingDoc && (
          <div className="mb-4 text-gray-500">{t('edit.loadingDocument')}</div>
        )}

        {loadingSchema && editMode === 'form' && (
          <div className="mb-4 text-gray-500">{t('edit.loadingSchema')}</div>
        )}

        {error && (
          <div className="mb-4 p-3 rounded bg-red-100 text-red-800 text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          {editMode === 'form' ? (
            <>
              {!loadingSchema && fields.length === 0 && (
                <div className="mb-4 p-3 rounded bg-yellow-100 text-yellow-800 text-sm">
                  {t('edit.noSchema')}
                </div>
              )}

              {!loadingSchema && fields.length > 0 && (
                <>
                  <div className="mb-4">
                    {currentFields.map((field) => {
                      const fieldName = field.name || field;
                      return (
                        <div key={fieldName} className="mb-4">
                          <label htmlFor={getFieldId(fieldName)} className="block text-sm font-medium text-gray-700 mb-2">
                            {titleize(fieldName)}
                            {!field.nullable && <span className="text-red-500 ml-1">*</span>}
                            {field.readonly && <span className="text-gray-500 ml-1 text-xs">({t('edit.readonly')})</span>}
                          </label>
                          {renderFieldInput(field)}
                          {field.example !== undefined && field.example !== null && (
                            <p className="mt-1 text-xs text-gray-500">
                              {t('common.example')}: {String(field.example)}
                            </p>
                          )}
                          {field.constraints && (
                            <p className="mt-1 text-xs text-gray-500">
                              {(() => {
                                const constraints = field.constraints;
                                const parts = [];
                                if (constraints.min_length !== undefined) {
                                  parts.push(t('validation.minLength', { length: constraints.min_length }));
                                }
                                if (constraints.max_length !== undefined) {
                                  parts.push(t('validation.maxLength', { length: constraints.max_length }));
                                }
                                if (constraints.ge !== undefined) {
                                  parts.push(t('validation.min', { value: constraints.ge }));
                                }
                                if (constraints.gt !== undefined) {
                                  parts.push(t('validation.minGreater', { value: constraints.gt }));
                                }
                                if (constraints.le !== undefined) {
                                  parts.push(t('validation.max', { value: constraints.le }));
                                }
                                if (constraints.lt !== undefined) {
                                  parts.push(t('validation.maxLess', { value: constraints.lt }));
                                }
                                if (constraints.pattern !== undefined) {
                                  parts.push(t('validation.pattern', { pattern: constraints.pattern }));
                                }
                                return parts.length > 0 ? `${t('validation.constraints')}: ${parts.join(', ')}` : '';
                              })()}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Pagination Controls */}
                  {totalPages > 1 && (
                    <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
                      <button
                        type="button"
                        onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
                        disabled={currentPage === 0}
                        className="px-4 py-2 border border-gray-300 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                        {t('common.previous')}
                      </button>
                      <span className="text-sm text-gray-600">
                        {t('common.page')} {currentPage + 1} {t('common.of')} {totalPages}
                      </span>
                      <button
                        type="button"
                        onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
                        disabled={currentPage >= totalPages - 1}
                        className="px-4 py-2 border border-gray-300 rounded text-sm font-medium bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                        {t('common.next')}
                      </button>
                    </div>
                  )}
                </>
              )}
            </>
          ) : (
            <div className="mb-4">
                <label htmlFor="id_json_data" className="block text-sm font-medium text-gray-700 mb-2">{t('edit.jsonData')}</label>
                <textarea
                  id="id_json_data"
                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm resize-none"
                  value={jsonData}
                  onChange={(e) => handleJsonChange(e.target.value)}
                  disabled={loadingDoc}
                  required
                  spellCheck={false}
                  style={{
                    fontFamily: '"Hasklig", "Menlo", "Ubuntu Mono", "Consolas", "Monaco", "Courier New", monospace',
                    minHeight: '400px',
                    maxHeight: '60vh',
                    overflow: 'auto'
                  }}
                />
            </div>
          )}

          <div className="flex gap-2.5 justify-end mt-5">
            <button
              type="button"
              onClick={onClose}
              disabled={loading || loadingDoc}
              className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700 disabled:opacity-50">
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading || loadingDoc}
              className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
              {loading ? t('common.saving') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
