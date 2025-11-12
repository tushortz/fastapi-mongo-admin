/**
 * Table utilities and virtual scrolling
 * @module table
 */

/**
 * Virtual scrolling table renderer
 */
export class VirtualTable {
  constructor(container, options = {}) {
    this.container = container;
    this.rowHeight = options.rowHeight || 40;
    this.visibleRows = options.visibleRows || 20;
    this.data = [];
    this.scrollTop = 0;
    this.init();
  }

  init() {
    this.container.style.position = 'relative';
    this.container.style.overflow = 'auto';
    this.container.style.height = `${this.visibleRows * this.rowHeight}px`;

    this.container.addEventListener('scroll', () => {
      this.handleScroll();
    });
  }

  /**
   * Set table data
   * @param {Array} data - Table data
   */
  setData(data) {
    this.data = data;
    this.render();
  }

  /**
   * Handle scroll event
   */
  handleScroll() {
    this.scrollTop = this.container.scrollTop;
    this.render();
  }

  /**
   * Render visible rows
   */
  render() {
    const startIndex = Math.floor(this.scrollTop / this.rowHeight);
    const endIndex = Math.min(startIndex + this.visibleRows + 2, this.data.length);

    // Calculate offset for smooth scrolling
    const offset = startIndex * this.rowHeight;
    const visibleData = this.data.slice(startIndex, endIndex);

    // Render visible rows
    // This would be implemented based on your table structure
  }
}

/**
 * Make table columns resizable
 * @param {HTMLElement} table - Table element
 */
export function makeColumnsResizable(table) {
  const headers = table.querySelectorAll('thead th');
  let startX, startWidth, column;

  headers.forEach((header, index) => {
    if (index === headers.length - 1) return; // Skip last column (Actions)

    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'resize-handle';
    resizeHandle.style.cssText = `
      position: absolute;
      right: 0;
      top: 0;
      width: 5px;
      height: 100%;
      cursor: col-resize;
      user-select: none;
      background: transparent;
    `;

    header.style.position = 'relative';
    header.appendChild(resizeHandle);

    resizeHandle.addEventListener('mousedown', (e) => {
      e.preventDefault();
      startX = e.pageX;
      startWidth = header.offsetWidth;
      column = header;

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    });

    function handleMouseMove(e) {
      const width = startWidth + (e.pageX - startX);
      if (width > 50) { // Minimum width
        column.style.width = `${width}px`;
        // Update all cells in this column
        const colIndex = Array.from(headers).indexOf(column);
        const cells = table.querySelectorAll(`tbody td:nth-child(${colIndex + 1})`);
        cells.forEach(cell => {
          cell.style.width = `${width}px`;
        });
      }
    }

    function handleMouseUp() {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    }
  });
}

/**
 * Add column sorting indicators
 * @param {HTMLElement} table - Table element
 */
export function enhanceTableSorting(table) {
  const headers = table.querySelectorAll('thead th[onclick]');
  headers.forEach(header => {
    header.style.cursor = 'pointer';
    header.style.userSelect = 'none';

    header.addEventListener('mouseenter', () => {
      if (!header.querySelector('.sort-indicator')) {
        const indicator = document.createElement('span');
        indicator.className = 'sort-indicator text-gray-400 ml-1';
        indicator.textContent = '↕';
        header.appendChild(indicator);
      }
    });
  });
}

