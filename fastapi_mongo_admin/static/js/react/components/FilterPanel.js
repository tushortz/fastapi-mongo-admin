/**
 * Filter panel component for advanced filtering
 * @module react/components/FilterPanel
 */

import { getSchema } from '../services/api.js';
import { titleize } from '../utils.js';

const { useState, useEffect } = React;

/**
 * Filter panel component
 * @param {Object} props - Component props
 */
export function FilterPanel({ collection, schema, onApplyFilter, onClearFilter }) {
  const [filters, setFilters] = useState({});
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (collection) {
      setFilters({});
    }
  }, [collection]);

  if (!schema || !schema.fields) {
    return null;
  }

  // Convert fields object to array of field objects with names
  const fieldsObj = schema.fields || {};
  const fields = Array.isArray(fieldsObj)
    ? fieldsObj
    : Object.entries(fieldsObj).map(([name, fieldInfo]) => ({
        name,
        ...fieldInfo
      }));

  // Only show filters for enum, date, and boolean fields
  const filterableFields = fields.filter(field => {
    const fieldType = (field.type || '').toLowerCase();
    // Check for enum fields
    if (field.enum && Array.isArray(field.enum) && field.enum.length > 0) {
      return true;
    }
    // Check for boolean fields
    if (fieldType === 'bool' || fieldType === 'boolean') {
      return true;
    }
    // Check for date/datetime fields
    if (fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp') {
      return true;
    }
    return false;
  });

  if (filterableFields.length === 0) {
    return null;
  }

  const handleFilterChange = (fieldName, value) => {
    const newFilters = { ...filters };
    if (value === '' || value === null || value === undefined) {
      delete newFilters[fieldName];
    } else {
      newFilters[fieldName] = value;
    }
    setFilters(newFilters);
  };

  const handleApply = () => {
    if (Object.keys(filters).length === 0) {
      onClearFilter();
      return;
    }

    // Build MongoDB query from filters
    const query = {};
    Object.entries(filters).forEach(([field, value]) => {
      if (value) {
        const fieldInfo = fields.find(f => {
          const fieldName = typeof f === 'string' ? f : (f.name || f);
          return fieldName === field;
        });
        const fieldType = (fieldInfo?.type || '').toLowerCase();

        // Enum field - exact match
        if (fieldInfo?.enum && Array.isArray(fieldInfo.enum)) {
          query[field] = value;
        }
        // Boolean field
        else if (fieldType === 'bool' || fieldType === 'boolean') {
          query[field] = value === 'true' || value === true;
        }
        // Date/datetime field
        else if (fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp') {
          // For date fields, match the entire day
          const date = new Date(value);
          const startOfDay = new Date(date);
          startOfDay.setHours(0, 0, 0, 0);
          const endOfDay = new Date(date);
          endOfDay.setHours(23, 59, 59, 999);
          query[field] = {
            $gte: startOfDay.toISOString(),
            $lte: endOfDay.toISOString()
          };
        }
      }
    });

    onApplyFilter(JSON.stringify(query));
  };

  const handleClear = () => {
    setFilters({});
    onClearFilter();
  };

  const renderFilterInput = (field) => {
    const fieldType = (field.type || '').toLowerCase();
    const fieldName = field.name || field;
    const currentValue = filters[fieldName] || '';

    // Enum field - show dropdown with enum values
    if (field.enum && Array.isArray(field.enum) && field.enum.length > 0) {
      // Sort enum values alphabetically
      const sortedEnum = [...field.enum].sort((a, b) => {
        const aStr = String(a).toLowerCase();
        const bStr = String(b).toLowerCase();
        return aStr.localeCompare(bStr);
      });

      return (
        <select
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
          value={currentValue}
          onChange={(e) => handleFilterChange(fieldName, e.target.value)}>
          <option value="">All</option>
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
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm bg-white"
          value={currentValue}
          onChange={(e) => handleFilterChange(fieldName, e.target.value)}>
          <option value="">All</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      );
    }

    // Date/datetime field
    if (fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp') {
      return (
        <input
          type="date"
          className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
          value={currentValue}
          onChange={(e) => handleFilterChange(fieldName, e.target.value)}
        />
      );
    }

    // Fallback (shouldn't reach here if filterableFields is correct)
    return null;
  };

  return (
    <div className="mb-5">
      <button
        onClick={() => setShowFilters(!showFilters)}
        className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700 mb-3">
        {showFilters ? '▼ Hide Filters' : '▶ Show Filters'}
      </button>

      {showFilters && (
        <div className="bg-white rounded-lg shadow p-5">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            {filterableFields.map((field) => {
              const fieldName = field.name || field;
              return (
                <div key={fieldName}>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {titleize(fieldName)}
                  </label>
                  {renderFilterInput(field)}
                </div>
              );
            })}
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleApply}
              className="px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
              Apply Filters
            </button>
            <button
              onClick={handleClear}
              className="px-4 py-2 bg-gray-600 text-white rounded text-sm font-medium hover:bg-gray-700">
              Clear Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

