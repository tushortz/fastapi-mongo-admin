/**
 * API service for making HTTP requests
 * @module react/services/api
 */

import { getApiBase, formatError } from '../utils.js';

const API_BASE = getApiBase();

/**
 * Make a fetch request with error handling
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<*>} Response data
 */
export async function apiRequest(endpoint, options = {}) {
  try {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: response.statusText
      }));
      throw new Error(errorData.error || errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * Get all collections
 * @returns {Promise<Array<string>>} List of collection names
 */
export async function getCollections() {
  const data = await apiRequest('/collections');
  return data.collections || [];
}

/**
 * Get documents from a collection
 * @param {string} collection - Collection name
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Documents data
 */
export async function getDocuments(collection, params = {}) {
  const queryParams = new URLSearchParams();
  if (params.skip !== undefined) queryParams.append('skip', params.skip);
  if (params.limit !== undefined) queryParams.append('limit', params.limit);
  if (params.query) queryParams.append('query', params.query);
  if (params.sort_field) queryParams.append('sort_field', params.sort_field);
  if (params.sort_order) queryParams.append('sort_order', params.sort_order);

  return await apiRequest(`/collections/${collection}/documents?${queryParams}`);
}

/**
 * Search documents using MongoDB query
 * @param {string} collection - Collection name
 * @param {Object} query - MongoDB query object
 * @param {Object} params - Additional parameters
 * @returns {Promise<Object>} Search results
 */
export async function searchDocuments(collection, query, params = {}) {
  const queryParams = new URLSearchParams();
  if (params.skip !== undefined) queryParams.append('skip', params.skip);
  if (params.limit !== undefined) queryParams.append('limit', params.limit);
  if (params.sort_field) queryParams.append('sort_field', params.sort_field);
  if (params.sort_order) queryParams.append('sort_order', params.sort_order);

  return await apiRequest(`/collections/${collection}/documents/search?${queryParams}`, {
    method: 'POST',
    body: JSON.stringify(query),
  });
}

/**
 * Get a single document by ID
 * @param {string} collection - Collection name
 * @param {string} documentId - Document ID
 * @returns {Promise<Object>} Document data
 */
export async function getDocument(collection, documentId) {
  return await apiRequest(`/collections/${collection}/documents/${documentId}`);
}

/**
 * Get schema for a collection
 * @param {string} collection - Collection name
 * @returns {Promise<Object>} Schema data
 */
export async function getSchema(collection) {
  return await apiRequest(`/collections/${collection}/schema`);
}

/**
 * Get analytics data for a collection
 * @param {string} collection - Collection name
 * @param {Object} params - Analytics parameters
 * @returns {Promise<Object>} Analytics data
 */
export async function getAnalytics(collection, params = {}) {
  const queryParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) queryParams.append(key, value);
  });
  return await apiRequest(`/collections/${collection}/analytics?${queryParams}`);
}

/**
 * Create a document
 * @param {string} collection - Collection name
 * @param {Object} data - Document data
 * @returns {Promise<Object>} Created document
 */
export async function createDocument(collection, data) {
  return await apiRequest(`/collections/${collection}/documents`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update a document
 * @param {string} collection - Collection name
 * @param {string} documentId - Document ID
 * @param {Object} data - Document data
 * @returns {Promise<Object>} Updated document
 */
export async function updateDocument(collection, documentId, data) {
  return await apiRequest(`/collections/${collection}/documents/${documentId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a document
 * @param {string} collection - Collection name
 * @param {string} documentId - Document ID
 * @returns {Promise<void>}
 */
export async function deleteDocument(collection, documentId) {
  return await apiRequest(`/collections/${collection}/documents/${documentId}`, {
    method: 'DELETE',
  });
}

/**
 * Bulk delete documents
 * @param {string} collection - Collection name
 * @param {Array<string>} documentIds - Array of document IDs to delete
 * @returns {Promise<Object>} Bulk delete result
 */
export async function bulkDeleteDocuments(collection, documentIds) {
  return await apiRequest(`/collections/${collection}/documents/bulk`, {
    method: 'DELETE',
    body: JSON.stringify({ document_ids: documentIds }),
  });
}

/**
 * Bulk update documents
 * @param {string} collection - Collection name
 * @param {Array<Object>} updates - Array of update objects with _id and data
 * @returns {Promise<Object>} Bulk update result
 */
export async function bulkUpdateDocuments(collection, updates) {
  return await apiRequest(`/collections/${collection}/documents/bulk`, {
    method: 'PUT',
    body: JSON.stringify({ updates }),
  });
}

/**
 * Export collection
 * @param {string} collection - Collection name
 * @param {string} format - Export format (csv, html, json, toml, xml, yaml)
 * @param {string} query - Optional query string
 * @returns {Promise<void>} Triggers download
 */
export async function exportCollection(collection, format = 'json', query = null) {
  let url = `${API_BASE}/collections/${collection}/export?format=${format}`;
  if (query) {
    url += `&query=${encodeURIComponent(query)}`;
  }

  // Trigger download
  const link = document.createElement('a');
  link.href = url;
  link.download = `${collection}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Import collection
 * @param {string} collection - Collection name
 * @param {File} file - File to import
 * @param {string} format - Import format
 * @param {boolean} overwrite - Overwrite existing documents
 * @returns {Promise<Object>} Import result
 */
export async function importCollection(collection, file, format, overwrite = false) {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_BASE}/collections/${collection}/import?format=${format}&overwrite=${overwrite}`;
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.error || errorData.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * Upload a file
 * @param {File} file - File to upload
 * @param {string} collectionName - Optional collection name for organization
 * @returns {Promise<Object>} Upload result with URL
 */
export async function uploadFile(file, collectionName = null) {
  const formData = new FormData();
  formData.append('file', file);

  let url = `${API_BASE}/files/upload`;
  if (collectionName) {
    url += `?collection_name=${encodeURIComponent(collectionName)}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(errorData.error || errorData.detail || `HTTP ${response.status}`);
  }

  return await response.json();
}

/**
 * Delete an uploaded file
 * @param {string} filePath - Path to the file relative to uploads directory
 * @returns {Promise<Object>} Delete result
 */
export async function deleteFile(filePath) {
  return await apiRequest(`/files/${filePath}`, {
    method: 'DELETE',
  });
}
