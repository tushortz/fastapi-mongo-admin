/**
 * Advanced MongoDB Query Builder UI
 * @module query-builder
 */

/**
 * Query builder class for constructing MongoDB queries visually
 */
export class QueryBuilder {
  constructor(container, options = {}) {
    this.container = container;
    this.rules = [];
    this.logicalOperator = 'and'; // 'and' or 'or'
    this.onChange = options.onChange || (() => {});
    this.schema = options.schema || {};
    this.init();
  }

  init() {
    this.render();
  }

  /**
   * Add a new query rule
   */
  addRule() {
    this.rules.push({
      field: '',
      operator: 'equals',
      value: '',
      id: Date.now() + Math.random()
    });
    this.render();
    this.onChange(this.getQuery());
  }

  /**
   * Remove a query rule
   * @param {string} ruleId - Rule ID to remove
   */
  removeRule(ruleId) {
    this.rules = this.rules.filter(r => r.id !== ruleId);
    this.render();
    this.onChange(this.getQuery());
  }

  /**
   * Update a rule
   * @param {string} ruleId - Rule ID
   * @param {Object} updates - Updates to apply
   */
  updateRule(ruleId, updates) {
    const rule = this.rules.find(r => r.id === ruleId);
    if (rule) {
      Object.assign(rule, updates);
      this.render();
      this.onChange(this.getQuery());
    }
  }

  /**
   * Get available fields from schema
   * @returns {Array} Array of field names
   */
  getAvailableFields() {
    if (!this.schema || !this.schema.fields) {
      return [];
    }
    return Object.keys(this.schema.fields).sort();
  }

  /**
   * Get operators for a field type
   * @param {string} fieldType - Field type
   * @returns {Array} Array of operator objects
   */
  getOperators(fieldType) {
    const type = (fieldType || '').toLowerCase();

    const commonOps = [
      { value: 'equals', label: 'Equals' },
      { value: 'not_equals', label: 'Not Equals' },
      { value: 'exists', label: 'Exists' },
      { value: 'not_exists', label: 'Not Exists' }
    ];

    if (type === 'str' || type === 'string' || type === 'text') {
      return [
        ...commonOps,
        { value: 'contains', label: 'Contains' },
        { value: 'starts_with', label: 'Starts With' },
        { value: 'ends_with', label: 'Ends With' },
        { value: 'regex', label: 'Regex' }
      ];
    }

    if (type === 'int' || type === 'integer' || type === 'float' || type === 'double' || type === 'decimal' || type === 'number') {
      return [
        ...commonOps,
        { value: 'greater_than', label: 'Greater Than' },
        { value: 'greater_than_equal', label: 'Greater Than or Equal' },
        { value: 'less_than', label: 'Less Than' },
        { value: 'less_than_equal', label: 'Less Than or Equal' },
        { value: 'between', label: 'Between' }
      ];
    }

    if (type === 'date' || type === 'datetime' || type === 'timestamp') {
      return [
        ...commonOps,
        { value: 'greater_than', label: 'After' },
        { value: 'less_than', label: 'Before' },
        { value: 'between', label: 'Between' }
      ];
    }

    return commonOps;
  }

  /**
   * Convert rules to MongoDB query
   * @returns {Object} MongoDB query object
   */
  getQuery() {
    if (this.rules.length === 0) {
      return {};
    }

    const conditions = this.rules
      .filter(rule => rule.field && rule.operator)
      .map(rule => this.ruleToMongoQuery(rule))
      .filter(q => q !== null);

    if (conditions.length === 0) {
      return {};
    }

    if (conditions.length === 1) {
      return conditions[0];
    }

    return {
      [this.logicalOperator === 'and' ? '$and' : '$or']: conditions
    };
  }

