/**
 * Confirmation modal component
 * @module react/components/ConfirmModal
 */

import { useTranslation } from '../hooks/useTranslation.js';

/**
 * Confirm modal component
 * @param {Object} props - Component props
 */
export function ConfirmModal({ isOpen, title, message, confirmText, cancelText, onConfirm, onCancel, variant = 'danger' }) {
  const t = useTranslation();
  const defaultTitle = title || t('confirm.title');
  const defaultMessage = message || t('confirm.message');
  const defaultConfirmText = confirmText || t('common.confirm');
  const defaultCancelText = cancelText || t('common.cancel');
  if (!isOpen) return null;

  const bgColor = variant === 'danger' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700';

  return (
    <div
      className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div
        className="bg-white p-6 rounded-lg max-w-md w-11/12"
        onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-2">{defaultTitle}</h3>
        <p className="text-gray-700 mb-6">{defaultMessage}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-50">
            {defaultCancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded text-sm font-medium text-white ${bgColor}`}>
            {defaultConfirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
