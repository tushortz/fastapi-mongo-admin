/**
 * API client for admin dashboard
 * @module api
 */

import { ApiCache, batchApiCalls, formatError } from './utils.js';

/**
 * API client class
 */
export class ApiClient {
  constructor(baseUrl = '/admin') {
    this.baseUrl = baseUrl;
    this.cache = new ApiCache(60000); // 1 minute TTL
  }

  /**
   * Make a cached fetch request
   * @param {string} url - Request URL
   * @param {Object} options - Fetch options
   * @param {boolean} useCache - Whether to use cache
   * @returns {Promise<*>} Response data
   */
  async fetch(url, options = {}, useCache = true) {
    const cacheKey = `${url}_${JSON.stringify(options)}`;

    if (useCache && options.method === 'GET') {
      const cached = this.cache.get(cacheKey);
      if (cached) return cached;
    }

    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(formatError(error));
      }

      const data = await response.json();

      if (useCache && options.method === 'GET') {
        this.cache.set(cacheKey, data);
      }

      return data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Get collections list
   * @returns {Promise<Object>} Collections data
   */
  async getCollections() {
    return this.fetch(`${this.baseUrl}/collections`);
  }

  /**
   * Get collection schema
   * @param {string} collectionName - Collection name
   * @param {number} sampleSize - Sample size for schema inference
   * @returns {Promise<Object>} Schema data
   */
  async getSchema(collectionName, sampleSize = 10) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/schema?sample_size=${sampleSize}`);
  }

  /**
   * List documents
   * @param {string} collectionName - Collection name
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Documents data
   */
  async listDocuments(collectionName, params = {}) {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.query) queryParams.append('query', params.query);
    if (params.sort_field) queryParams.append('sort_field', params.sort_field);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents?${queryParams}`);
  }

  /**
   * Search documents
   * @param {string} collectionName - Collection name
   * @param {Object} query - MongoDB query
   * @param {Object} params - Additional parameters
   * @returns {Promise<Object>} Search results
   */
  async searchDocuments(collectionName, query, params = {}) {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.sort_field) queryParams.append('sort_field', params.sort_field);
    if (params.sort_order) queryParams.append('sort_order', params.sort_order);

    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents/search?${queryParams}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(query)
    }, false); // Don't cache search results
  }

  /**
   * Get single document
   * @param {string} collectionName - Collection name
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>} Document data
   */
  async getDocument(collectionName, documentId) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents/${documentId}`);
  }

  /**
   * Create document
   * @param {string} collectionName - Collection name
   * @param {Object} data - Document data
   * @returns {Promise<Object>} Created document
   */
  async createDocument(collectionName, data) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }, false);
  }

  /**
   * Update document
   * @param {string} collectionName - Collection name
   * @param {string} documentId - Document ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} Updated document
   */
  async updateDocument(collectionName, documentId, data) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents/${documentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }, false);
  }

  /**
   * Delete document
   * @param {string} collectionName - Collection name
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>} Deletion result
   */
  async deleteDocument(collectionName, documentId) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents/${documentId}`, {
      method: 'DELETE'
    }, false);
  }

  /**
   * Bulk create documents
   * @param {string} collectionName - Collection name
   * @param {Array<Object>} documents - Documents to create
   * @returns {Promise<Object>} Bulk create result
   */
  async bulkCreate(collectionName, documents) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documents })
    }, false);
  }

  /**
   * Bulk update documents
   * @param {string} collectionName - Collection name
   * @param {Array<Object>} updates - Updates array
   * @returns {Promise<Object>} Bulk update result
   */
  async bulkUpdate(collectionName, updates) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents/bulk`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ updates })
    }, false);
  }

  /**
   * Bulk delete documents
   * @param {string} collectionName - Collection name
   * @param {Array<string>} documentIds - Document IDs to delete
   * @returns {Promise<Object>} Bulk delete result
   */
  async bulkDelete(collectionName, documentIds) {
    return this.fetch(`${this.baseUrl}/collections/${collectionName}/documents/bulk`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_ids: documentIds })
    }, false);
  }

  /**
   * Export collection
   * @param {string} collectionName - Collection name
   * @param {string} format - Export format
   * @param {string} query - Optional query string
   * @returns {Promise<void>} Triggers download
   */
  async exportCollection(collectionName, format = 'json', query = null) {
    let url = `${this.baseUrl}/collections/${collectionName}/export?format=${format}`;
    if (query) {
      url += `&query=${encodeURIComponent(query)}`;
    }

    // Trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = `${collectionName}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Import collection
   * @param {string} collectionName - Collection name
   * @param {File} file - File to import
   * @param {string} format - Import format
   * @param {boolean} overwrite - Overwrite existing documents
   * @returns {Promise<Object>} Import result
   */
  async importCollection(collectionName, file, format, overwrite = false) {
    const formData = new FormData();
    formData.append('file', file);

    return this.fetch(
      `${this.baseUrl}/collections/${collectionName}/import?format=${format}&overwrite=${overwrite}`,
      {
        method: 'POST',
        body: formData
      },
      false
    );
  }

  /**
   * Batch load collection data (documents + schema)
   * @param {string} collectionName - Collection name
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Combined data
   */
  async batchLoadCollectionData(collectionName, params = {}) {
    const [documents, schema] = await batchApiCalls([
      this.listDocuments(collectionName, params),
      this.getSchema(collectionName)
    ]);

    return { documents, schema };
  }
}