  /**
   * Convert a single rule to MongoDB query
   * @param {Object} rule - Rule object
   * @returns {Object|null} MongoDB query fragment
   */
  ruleToMongoQuery(rule) {
    const { field, operator, value } = rule;
    if (!field || !operator) return null;

    const fieldInfo = this.schema?.fields?.[field];
    const fieldType = fieldInfo?.type?.toLowerCase() || '';

    switch (operator) {
      case 'equals':
        return { [field]: this.parseValue(value, fieldType) };

      case 'not_equals':
        return { [field]: { $ne: this.parseValue(value, fieldType) } };

      case 'contains':
        return { [field]: { $regex: value, $options: 'i' } };

      case 'starts_with':
        return { [field]: { $regex: `^${value}`, $options: 'i' } };

      case 'ends_with':
        return { [field]: { $regex: `${value}$`, $options: 'i' } };

      case 'regex':
        return { [field]: { $regex: value, $options: 'i' } };

      case 'greater_than':
        return { [field]: { $gt: this.parseValue(value, fieldType) } };

      case 'greater_than_equal':
        return { [field]: { $gte: this.parseValue(value, fieldType) } };

      case 'less_than':
        return { [field]: { $lt: this.parseValue(value, fieldType) } };

      case 'less_than_equal':
        return { [field]: { $lte: this.parseValue(value, fieldType) } };

      case 'between':
        const [min, max] = value.split(',').map(v => this.parseValue(v.trim(), fieldType));
        return { [field]: { $gte: min, $lte: max } };

      case 'exists':
        return { [field]: { $exists: true } };

      case 'not_exists':
        return { [field]: { $exists: false } };

      default:
        return null;
    }
  }

  /**
   * Parse value based on field type
   * @param {string} value - Value string
   * @param {string} fieldType - Field type
   * @returns {*} Parsed value
   */
  parseValue(value, fieldType) {
    if (!value) return value;

    const type = fieldType.toLowerCase();

    if (type === 'int' || type === 'integer') {
      return parseInt(value, 10);
    }

    if (type === 'float' || type === 'double' || type === 'decimal' || type === 'number') {
      return parseFloat(value);
    }

    if (type === 'bool' || type === 'boolean') {
      return value === 'true' || value === '1';
    }

    if (type === 'date' || type === 'datetime' || type === 'timestamp') {
      return new Date(value).toISOString();
    }

    return value;
  }

  /**
   * Render the query builder UI
   */
  render() {
    const fields = this.getAvailableFields();

    this.container.innerHTML = `
      <div class="query-builder bg-white rounded-lg shadow p-4">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-800">Query Builder</h3>
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-700">
              <input type="radio" name="logical-op" value="and" ${this.logicalOperator === 'and' ? 'checked' : ''}
                onchange="this.closest('.query-builder').queryBuilder.setLogicalOperator('and')">
              AND
            </label>
            <label class="text-sm text-gray-700">
              <input type="radio" name="logical-op" value="or" ${this.logicalOperator === 'or' ? 'checked' : ''}
                onchange="this.closest('.query-builder').queryBuilder.setLogicalOperator('or')">
              OR
            </label>
          </div>
        </div>

        <div id="query-rules" class="space-y-3 mb-4">
          ${this.rules.map(rule => this.renderRule(rule, fields)).join('')}
        </div>

        <button onclick="this.closest('.query-builder').queryBuilder.addRule()"
          class="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
          + Add Rule
        </button>

        <div class="mt-4 p-3 bg-gray-50 rounded">
          <div class="text-xs text-gray-600 mb-1">MongoDB Query:</div>
          <pre class="text-xs font-mono bg-white p-2 rounded border overflow-auto max-h-32">${JSON.stringify(this.getQuery(), null, 2)}</pre>
        </div>
      </div>
    `;

    // Attach queryBuilder instance to container for event handlers
    this.container.querySelector('.query-builder').queryBuilder = this;
  }

  /**
   * Render a single rule
   * @param {Object} rule - Rule object
   * @param {Array} fields - Available fields
   * @returns {string} HTML string
   */
  renderRule(rule, fields) {
    const fieldInfo = this.schema?.fields?.[rule.field];
    const fieldType = fieldInfo?.type?.toLowerCase() || '';
    const operators = this.getOperators(fieldType);

    const fieldOptions = fields.map(f =>
      `<option value="${f}" ${rule.field === f ? 'selected' : ''}>${f}</option>`
    ).join('');

    const operatorOptions = operators.map(op =>
      `<option value="${op.value}" ${rule.operator === op.value ? 'selected' : ''}>${op.label}</option>`
    ).join('');

    const valueInput = this.renderValueInput(rule, fieldType);

    return `
      <div class="query-rule flex gap-2 items-center p-3 bg-gray-50 rounded border" data-rule-id="${rule.id}">
        <select class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
          onchange="this.closest('.query-rule').queryBuilder.updateRuleField('${rule.id}', this.value)">
          <option value="">Select Field</option>
          ${fieldOptions}
        </select>

        <select class="px-2 py-1.5 border border-gray-300 rounded text-sm"
          onchange="this.closest('.query-rule').queryBuilder.updateRuleOperator('${rule.id}', this.value)">
          ${operatorOptions}
        </select>

        ${valueInput}

        <button onclick="this.closest('.query-rule').queryBuilder.removeRule('${rule.id}')"
          class="px-2 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700">
          ×
        </button>
      </div>
    `;
  }

