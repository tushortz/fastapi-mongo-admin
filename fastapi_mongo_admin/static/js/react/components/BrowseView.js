/**
 * Browse view component for displaying documents
 * @module react/components/BrowseView
 */

import { getDocuments, getSchema, deleteDocument, searchDocuments, bulkDeleteDocuments, bulkUpdateDocuments } from '../services/api.js';
import { ViewModal } from './ViewModal.js';
import { EditModal } from './EditModal.js';
import { ConfirmModal } from './ConfirmModal.js';
import { FieldSelectionModal } from './FieldSelectionModal.js';
import { ExportModal } from './ExportModal.js';
import { ImportModal } from './ImportModal.js';
import { FilterPanel } from './FilterPanel.js';
import { BulkUpdateModal } from './BulkUpdateModal.js';
import { CustomActionsModal } from './CustomActionsModal.js';
import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect, useCallback, useRef } = React;

/**
 * Browse view component
 * @param {Object} props - Component props
 */
export function BrowseView({ collection, onRefresh, onShowCreateModal, onSuccess }) {
  const [documents, setDocuments] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [sortField, setSortField] = useState('');
  const [sortOrder, setSortOrder] = useState('asc');
  const [selectedFields, setSelectedFields] = useState([]);
  const [allFields, setAllFields] = useState([]);
  const [schema, setSchema] = useState(null);
  const [filterQuery, setFilterQuery] = useState(null);
  const [viewingDoc, setViewingDoc] = useState(null);
  const [editingDoc, setEditingDoc] = useState(null);
  const [deletingDoc, setDeletingDoc] = useState(null);
  const [showFieldModal, setShowFieldModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState(new Set());
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [showBulkUpdateModal, setShowBulkUpdateModal] = useState(false);
  const [showCustomActionsModal, setShowCustomActionsModal] = useState(false);
  const [bulkAction, setBulkAction] = useState('');
  const pageSize = 100;
  const searchQueryRef = useRef(searchQuery);
  const t = useTranslation();

  // Load schema to get available fields
  useEffect(() => {
    if (collection) {
      loadSchema();
      setSelectedDocIds(new Set()); // Clear selection when collection changes
      // Load persisted field selection from localStorage
      const storageKey = `selectedFields_${collection}`;
      const savedFields = localStorage.getItem(storageKey);
      if (savedFields) {
        try {
          const parsed = JSON.parse(savedFields);
          if (Array.isArray(parsed) && parsed.length > 0) {
            // Ensure _id is always included and first
            const fieldsWithId = ['_id', ...parsed.filter(f => f !== '_id')];
            setSelectedFields(fieldsWithId);
          }
        } catch (e) {
          // Failed to parse saved fields, use defaults
        }
      }
    }
  }, [collection]);

  // Update ref when searchQuery changes
  useEffect(() => {
    searchQueryRef.current = searchQuery;
  }, [searchQuery]);

  // Load documents
  const loadDocuments = useCallback(async () => {
    if (!collection) return;

    setLoading(true);
    setError('');
    try {
      const params = {
        skip: page * pageSize,
        limit: pageSize,
      };

      // Add sorting params
      if (sortField) {
        params.sort_field = sortField;
        params.sort_order = sortOrder;
      }

      // Use ref to get latest searchQuery value (avoids dependency issues)
      const currentSearchQuery = searchQueryRef.current;

      let data;
      // Combine filter query and search query if both exist
      if (filterQuery) {
        try {
          const queryObj = JSON.parse(filterQuery);
          // If search query exists, combine it with filter query using $and
          if (currentSearchQuery) {
            // Get searchable string fields from schema
            // Exclude enum fields and date types from search
            const stringFields = [];
            if (schema && schema.fields) {
              const fieldsObj = schema.fields || {};
              const allFields = Array.isArray(fieldsObj)
                ? fieldsObj.map(f => typeof f === 'string' ? f : (f.name || f))
                : Object.keys(fieldsObj);

              // Filter to only string fields, excluding enum and date fields
              allFields.forEach(field => {
                const fieldInfo = Array.isArray(fieldsObj)
                  ? fieldsObj.find(f => (f.name || f) === field)
                  : fieldsObj[field];
                const fieldType = (fieldInfo?.type || '').toLowerCase();

                // Skip enum fields
                if (fieldInfo?.enum && Array.isArray(fieldInfo.enum) && fieldInfo.enum.length > 0) {
                  return;
                }

                // Skip date/datetime fields
                if (['date', 'datetime', 'timestamp'].includes(fieldType)) {
                  return;
                }

                // Only include string fields
                if (['str', 'string', 'text'].includes(fieldType)) {
                  stringFields.push(field);
                }
              });
            }

            // Build combined query with $and
            const combinedQuery = {
              $and: [queryObj]
            };

            // Add text search using $or with regex on string fields
            if (stringFields.length > 0) {
              combinedQuery.$and.push({
                $or: stringFields.map(field => ({
                  [field]: { $regex: currentSearchQuery, $options: 'i' }
                }))
              });
            } else {
              // Fallback: search in common fields if schema not available
              combinedQuery.$and.push({
                $or: [
                  { _id: { $regex: currentSearchQuery, $options: 'i' } }
                ]
              });
            }

            data = await searchDocuments(collection, combinedQuery, params);
          } else {
            // Only filter query, no text search
            data = await searchDocuments(collection, queryObj, params);
          }
        } catch (err) {
          // If filter query is invalid JSON, fall back to regular search
          if (currentSearchQuery) {
            params.query = currentSearchQuery;
          }
          data = await getDocuments(collection, params);
        }
      } else if (currentSearchQuery) {
        params.query = currentSearchQuery;
        data = await getDocuments(collection, params);
      } else {
        data = await getDocuments(collection, params);
      }

      setDocuments(data.documents || []);
      setTotal(data.total || 0);

      // Auto-select fields if not set and no persisted selection
      if (data.documents && data.documents.length > 0 && selectedFields.length === 0) {
        const storageKey = `selectedFields_${collection}`;
        const savedFields = localStorage.getItem(storageKey);
        if (!savedFields) {
          const fields = Object.keys(data.documents[0]);
          // Always include _id first, then other fields
          const otherFields = fields.filter(f => f !== '_id').slice(0, 9);
          const defaultFields = ['_id', ...otherFields];
          setSelectedFields(defaultFields);
          // Save default fields to localStorage
          localStorage.setItem(storageKey, JSON.stringify(defaultFields));
        }
      }
    } catch (err) {
      setError(err.message || t('browse.failedToLoad'));
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [collection, page, filterQuery, sortField, sortOrder, selectedFields.length, t]);

  // Debounced search - trigger loadDocuments 2 seconds after user stops typing
  useEffect(() => {
    // If search is cleared, trigger immediately
    if (searchQuery === '') {
      setPage(0);
      return;
    }

    // Debounce: wait 2 seconds after user stops typing
    const debounceTimer = setTimeout(() => {
      setPage(0);
    }, 2000);

    return () => clearTimeout(debounceTimer);
  }, [searchQuery]);

  // Initial load and load when non-search dependencies change
  useEffect(() => {
    loadDocuments();
  }, [collection, page, filterQuery, sortField, sortOrder, selectedFields.length]);

  const loadSchema = async () => {
    try {
      const schemaData = await getSchema(collection);
      setSchema(schemaData);
      // Convert fields object to array if needed
      const fieldsObj = schemaData.fields || {};
      const fields = Array.isArray(fieldsObj)
        ? fieldsObj.map(f => typeof f === 'string' ? f : (f.name || f))
        : Object.keys(fieldsObj);
      setAllFields(fields);

      // Only set default fields if no persisted selection exists
      const storageKey = `selectedFields_${collection}`;
      const savedFields = localStorage.getItem(storageKey);
      if (fields.length > 0 && selectedFields.length === 0 && !savedFields) {
        // Always include _id first, then other fields
        const otherFields = fields.filter(f => f !== '_id').slice(0, 9);
        const defaultFields = ['_id', ...otherFields];
        setSelectedFields(defaultFields);
        // Save default fields to localStorage
        localStorage.setItem(storageKey, JSON.stringify(defaultFields));
      }
    } catch (err) {
      // Schema loading failed, continue without schema
    }
  };

  const handleSearch = (e) => {
    // Enter key still triggers immediate search
    if (e.key === 'Enter') {
      setPage(0);
      loadDocuments();
    }
  };

  const handleRefresh = () => {
    setPage(0);
    loadDocuments();
    if (onRefresh) onRefresh();
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleDelete = async () => {
    if (!deletingDoc) return;
    const docId = deletingDoc;
    try {
      await deleteDocument(collection, docId);
      setDeletingDoc(null);
      setSelectedDocIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(docId);
        return newSet;
      });
      loadDocuments();
      if (onRefresh) onRefresh();
      // Show success notification with document ID
      if (onSuccess) {
        onSuccess(t('browse.documentDeleted', { id: docId }));
      }
    } catch (err) {
      setError(err.message || t('browse.failedToDelete'));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedDocIds.size === 0) return;
    try {
      const ids = Array.from(selectedDocIds);
      const result = await bulkDeleteDocuments(collection, ids);
      setSelectedDocIds(new Set());
      setShowBulkDeleteConfirm(false);
      loadDocuments();
      if (onRefresh) onRefresh();
      // Show success notification
      if (onSuccess) {
        onSuccess(t('browse.documentsDeleted', { count: result.deleted_count || ids.length }));
      }
    } catch (err) {
      setError(err.message || t('browse.failedToDeleteDocuments'));
      setShowBulkDeleteConfirm(false);
    }
  };

  const handleBulkUpdateSuccess = (result) => {
    setSelectedDocIds(new Set());
    loadDocuments();
    if (onRefresh) onRefresh();
    // Show success notification
    if (onSuccess) {
      onSuccess(t('browse.documentsUpdated', { count: result.updated_count || selectedDocIds.size }) || `Updated ${result.updated_count || selectedDocIds.size} document(s)`);
    }
  };

  const handleSelectDoc = (docId) => {
    setSelectedDocIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(docId)) {
        newSet.delete(docId);
      } else {
        newSet.add(docId);
      }
      return newSet;
    });
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = new Set(documents.map(doc => doc._id));
      setSelectedDocIds(allIds);
    } else {
      setSelectedDocIds(new Set());
    }
  };

  const isAllSelected = documents.length > 0 && selectedDocIds.size === documents.length;
  const isSomeSelected = selectedDocIds.size > 0 && selectedDocIds.size < documents.length;

  const handleEditSuccess = () => {
    loadDocuments();
    if (onRefresh) onRefresh();
  };

  const handleImportSuccess = () => {
    loadDocuments();
    if (onRefresh) onRefresh();
  };

  const handleApplyFilter = (query) => {
    setFilterQuery(query);
    setPage(0);
  };

  const handleClearFilter = () => {
    setFilterQuery(null);
    setPage(0);
  };

  /**
   * Format date in human-readable format: "2nd Aug 2025, 1:08 PM"
   * @param {Date|string|number} dateValue - Date value to format
   * @param {boolean} includeTime - Whether to include time in the format
   * @returns {string} Formatted date string
   */
  const formatDate = (dateValue, includeTime = true) => {
    if (!dateValue) return 'null';

    let date;
    if (dateValue instanceof Date) {
      date = dateValue;
    } else if (typeof dateValue === 'string' || typeof dateValue === 'number') {
      date = new Date(dateValue);
    } else {
      return String(dateValue);
    }

    if (isNaN(date.getTime())) {
      return String(dateValue);
    }

    // Get day with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)
    const day = date.getDate();
    const getOrdinalSuffix = (n) => {
      const j = n % 10;
      const k = n % 100;
      if (j === 1 && k !== 11) {
        return n + 'st';
      }
      if (j === 2 && k !== 12) {
        return n + 'nd';
      }
      if (j === 3 && k !== 13) {
        return n + 'rd';
      }
      return n + 'th';
    };

    // Month abbreviations
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[date.getMonth()];
    const year = date.getFullYear();

    // Format time in 12-hour format
    let timeStr = '';
    if (includeTime) {
      let hours = date.getHours();
      const minutes = date.getMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12; // 0 should be 12
      const minutesStr = minutes < 10 ? `0${minutes}` : minutes;
      timeStr = `, ${hours}:${minutesStr} ${ampm}`;
    }

    return `${getOrdinalSuffix(day)} ${month} ${year}${timeStr}`;
  };

  /**
   * Get a consistent color for an enum value
   * @param {string} value - Enum value
   * @returns {string} Tailwind CSS color class
   */
  const getEnumColor = (value) => {
    const colors = [
      'bg-blue-100 text-blue-600',
      'bg-green-100 text-green-800',
      'bg-yellow-100 text-yellow-800',
      'bg-red-100 text-red-800',
      'bg-purple-100 text-purple-800',
      'bg-pink-100 text-pink-800',
      'bg-indigo-100 text-indigo-800',
      'bg-teal-100 text-teal-800',
      'bg-orange-100 text-orange-800',
      'bg-cyan-100 text-cyan-800',
    ];
    // Use a simple hash to get consistent color for same value
    let hash = 0;
    const str = String(value);
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  /**
   * Check if a field is an enum field
   * @param {string} field - Field name
   * @returns {boolean} True if field is an enum
   */
  const isEnumField = (field) => {
    if (!schema || !schema.fields || !schema.fields[field]) {
      return false;
    }
    const fieldInfo = schema.fields[field];
    return fieldInfo.enum && Array.isArray(fieldInfo.enum) && fieldInfo.enum.length > 0;
  };

  const getFieldValue = (doc, field) => {
    const value = doc[field];
    if (value === null || value === undefined) return 'null';

    // Check if field is a date/datetime field from schema
    if (schema && schema.fields && schema.fields[field]) {
      const fieldInfo = schema.fields[field];
      const fieldType = (fieldInfo.type || '').toLowerCase();
      const fieldTypes = (fieldInfo.types || []).map(t => String(t).toLowerCase());

      // Check if it's a date or datetime field
      if (fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp' ||
        fieldTypes.includes('date') || fieldTypes.includes('datetime') || fieldTypes.includes('timestamp')) {
        // Format date (date fields don't include time, datetime/timestamp do)
        const includeTime = fieldType === 'datetime' || fieldType === 'timestamp' ||
          fieldTypes.includes('datetime') || fieldTypes.includes('timestamp');
        return formatDate(value, includeTime);
      }
    }

    // Try to detect if value is a date by checking if it's a valid date string/number
    if (typeof value === 'string' || typeof value === 'number') {
      const date = new Date(value);
      if (!isNaN(date.getTime()) && (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/) ||
        typeof value === 'string' && value.includes('T') ||
        typeof value === 'number' && value > 946684800000)) { // Rough check for timestamp
        // Likely a date - format it with time
        return formatDate(value, true);
      }
    }

    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    const stringValue = String(value);
    // Truncate _id to 8 characters
    if (field === '_id' && stringValue.length > 8) {
      return stringValue.substring(0, 8);
    }
    return stringValue;
  };

  if (loading && documents.length === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <div>{t('common.loading')}</div>
        </div>
      </div>
    );
  }

  if (error && documents.length === 0) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <div className="p-4 rounded bg-red-100 text-red-800">{error}</div>
      </div>
    );
  }

  // Always include _id as the first field, then add other selected fields
  const baseFields = documents[0] ? Object.keys(documents[0]) : [];
  const fieldsToDisplay = selectedFields.length > 0 ? selectedFields : baseFields.slice(0, 10);
  // Ensure _id is always first, and remove duplicates
  const displayFields = ['_id', ...fieldsToDisplay.filter(f => f !== '_id')];

  // Parse active filters for FilterPanel
  const activeFilters = filterQuery ? (() => {
    try {
      const parsed = JSON.parse(filterQuery);
      return Object.keys(parsed).reduce((acc, key) => {
        acc[key] = true;
        return acc;
      }, {});
    } catch {
      return {};
    }
  })() : {};

  return (
    <div className="flex flex-col">
      <FilterPanel
        collection={collection}
        schema={schema}
        onApplyFilter={handleApplyFilter}
        onClearFilter={handleClearFilter}
        activeFilters={activeFilters}
        currentFilterQuery={filterQuery}
      />
      <div className="flex gap-2.5 mb-5 flex-wrap items-center flex-shrink-0">
        <button
          onClick={onShowCreateModal}
          className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-blue-600 text-white hover:bg-blue-700">
          + {t('browse.createDocument')}
        </button>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700 disabled:opacity-50">
          {loading ? t('common.refreshing') : t('common.refresh')}
        </button>
        <button
          onClick={() => setShowFieldModal(true)}
          className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700">
          {t('browse.selectFields')}
        </button>
        <button
          onClick={() => setShowExportModal(true)}
          className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700">
          {t('common.export')}
        </button>
        <button
          onClick={() => setShowImportModal(true)}
          className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700">
          {t('common.import')}
        </button>
        <div className="flex-1 flex gap-2.5 items-center ml-5">
          <input
            type="text"
            placeholder={t('browse.searchDocuments')}
            className="flex-1 px-2.5 py-2.5 border border-gray-300 rounded text-sm bg-white text-gray-800 placeholder-gray-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleSearch}
          />
          <button
            onClick={() => {
              setPage(0);
              loadDocuments();
            }}
            className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700">
            {t('common.search')}
          </button>
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery('');
                setPage(0);
                loadDocuments();
              }}
              className="px-5 py-2.5 border-none rounded text-sm cursor-pointer transition-all font-medium bg-gray-600 text-white hover:bg-gray-700">
              {t('common.clear')}
            </button>
          )}
        </div>
      </div>
      {error && (
        <div className="p-4 rounded mb-5 bg-red-100 text-red-800">{error}</div>
      )}
      {selectedDocIds.size > 0 && (
        <div className="mb-5 p-4 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
              {selectedDocIds.size} {t('browse.documentsSelected')}
            </span>
            <button
              onClick={() => setSelectedDocIds(new Set())}
              className="text-sm text-blue-600 dark:text-blue-300 hover:text-blue-800 dark:hover:text-blue-100 underline">
              {t('browse.clearSelection')}
            </button>
          </div>
          <div className="flex items-center gap-2">
            <select
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              value={bulkAction}
              onChange={(e) => {
                const action = e.target.value;
                setBulkAction('');
                if (action === 'delete') {
                  setShowBulkDeleteConfirm(true);
                } else if (action === 'update') {
                  setShowBulkUpdateModal(true);
                } else if (action === 'custom') {
                  setShowCustomActionsModal(true);
                }
              }}>
              <option value="">{t('common.selectAction') || 'Select action...'}</option>
              <option value="update">{t('browse.bulkUpdate') || 'Bulk Update'}</option>
              <option value="delete">{t('browse.bulkDelete') || 'Bulk Delete'}</option>
              <option value="custom">{t('browse.customAction') || 'Custom Action'}</option>
            </select>
          </div>
        </div>
      )}
      {documents.length === 0 ? (
        <div className="flex-1 w-full flex items-center justify-center text-center text-gray-500">
          <div>
            <div className="text-5xl mb-5">📭</div>
            <h3 className="text-xl font-semibold mb-2">{t('browse.noDocuments')}</h3>
            <p>{t('browse.emptyCollection')}</p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col bg-white rounded-lg shadow">
          <div className="overflow-x-auto">
            <table className="border-collapse" style={{ minWidth: '100%' }}>
              <thead>
                  <tr className="bg-gray-50 dark:bg-gray-700">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase dark:text-gray-400 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={isAllSelected}
                      ref={(input) => {
                        if (input) input.indeterminate = isSomeSelected;
                      }}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="cursor-pointer"
                    />
                  </th>
                  {displayFields.map((field) => (
                    <th
                      key={field}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 dark:text-gray-400 whitespace-nowrap"
                      onClick={() => handleSort(field)}>
                      <div className="flex items-center gap-1">
                        {titleize(field)}
                        {sortField === field && (
                          <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                  ))}
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase dark:text-gray-400 whitespace-nowrap">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc, idx) => (
                  <tr key={doc._id || idx} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-600 dark:hover:text-gray-200">
                    <td className="px-4 py-3 text-sm whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedDocIds.has(doc._id)}
                        onChange={() => handleSelectDoc(doc._id)}
                        className="cursor-pointer"
                      />
                    </td>
                    {displayFields.map((field) => {
                      const fieldValue = getFieldValue(doc, field);
                      const fullValue = doc[field];
                      const fullValueStr = fullValue === null || fullValue === undefined
                        ? 'null'
                        : (typeof fullValue === 'object' ? JSON.stringify(fullValue) : String(fullValue));

                      // Check if this is an enum field
                      const isEnum = isEnumField(field);
                      const enumValue = fullValue !== null && fullValue !== undefined ? String(fullValue) : null;

                      // Check if value is null/undefined
                      const isNull = fullValue === null || fullValue === undefined || fieldValue === 'null';

                      return (
                        <td
                          key={field}
                          className="px-4 py-3 text-sm whitespace-nowrap"
                          onClick={field === '_id' ? () => setViewingDoc(doc._id) : undefined}
                          style={field === '_id' ? { cursor: 'pointer', color: '#3b82f6' } : {}}>
                          {isEnum && enumValue ? (
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEnumColor(enumValue)}`}
                              title={fullValueStr}>
                              {titleize(enumValue)}
                            </span>
                          ) : (
                            <div
                                className={`max-w-xs truncate ${field === '_id' ? 'font-mono' : ''} ${isNull ? 'text-gray-400' : ''}`}
                              title={field === '_id' ? fullValueStr : fieldValue}>
                              {fieldValue}
                            </div>
                          )}
                        </td>
                      );
                    })}
                    <td className="px-4 py-3 text-sm whitespace-nowrap">
                      <div className="flex gap-2">
                        <button
                          onClick={() => setViewingDoc(doc._id)}
                          className="px-2 py-1 text-xs bg-blue-600 text-white dark:bg-blue-900 dark:text-blue-200 rounded hover:bg-blue-700 dark:hover:bg-blue-800 font-medium">
                          {t('common.view')}
                        </button>
                        <button
                          onClick={() => setEditingDoc(doc._id)}
                          className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded hover:bg-green-200 dark:hover:bg-green-800 font-medium">
                          {t('common.edit')}
                        </button>
                        <button
                          onClick={() => setDeletingDoc(doc._id)}
                          className="px-2 py-1 text-xs bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded hover:bg-red-200 dark:hover:bg-red-800 font-medium">
                          {t('common.delete')}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-2.5 items-center justify-center p-5 border-t border-gray-200 flex-shrink-0">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-4 py-2 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 disabled:opacity-50">
              {t('common.previous')}
            </button>
            <span className="text-sm text-gray-700">
              {t('common.page')} {page + 1} {t('common.of')} {Math.ceil(total / pageSize)} ({total} {t('common.total')})
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={(page + 1) * pageSize >= total}
              className="px-4 py-2 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 disabled:opacity-50">
              {t('common.next')}
            </button>
          </div>
        </div>
      )}
      <ViewModal
        collection={collection}
        documentId={viewingDoc}
        isOpen={!!viewingDoc}
        onClose={() => setViewingDoc(null)}
      />
      <EditModal
        collection={collection}
        documentId={editingDoc}
        isOpen={!!editingDoc}
        onClose={() => setEditingDoc(null)}
        onSuccess={handleEditSuccess}
      />
      <ConfirmModal
        isOpen={!!deletingDoc}
        title={t('browse.deleteDocument')}
        message={t('browse.deleteConfirm')}
        confirmText={t('common.delete')}
        cancelText={t('common.cancel')}
        onConfirm={handleDelete}
        onCancel={() => setDeletingDoc(null)}
        variant="danger"
      />
      <ConfirmModal
        isOpen={showBulkDeleteConfirm}
        title={t('browse.bulkDeleteConfirm')}
        message={t('browse.bulkDeleteMessage', { count: selectedDocIds.size })}
        confirmText={t('browse.deleteAll')}
        cancelText={t('common.cancel')}
        onConfirm={handleBulkDelete}
        onCancel={() => setShowBulkDeleteConfirm(false)}
        variant="danger"
      />
      <BulkUpdateModal
        collection={collection}
        documentIds={selectedDocIds}
        isOpen={showBulkUpdateModal}
        onClose={() => setShowBulkUpdateModal(false)}
        onSuccess={handleBulkUpdateSuccess}
      />
      <CustomActionsModal
        collection={collection}
        documentIds={selectedDocIds}
        isOpen={showCustomActionsModal}
        onClose={() => setShowCustomActionsModal(false)}
        onExecute={async (actionData) => {
          try {
            if (actionData.type === 'custom_query') {
              setError(t('browse.customQueryNotSupported') || 'Custom queries not yet supported');
              return;
            }
            // Handle update_field action - actionData is already an array of updates
            const result = await bulkUpdateDocuments(collection, actionData);
            handleBulkUpdateSuccess(result);
          } catch (err) {
            setError(err.message || t('browse.failedToExecuteAction') || 'Failed to execute action');
          }
        }}
      />
      <FieldSelectionModal
        isOpen={showFieldModal}
        fields={allFields.length > 0 ? allFields : (documents[0] ? Object.keys(documents[0]) : [])}
        selectedFields={selectedFields}
        onClose={() => setShowFieldModal(false)}
        onApply={(fields) => {
          // Ensure _id is always included and first
          const fieldsWithId = ['_id', ...fields.filter(f => f !== '_id')];
          setSelectedFields(fieldsWithId);
          // Persist field selection to localStorage
          if (collection) {
            const storageKey = `selectedFields_${collection}`;
            localStorage.setItem(storageKey, JSON.stringify(fieldsWithId));
          }
        }}
      />
      <ExportModal
        collection={collection}
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
      />
      <ImportModal
        collection={collection}
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onSuccess={handleImportSuccess}
      />
    </div>
  );
}
