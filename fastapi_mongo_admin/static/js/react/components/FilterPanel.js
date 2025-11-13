/**
 * Filter panel component for advanced filtering
 * @module react/components/FilterPanel
 */

import { getSchema } from '../services/api.js';
import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';
import { DateHierarchy } from './DateHierarchy.js';

const { useState, useEffect } = React;

/**
 * Filter panel component
 * @param {Object} props - Component props
 */
export function FilterPanel({ collection, schema, onApplyFilter, onClearFilter, activeFilters = {}, currentFilterQuery = null }) {
  const [filters, setFilters] = useState({});
  const [showFilters, setShowFilters] = useState(false);
  const [isSidebar, setIsSidebar] = useState(true); // Sidebar mode by default
  const t = useTranslation();

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
          <option value="">{t('common.all')}</option>
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
          <option value="">{t('common.all')}</option>
          <option value="true">{t('common.true')}</option>
          <option value="false">{t('common.false')}</option>
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

  // Quick filters for common scenarios
  const quickFilters = [
    {
      label: t('filter.last7Days') || 'Last 7 Days',
      type: 'last7Days',
      query: () => {
        const today = new Date();
        const sevenDaysAgo = new Date(today);
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        // Find first date field
        const dateField = filterableFields.find(f => {
          const fieldType = (f.type || '').toLowerCase();
          return fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp';
        });
        if (dateField) {
          const fieldName = dateField.name || dateField;
          return JSON.stringify({
            [fieldName]: {
              $gte: sevenDaysAgo.toISOString(),
              $lte: today.toISOString()
            }
          });
        }
        return null;
      }
    },
    {
      label: t('filter.last30Days') || 'Last 30 Days',
      type: 'last30Days',
      query: () => {
        const today = new Date();
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        const dateField = filterableFields.find(f => {
          const fieldType = (f.type || '').toLowerCase();
          return fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp';
        });
        if (dateField) {
          const fieldName = dateField.name || dateField;
          return JSON.stringify({
            [fieldName]: {
              $gte: thirtyDaysAgo.toISOString(),
              $lte: today.toISOString()
            }
          });
        }
        return null;
      }
    },
    {
      label: t('filter.today') || 'Today',
      type: 'today',
      query: () => {
        const today = new Date();
        const startOfDay = new Date(today);
        startOfDay.setHours(0, 0, 0, 0);
        const endOfDay = new Date(today);
        endOfDay.setHours(23, 59, 59, 999);
        const dateField = filterableFields.find(f => {
          const fieldType = (f.type || '').toLowerCase();
          return fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp';
        });
        if (dateField) {
          const fieldName = dateField.name || dateField;
          return JSON.stringify({
            [fieldName]: {
              $gte: startOfDay.toISOString(),
              $lte: endOfDay.toISOString()
            }
          });
        }
        return null;
      }
    }
  ];

  const handleQuickFilter = (quickFilter) => {
    const query = quickFilter.query();
    if (query) {
      onApplyFilter(query);
    }
  };

  // Check if a quick filter is currently active
  const isQuickFilterActive = (quickFilter) => {
    if (!currentFilterQuery) return false;
    try {
      const quickFilterQuery = quickFilter.query();
      if (!quickFilterQuery) return false;

      // Parse both queries for comparison
      const currentQuery = JSON.parse(currentFilterQuery);
      const quickQuery = JSON.parse(quickFilterQuery);

      // Compare the queries - check if all keys and values match
      const currentKeys = Object.keys(currentQuery);
      const quickKeys = Object.keys(quickQuery);

      if (currentKeys.length !== quickKeys.length) return false;

      // Check if all keys match and their values are equivalent
      for (const key of quickKeys) {
        if (!currentQuery[key]) return false;

        const currentValue = currentQuery[key];
        const quickValue = quickQuery[key];

        // Handle date range objects with $gte and $lte
        if (typeof currentValue === 'object' && typeof quickValue === 'object') {
          if (currentValue.$gte && currentValue.$lte && quickValue.$gte && quickValue.$lte) {
            // Use the quick filter type to determine the pattern to match
            const currentStart = new Date(currentValue.$gte);
            const currentEnd = new Date(currentValue.$lte);
            const currentDuration = currentEnd.getTime() - currentStart.getTime();
            const now = new Date();

            // Match based on quick filter type
            if (quickFilter.type === 'today') {
              // Check if current range covers today
              const currentStartDate = new Date(currentStart.getFullYear(), currentStart.getMonth(), currentStart.getDate());
              const todayStartDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
              return currentStartDate.getTime() === todayStartDate.getTime() &&
                currentDuration <= 86400000; // ~1 day
            } else if (quickFilter.type === 'last7Days') {
              // Check if current range is approximately 7 days and ends close to now
              const daysDiff = Math.abs((currentEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
              return daysDiff <= 1 &&
                currentDuration >= 6 * 86400000 &&
                currentDuration <= 8 * 86400000; // 6-8 days
            } else if (quickFilter.type === 'last30Days') {
              // Check if current range is approximately 30 days and ends close to now
              const daysDiff = Math.abs((currentEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
              return daysDiff <= 1 &&
                currentDuration >= 29 * 86400000 &&
                currentDuration <= 31 * 86400000; // 29-31 days
            }

            // Fallback: check if dates are very close (within 1 hour) - for other quick filter types
            const quickStart = new Date(quickValue.$gte);
            const quickEnd = new Date(quickValue.$lte);
            const startDiff = Math.abs(currentStart.getTime() - quickStart.getTime());
            const endDiff = Math.abs(currentEnd.getTime() - quickEnd.getTime());
            return startDiff <= 3600000 && endDiff <= 3600000;
          } else {
            // For other objects, do deep comparison
            if (JSON.stringify(currentValue) !== JSON.stringify(quickValue)) {
              return false;
            }
          }
        } else if (currentValue !== quickValue) {
          return false;
        }
      }

      return true;
    } catch (e) {
      return false;
    }
  };

  // Sidebar layout
  if (isSidebar) {
    return (
      <>
        {/* Sidebar */}
        {showFilters && (
          <div
            className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 p-4 z-40 overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{t('filter.filters') || 'Filters'}</h3>
              <button
                onClick={() => setShowFilters(false)}
                className="text-gray-500 hover:text-gray-700">
                ×
              </button>
            </div>

            {/* Date Hierarchy */}
            {(() => {
              const dateField = filterableFields.find(f => {
                const fieldType = (f.type || '').toLowerCase();
                return fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp';
              });
              if (dateField) {
                const fieldName = dateField.name || dateField;
                return (
                  <div className="mb-6">
                    <DateHierarchy
                      fieldName={titleize(fieldName)}
                      onDateSelect={(dateRange) => {
                        if (dateRange) {
                          onApplyFilter(JSON.stringify({ [fieldName]: dateRange }));
                        } else {
                          onClearFilter();
                        }
                      }}
                    />
                  </div>
                );
              }
              return null;
            })()}

            {/* Quick Filters */}
            {quickFilters.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  {t('filter.quickFilters') || 'Quick Filters'}
                </h4>
                <div className="space-y-2">
                  {quickFilters.map((qf, idx) => {
                    const isActive = isQuickFilterActive(qf);
                    return (
                      <button
                        key={idx}
                        onClick={() => handleQuickFilter(qf)}
                        className={`w-full text-left px-3 py-2 text-sm rounded ${isActive
                          ? 'bg-blue-600 text-white hover:bg-blue-700 font-medium'
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                          }`}>
                        {qf.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Field Filters */}
            <div className="space-y-4 max-h-[calc(100vh-300px)] overflow-y-auto">
              {filterableFields.map((field) => {
                const fieldName = field.name || field;
                const isActive = activeFilters[fieldName];
                return (
                  <div key={fieldName} className={isActive ? 'bg-blue-50 p-2 rounded' : ''}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {titleize(fieldName)}
                      {isActive && <span className="ml-2 text-blue-600">●</span>}
                    </label>
                    {renderFilterInput(field)}
                  </div>
                );
              })}
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 space-y-2">
              <button
                onClick={handleApply}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
                {t('filter.applyFilters') || 'Apply Filters'}
              </button>
              <button
                onClick={handleClear}
                className="w-full px-4 py-2 bg-gray-600 text-white rounded text-sm font-medium hover:bg-gray-700">
                {t('filter.clearFilters') || 'Clear Filters'}
              </button>
            </div>
          </div>
        )}

        {/* Toggle Button */}
        {!showFilters && (
          <button
            onClick={() => setShowFilters(true)}
            className="fixed left-0 top-1/2 transform -translate-y-1/2 bg-blue-600 text-white px-2 py-4 rounded-r-lg shadow-lg hover:bg-blue-700 z-40">
            <span className="text-sm">▶</span>
          </button>
        )}
      </>
    );
  }

  // Original inline layout (fallback)
  return (
    <div className="mb-5">
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700">
          {showFilters ? `▼ ${t('filter.hideFilters')}` : `▶ ${t('filter.showFilters')}`}
        </button>
        <button
          onClick={() => setIsSidebar(true)}
          className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800">
          {t('filter.sidebarMode') || 'Sidebar Mode'}
        </button>
      </div>

      {showFilters && (
        <div className="bg-white rounded-lg shadow p-5">
          {/* Quick Filters */}
          {quickFilters.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                {t('filter.quickFilters') || 'Quick Filters'}
              </h4>
              <div className="flex gap-2 flex-wrap">
                {quickFilters.map((qf, idx) => {
                  const isActive = isQuickFilterActive(qf);
                  return (
                    <button
                      key={idx}
                      onClick={() => handleQuickFilter(qf)}
                      className={`px-3 py-1 text-sm rounded ${isActive
                        ? 'bg-blue-600 text-white hover:bg-blue-700 font-medium'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                        }`}>
                      {qf.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

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
              {t('filter.applyFilters') || 'Apply Filters'}
            </button>
            <button
              onClick={handleClear}
              className="px-4 py-2 bg-gray-600 text-white rounded text-sm font-medium hover:bg-gray-700">
              {t('filter.clearFilters') || 'Clear Filters'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