  /**
   * Render value input based on operator and field type
   * @param {Object} rule - Rule object
   * @param {string} fieldType - Field type
   * @returns {string} HTML string
   */
  renderValueInput(rule, fieldType) {
    const needsValue = !['exists', 'not_exists'].includes(rule.operator);
    if (!needsValue) {
      return '<div class="flex-1"></div>';
    }

    const isBetween = rule.operator === 'between';
    const isBoolean = fieldType === 'bool' || fieldType === 'boolean';
    const isNumber = ['int', 'integer', 'float', 'double', 'decimal', 'number'].includes(fieldType);
    const isDate = ['date', 'datetime', 'timestamp'].includes(fieldType);

    if (isBoolean) {
      return `
        <select class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
          onchange="this.closest('.query-rule').queryBuilder.updateRuleValue('${rule.id}', this.value)">
          <option value="true" ${rule.value === 'true' ? 'selected' : ''}>True</option>
          <option value="false" ${rule.value === 'false' ? 'selected' : ''}>False</option>
        </select>
      `;
    }

    if (isDate) {
      const inputType = fieldType === 'date' ? 'date' : 'datetime-local';
      if (isBetween) {
        return `
          <input type="${inputType}" class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
            placeholder="From" onchange="this.closest('.query-rule').queryBuilder.updateRuleValue('${rule.id}', this.value + ',' + (this.nextElementSibling?.value || ''))">
          <input type="${inputType}" class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
            placeholder="To" onchange="this.closest('.query-rule').queryBuilder.updateRuleValue('${rule.id}', (this.previousElementSibling?.value || '') + ',' + this.value)">
        `;
      }
      return `
        <input type="${inputType}" value="${rule.value || ''}" class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
          onchange="this.closest('.query-rule').queryBuilder.updateRuleValue('${rule.id}', this.value)">
      `;
    }

    if (isNumber && isBetween) {
      return `
        <input type="number" class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
          placeholder="Min" step="${fieldType.includes('int') ? '1' : '0.01'}"
          onchange="this.closest('.query-rule').queryBuilder.updateRuleValue('${rule.id}', this.value + ',' + (this.nextElementSibling?.value || ''))">
        <input type="number" class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
          placeholder="Max" step="${fieldType.includes('int') ? '1' : '0.01'}"
          onchange="this.closest('.query-rule').queryBuilder.updateRuleValue('${rule.id}', (this.previousElementSibling?.value || '') + ',' + this.value)">
      `;
    }

    const inputType = isNumber ? 'number' : 'text';
    const step = isNumber && fieldType.includes('int') ? '1' : (isNumber ? '0.01' : '');

    return `
      <input type="${inputType}" value="${rule.value || ''}" ${step ? `step="${step}"` : ''}
        class="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
        placeholder="Value"
        onchange="this.closest('.query-rule').queryBuilder.updateRuleValue('${rule.id}', this.value)">
    `;
  }

  /**
   * Set logical operator
   * @param {string} op - Operator ('and' or 'or')
   */
  setLogicalOperator(op) {
    this.logicalOperator = op;
    this.onChange(this.getQuery());
    this.render();
  }

  /**
   * Update rule field
   * @param {string} ruleId - Rule ID
   * @param {string} field - Field name
   */
  updateRuleField(ruleId, field) {
    const rule = this.rules.find(r => r.id === ruleId);
    if (rule) {
      rule.field = field;
      rule.operator = 'equals'; // Reset operator
      this.render();
      this.onChange(this.getQuery());
    }
  }

  /**
   * Update rule operator
   * @param {string} ruleId - Rule ID
   * @param {string} operator - Operator
   */
  updateRuleOperator(ruleId, operator) {
    this.updateRule(ruleId, { operator });
  }

  /**
   * Update rule value
   * @param {string} ruleId - Rule ID
   * @param {string} value - Value
   */
  updateRuleValue(ruleId, value) {
    this.updateRule(ruleId, { value });
  }
}

