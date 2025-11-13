/**
 * Custom validators utility
 * @module react/utils/validators
 */

/**
 * Registry for custom validators
 * Format: { fieldName: { validator: function, message: string } }
 */
const customValidators = new Map();

/**
 * Register a custom field validator
 * @param {string} fieldName - Field name to validate
 * @param {Function} validator - Validator function (value, fieldInfo, formData) => string | null
 * @param {string} errorMessage - Custom error message (optional)
 */
export function registerFieldValidator(fieldName, validator, errorMessage = null) {
  customValidators.set(fieldName, {
    validator,
    message: errorMessage
  });
}

/**
 * Register a custom form validator
 * @param {Function} validator - Validator function (formData, schema) => { isValid: boolean, errors: string[] }
 */
let formValidator = null;

export function registerFormValidator(validator) {
  formValidator = validator;
}

/**
 * Validate a field using custom validators
 * @param {string} fieldName - Field name
 * @param {*} value - Field value
 * @param {Object} fieldInfo - Field schema info
 * @param {Object} formData - Complete form data
 * @param {Function} t - Translation function (optional)
 * @returns {string | null} Error message or null if valid
 */
export function validateField(fieldName, value, fieldInfo, formData, t = null) {
  const validator = customValidators.get(fieldName);
  if (validator) {
    try {
      const error = validator.validator(value, fieldInfo, formData);
      if (error) {
        return validator.message || error;
      }
    } catch (e) {
      const errorMsg = t ? t('validation.validationError', { error: e.message }) : `Validation error: ${e.message}`;
      return errorMsg;
    }
  }
  return null;
}

/**
 * Validate entire form using custom form validator
 * @param {Object} formData - Form data
 * @param {Object} schema - Schema object
 * @param {Function} t - Translation function (optional)
 * @returns {{ isValid: boolean, errors: string[] }} Validation result
 */
export function validateForm(formData, schema, t = null) {
  if (formValidator) {
    try {
      return formValidator(formData, schema);
    } catch (e) {
      const errorMsg = t ? t('validation.formValidationError', { error: e.message }) : `Form validation error: ${e.message}`;
      return {
        isValid: false,
        errors: [errorMsg]
      };
    }
  }
  return { isValid: true, errors: [] };
}

/**
 * Clear all custom validators
 */
export function clearValidators() {
  customValidators.clear();
  formValidator = null;
}

/**
 * Get all registered field validators
 * @returns {Map} Map of validators
 */
export function getValidators() {
  return customValidators;
}

