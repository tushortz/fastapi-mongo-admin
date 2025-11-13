/**
 * Create document modal component
 * @module react/components/CreateModal
 */

import { createDocument, getSchema, uploadFile } from '../services/api.js';
import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect } = React;

const FIELDS_PER_PAGE = 5;

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
 * Create modal component
 * @param {Object} props - Component props
 */
export function CreateModal({ collection, isOpen, onClose, onSuccess }) {
  const [editMode, setEditMode] = useState('form'); // 'form' or 'json'
  const [schema, setSchema] = useState(null);
  const [formData, setFormData] = useState({});
  const [jsonData, setJsonData] = useState('{}');
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(isDarkMode());
  const [uploadingFiles, setUploadingFiles] = useState({});
  const t = useTranslation();

  useEffect(() => {
    if (isOpen && collection) {
      loadSchema();
      setFormData({});
      setJsonData('{}');
      setCurrentPage(0);
      setEditMode('form');
      setError('');
      setDarkMode(isDarkMode());
    }
  }, [isOpen, collection]);

  // Listen for dark mode changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => setDarkMode(isDarkMode());
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Generate JSON structure when schema loads and we're in JSON mode
  useEffect(() => {
    if (schema && editMode === 'json' && jsonData === '{}') {
      generateJsonFromSchema(schema);
    }
  }, [schema, editMode]);

  const loadSchema = async () => {
    if (!collection) return;
    setLoadingSchema(true);
    try {
      const schemaData = await getSchema(collection);
      setSchema(schemaData);
      // If in JSON mode, generate structure from schema
      if (editMode === 'json') {
        generateJsonFromSchema(schemaData);
      }
    } catch (err) {
      // Schema loading failed, continue without schema
      setError(t('create.failedToLoadSchema'));
    } finally {
      setLoadingSchema(false);
    }
  };

  /**
   * Generate JSON data structure from schema
   * @param {Object} schemaData - Schema data from API
   */
  const generateJsonFromSchema = (schemaData) => {
    if (!schemaData || !schemaData.fields) {
      setJsonData('{}');
      return;
    }

    const fieldsObj = schemaData.fields || {};
    const fields = Array.isArray(fieldsObj)
      ? fieldsObj
      : Object.entries(fieldsObj).map(([name, fieldInfo]) => ({
        name,
        ...fieldInfo
      }));

    const generatedData = {};

    fields.forEach(field => {
      const fieldName = field.name || field;
      const fieldType = (field.type || '').toLowerCase();

      // Use example if available (but not null)
      if (field.example !== undefined && field.example !== null) {
        generatedData[fieldName] = field.example;
        return;
      }

      // Generate default value based on type
      if (field.enum && Array.isArray(field.enum) && field.enum.length > 0) {
        // Use first enum value as default
        generatedData[fieldName] = field.enum[0];
      } else if (fieldType === 'bool' || fieldType === 'boolean') {
        generatedData[fieldName] = false;
      } else if (fieldType === 'int' || fieldType === 'integer') {
        generatedData[fieldName] = 0;
      } else if (fieldType === 'float' || fieldType === 'double' || fieldType === 'number') {
        generatedData[fieldName] = 0.0;
      } else if (fieldType === 'date') {
        // Use today's date in YYYY-MM-DD format
        const today = new Date();
        generatedData[fieldName] = today.toISOString().split('T')[0];
      } else if (fieldType === 'datetime' || fieldType === 'timestamp') {
        // Use current datetime in ISO format
        generatedData[fieldName] = new Date().toISOString();
      } else if (fieldType === 'list' || fieldType === 'array') {
        generatedData[fieldName] = [];
      } else if (fieldType === 'dict' || fieldType === 'object') {
        generatedData[fieldName] = {};
      } else {
        // Default to empty string for string types
        const fieldNameLower = fieldName.toLowerCase();
        if (fieldNameLower === 'email' || fieldType === 'email' || fieldType === 'email_str') {
          generatedData[fieldName] = 'example@email.com';
        } else {
          generatedData[fieldName] = '';
        }
      }

      // Handle nullable fields: if field is optional (nullable = true) and no example,
      // set to null instead of generated default
      if (field.nullable === true && field.example === undefined) {
        generatedData[fieldName] = null;
      }
      // For required fields (nullable = false), keep the generated default value
    });

    setJsonData(JSON.stringify(generatedData, null, 2));
    setFormData(generatedData);
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
    setFormData(prev => {
      const updated = {
        ...prev,
        [fieldName]: value
      };
      // Also update JSON data
      setJsonData(JSON.stringify(updated, null, 2));
      return updated;
    });
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

  /**
   * Validate JSON data against schema
   * @param {string} jsonString - JSON string to validate
   * @param {Object} schemaData - Schema data
   * @returns {Object} Validation result with isValid and errors array
   */
  const validateJsonData = (jsonString, schemaData) => {
    const errors = [];

    // Validate JSON syntax
    let data;
    try {
      data = JSON.parse(jsonString);
    } catch (e) {
      return {
        isValid: false,
        errors: [t('create.invalidJsonSyntax', { error: e.message })]
      };
    }

    if (!schemaData || !schemaData.fields) {
      // No schema available, skip validation
      return { isValid: true, errors: [] };
    }

    // Convert schema fields to array
    const fieldsObj = schemaData.fields || {};
    const fields = Array.isArray(fieldsObj)
      ? fieldsObj
      : Object.entries(fieldsObj).map(([name, fieldInfo]) => ({
        name,
        ...fieldInfo
      }));

    // Validate each field
    fields.forEach(field => {
      const fieldName = field.name || field;
      const fieldType = (field.type || '').toLowerCase();
      const value = data[fieldName];
      const isRequired = !field.nullable;
      const constraints = field.constraints || {};

      // Check required fields
      if (isRequired && (value === undefined || value === null || value === '')) {
        errors.push(t('validation.fieldRequired', { field: fieldName }));
        return;
      }

      // Skip validation if value is null/undefined and field is nullable
      if ((value === null || value === undefined) && field.nullable) {
        return;
      }

      // Validate enum values
      if (field.enum && Array.isArray(field.enum) && field.enum.length > 0) {
        const enumStr = String(value);
        const enumValues = field.enum.map(e => String(e));
        if (!enumValues.includes(enumStr)) {
          errors.push(t('validation.fieldMustBeOneOf', { field: fieldName, values: enumValues.join(', ') }));
        }
      }

      // Validate type
      if (value !== null && value !== undefined && value !== '') {
        // Boolean validation
        if (fieldType === 'bool' || fieldType === 'boolean') {
          if (typeof value !== 'boolean') {
            errors.push(t('validation.fieldMustBeBoolean', { field: fieldName }));
          }
        }
        // Integer validation
        else if (fieldType === 'int' || fieldType === 'integer') {
          if (!Number.isInteger(value)) {
            errors.push(t('validation.fieldMustBeInteger', { field: fieldName }));
          } else {
            // Validate constraints
            if (constraints.ge !== undefined && value < constraints.ge) {
              errors.push(t('validation.fieldMustBeGreaterOrEqual', { field: fieldName, value: constraints.ge }));
            }
            if (constraints.gt !== undefined && value <= constraints.gt) {
              errors.push(t('validation.fieldMustBeGreater', { field: fieldName, value: constraints.gt }));
            }
            if (constraints.le !== undefined && value > constraints.le) {
              errors.push(t('validation.fieldMustBeLessOrEqual', { field: fieldName, value: constraints.le }));
            }
            if (constraints.lt !== undefined && value >= constraints.lt) {
              errors.push(t('validation.fieldMustBeLess', { field: fieldName, value: constraints.lt }));
            }
          }
        }
        // Float/Number validation
        else if (fieldType === 'float' || fieldType === 'double' || fieldType === 'number') {
          if (typeof value !== 'number' || isNaN(value)) {
            errors.push(t('validation.fieldMustBeNumber', { field: fieldName }));
          } else {
            // Validate constraints
            if (constraints.ge !== undefined && value < constraints.ge) {
              errors.push(t('validation.fieldMustBeGreaterOrEqual', { field: fieldName, value: constraints.ge }));
            }
            if (constraints.gt !== undefined && value <= constraints.gt) {
              errors.push(t('validation.fieldMustBeGreater', { field: fieldName, value: constraints.gt }));
            }
            if (constraints.le !== undefined && value > constraints.le) {
              errors.push(t('validation.fieldMustBeLessOrEqual', { field: fieldName, value: constraints.le }));
            }
            if (constraints.lt !== undefined && value >= constraints.lt) {
              errors.push(t('validation.fieldMustBeLess', { field: fieldName, value: constraints.lt }));
            }
          }
        }
        // String validation
        else if (fieldType === 'str' || fieldType === 'string' || fieldType === 'email' || fieldType === 'email_str') {
          if (typeof value !== 'string') {
            errors.push(t('validation.fieldMustBeString', { field: fieldName }));
          } else {
            // Validate string constraints
            if (constraints.min_length !== undefined && value.length < constraints.min_length) {
              errors.push(t('validation.fieldMinLength', { field: fieldName, length: constraints.min_length }));
            }
            if (constraints.max_length !== undefined && value.length > constraints.max_length) {
              errors.push(t('validation.fieldMaxLength', { field: fieldName, length: constraints.max_length }));
            }
            if (constraints.pattern) {
              try {
                const regex = new RegExp(constraints.pattern);
                if (!regex.test(value)) {
                  errors.push(t('validation.fieldPatternMismatch', { field: fieldName }));
                }
              } catch (e) {
                // Invalid regex pattern, skip validation
              }
            }
            // Email validation
            if (fieldName.toLowerCase() === 'email' || fieldType === 'email' || fieldType === 'email_str') {
              const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
              if (!emailRegex.test(value)) {
                errors.push(t('validation.fieldMustBeEmail', { field: fieldName }));
              }
            }
          }
        }
        // Date validation
        else if (fieldType === 'date') {
          if (typeof value !== 'string') {
            errors.push(t('validation.fieldMustBeDateString', { field: fieldName }));
          } else {
            const date = new Date(value);
            if (isNaN(date.getTime())) {
              errors.push(t('validation.fieldMustBeValidDate', { field: fieldName }));
            }
          }
        }
        // DateTime/Timestamp validation
        else if (fieldType === 'datetime' || fieldType === 'timestamp') {
          if (typeof value !== 'string') {
            errors.push(t('validation.fieldMustBeDatetimeString', { field: fieldName }));
          } else {
            const date = new Date(value);
            if (isNaN(date.getTime())) {
              errors.push(t('validation.fieldMustBeValidDatetime', { field: fieldName }));
            }
          }
        }
        // Array/List validation
        else if (fieldType === 'list' || fieldType === 'array') {
          if (!Array.isArray(value)) {
            errors.push(t('validation.fieldMustBeArray', { field: fieldName }));
          }
        }
        // Object/Dict validation
        else if (fieldType === 'dict' || fieldType === 'object') {
          if (typeof value !== 'object' || Array.isArray(value) || value === null) {
            errors.push(t('validation.fieldMustBeObject', { field: fieldName }));
          }
        }
      }
    });

    return {
      isValid: errors.length === 0,
      errors
    };
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
      // datetime-local returns format: YYYY-MM-DDTHH:mm
      // Convert to ISO string
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
        // If not an array, wrap in array
        return [parsed];
      } catch {
        // If not valid JSON, try to split by comma or return as single-item array
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
        // Parse JSON data first
        try {
          data = JSON.parse(jsonData);
        } catch (e) {
          setError(t('create.invalidJson', { error: e.message }));
          setLoading(false);
          return;
        }

        // Validate JSON data
        const validation = validateJsonData(jsonData, schema);
        if (!validation.isValid) {
          setError(validation.errors.join('; '));
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
            // Use example value for required fields if not provided
            data[fieldName] = field.example;
          }
        });

        // Validate form data by converting to JSON and validating
        const jsonString = JSON.stringify(data);
        const validation = validateJsonData(jsonString, schema);
        if (!validation.isValid) {
          setError(validation.errors.join('; '));
          setLoading(false);
          return;
        }

        // Run custom field validators
        const customFieldErrors = [];
        fields.forEach(field => {
          const fieldName = field.name || field;
          const value = data[fieldName];
          const fieldError = validateField(fieldName, value, field, data, t);
          if (fieldError) {
            customFieldErrors.push(fieldError);
          }
        });

        // Run custom form validator
        const customFormValidation = validateForm(data, schema, t);
        if (!customFormValidation.isValid) {
          customFieldErrors.push(...customFormValidation.errors);
        }

        if (customFieldErrors.length > 0) {
          setError(customFieldErrors.join('; '));
          setLoading(false);
          return;
        }
      }

      await createDocument(collection, data);
      onSuccess();
      onClose();
      setFormData({});
      setCurrentPage(0);
    } catch (err) {
      setError(err.message || t('create.failedToCreate'));
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
      setError(err.message || t('create.failedToUploadFile') || 'Failed to upload file');
    } finally {
      setUploadingFiles(prev => ({ ...prev, [fieldName]: false }));
    }
  };

  const renderFieldInput = (field) => {
    const fieldName = field.name || field;
    const fieldId = getFieldId(fieldName);
    const fieldType = (field.type || '').toLowerCase();
    const value = formData[fieldName] || '';
    const isRequired = !field.nullable;
    const isReadonly = field.readonly === true;

    // Enum field - dropdown
    if (field.enum && Array.isArray(field.enum) && field.enum.length > 0) {
      // Sort enum values alphabetically
      const sortedEnum = [...field.enum].sort((a, b) => {
        const aStr = String(a).toLowerCase();
        const bStr = String(b).toLowerCase();
        return aStr.localeCompare(bStr);
      });

      return (
        <select
          id={fieldId}
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          required={isRequired}
          disabled={isReadonly}>
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
      // Convert ISO string to datetime-local format (YYYY-MM-DDTHH:mm)
      let datetimeValue = '';
      if (value) {
        try {
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            // Format as YYYY-MM-DDTHH:mm for datetime-local
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            datetimeValue = `${year}-${month}-${day}T${hours}:${minutes}`;
          }
        } catch (e) {
          // If parsing fails, use value as is
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
      // Parse current value as array or use empty array
      let currentValues = [];
      if (value) {
        if (Array.isArray(value)) {
          currentValues = value;
        } else if (typeof value === 'string') {
          try {
            const parsed = JSON.parse(value);
            currentValues = Array.isArray(parsed) ? parsed : [parsed];
          } catch {
            // If not JSON, try comma-separated
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
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm font-mono"
          rows={4}
          value={jsonValue}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={field.example !== undefined && field.example !== null ? JSON.stringify(field.example, null, 2) : '{}'}
          required={isRequired}
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
            <p className="text-sm text-gray-500 mt-1">{t('create.uploading') || 'Uploading...'}</p>
          )}
        </div>
      );
    }

    // Email field - check if field name is "email" or type is "email" or "email_str"
    const fieldNameLower = fieldName.toLowerCase();
    if (fieldNameLower === 'email' || fieldType === 'email' || fieldType === 'email_str') {
      return (
        <input
          id={fieldId}
          type="email"
          className={`w-full px-3 py-2 border border-gray-300 rounded text-sm ${isReadonly ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={value}
          onChange={(e) => handleFieldChange(fieldName, e.target.value)}
          placeholder={field.example !== undefined && field.example !== null ? String(field.example) : 'example@email.com'}
          required={isRequired}
          readOnly={isReadonly}
          disabled={isReadonly}
        />
      );
    }

    // Default: text input for string fields
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
          <h2 className="text-2xl font-semibold">{t('create.title')}</h2>
          <div className="flex items-center gap-3">
            <div className="flex border border-gray-300 rounded overflow-hidden">
              <button
                type="button"
                onClick={() => setEditMode('form')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${editMode === 'form'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}>
                {t('create.form')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditMode('json');
                  // Generate JSON structure from schema if available
                  if (schema) {
                    generateJsonFromSchema(schema);
                  }
                }}
                className={`px-4 py-2 text-sm font-medium transition-colors ${editMode === 'json'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
                  }`}>
                {t('create.json')}
              </button>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-2xl">
              ×
            </button>
          </div>
        </div>

        {loadingSchema && editMode === 'form' && (
          <div className="mb-4 text-gray-500">{t('common.loadingSchema')}</div>
        )}

        {error && (
          <div className="mb-4 p-3 rounded bg-red-100 text-red-800 text-sm">
            {error.includes('; ') ? (
              <div>
                <div className="font-semibold mb-2">{t('validation.errors')}:</div>
                <ul className="list-disc list-inside space-y-1">
                  {error.split('; ').map((err, index) => (
                    <li key={index}>{err}</li>
                  ))}
                </ul>
              </div>
            ) : (
              error
            )}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {editMode === 'form' ? (
            <>
              {!loadingSchema && fields.length === 0 && (
                <div className="mb-4 p-3 rounded bg-yellow-100 text-yellow-800 text-sm">
                  {t('create.noSchema')}
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
                            {field.readonly && <span className="text-gray-500 ml-1 text-xs">({t('create.readonly')})</span>}
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
                <label htmlFor="id_json_data" className="block text-sm font-medium text-gray-700 mb-2">{t('create.jsonData')}</label>
              <textarea
                  id="id_json_data"
                className="w-full px-3 py-2 border border-gray-300 rounded text-sm resize-none"
                value={jsonData}
                onChange={(e) => handleJsonChange(e.target.value)}
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
              disabled={loading}
              className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700 disabled:opacity-50">
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
              {loading ? t('common.saving') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
