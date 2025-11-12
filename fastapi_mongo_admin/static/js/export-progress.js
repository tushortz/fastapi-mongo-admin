/**
 * Export progress tracking and resume functionality
 * @module export-progress
 */

/**
 * Export progress manager
 */
export class ExportProgressManager {
  constructor() {
    this.activeExports = new Map();
  }

  /**
   * Start export with progress tracking
   * @param {string} collectionName - Collection name
   * @param {string} format - Export format
   * @param {Object} options - Export options
   * @returns {Promise<void>}
   */
  async startExport(collectionName, format, options = {}) {
    const exportId = `${collectionName}_${format}_${Date.now()}`;

    // Create progress tracker
    const progress = {
      id: exportId,
      collectionName,
      format,
      status: 'starting',
      progress: 0,
      total: null,
      startTime: Date.now(),
      chunks: [],
      error: null
    };

    this.activeExports.set(exportId, progress);

    try {
      // Show progress UI
      this.showProgressUI(progress);

      // Start export
      const url = this.buildExportUrl(collectionName, format, options);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Handle streaming response
      const reader = response.body.getReader();
      const contentLength = response.headers.get('content-length');
      if (contentLength) {
        progress.total = parseInt(contentLength, 10);
      }

      let received = 0;
      const chunks = [];

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        chunks.push(value);
        received += value.length;

        if (progress.total) {
          progress.progress = (received / progress.total) * 100;
        } else {
          progress.progress = Math.min(progress.progress + 10, 90);
        }

        this.updateProgress(progress);
      }

      // Combine chunks
      const blob = new Blob(chunks);
      const url_obj = URL.createObjectURL(blob);

      // Trigger download
      const link = document.createElement('a');
      link.href = url_obj;
      link.download = `${collectionName}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url_obj);

      progress.status = 'completed';
      progress.progress = 100;
      this.updateProgress(progress);

      // Remove after delay
      setTimeout(() => {
        this.activeExports.delete(exportId);
        this.hideProgressUI(exportId);
      }, 3000);

    } catch (error) {
      progress.status = 'error';
      progress.error = error.message;
      this.updateProgress(progress);
    }
  }

  /**
   * Build export URL
   * @param {string} collectionName - Collection name
   * @param {string} format - Export format
   * @param {Object} options - Export options
   * @returns {string} Export URL
   */
  buildExportUrl(collectionName, format, options) {
    const baseUrl = '/admin';
    let url = `${baseUrl}/collections/${collectionName}/export?format=${format}`;

    if (options.query) {
      url += `&query=${encodeURIComponent(options.query)}`;
    }

    return url;
  }

  /**
   * Show progress UI
   * @param {Object} progress - Progress object
   */
  showProgressUI(progress) {
    const container = document.getElementById('export-progress-container') || this.createProgressContainer();

    const progressEl = document.createElement('div');
    progressEl.id = `export-progress-${progress.id}`;
    progressEl.className = 'export-progress-item mb-3 p-3 bg-blue-50 rounded border border-blue-200';
    progressEl.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">Exporting ${progress.collectionName}.${progress.format}</span>
        <button onclick="exportProgressManager.cancelExport('${progress.id}')" class="text-red-600 hover:text-red-800 text-sm">×</button>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: ${progress.progress}%"></div>
      </div>
      <div class="text-xs text-gray-600 mt-1">${Math.round(progress.progress)}%</div>
    `;

    container.appendChild(progressEl);
  }

  /**
   * Update progress UI
   * @param {Object} progress - Progress object
   */
  updateProgress(progress) {
    const progressEl = document.getElementById(`export-progress-${progress.id}`);
    if (!progressEl) return;

    const bar = progressEl.querySelector('.bg-blue-600');
    const percent = progressEl.querySelector('.text-xs');

    if (bar) {
      bar.style.width = `${progress.progress}%`;
    }
    if (percent) {
      percent.textContent = `${Math.round(progress.progress)}%`;
    }

    if (progress.status === 'completed') {
      progressEl.classList.remove('bg-blue-50', 'border-blue-200');
      progressEl.classList.add('bg-green-50', 'border-green-200');
    } else if (progress.status === 'error') {
      progressEl.classList.remove('bg-blue-50', 'border-blue-200');
      progressEl.classList.add('bg-red-50', 'border-red-200');
      const errorMsg = document.createElement('div');
      errorMsg.className = 'text-red-600 text-xs mt-1';
      errorMsg.textContent = progress.error;
      progressEl.appendChild(errorMsg);
    }
  }

  /**
   * Hide progress UI
   * @param {string} exportId - Export ID
   */
  hideProgressUI(exportId) {
    const progressEl = document.getElementById(`export-progress-${exportId}`);
    if (progressEl) {
      progressEl.remove();
    }
  }

  /**
   * Create progress container if it doesn't exist
   * @returns {HTMLElement} Progress container
   */
  createProgressContainer() {
    const container = document.createElement('div');
    container.id = 'export-progress-container';
    container.className = 'fixed top-20 right-4 w-80 z-50';
    document.body.appendChild(container);
    return container;
  }

  /**
   * Cancel export
   * @param {string} exportId - Export ID
   */
  cancelExport(exportId) {
    this.activeExports.delete(exportId);
    this.hideProgressUI(exportId);
  }
}

// Global instance
export const exportProgressManager = new ExportProgressManager();

