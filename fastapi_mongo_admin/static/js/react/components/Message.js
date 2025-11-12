/**
 * Message component for displaying error/success messages
 * @module react/components/Message
 */

const { useState, useEffect } = React;

/**
 * Message component
 * @param {Object} props - Component props
 * @param {string} props.type - Message type: 'error' or 'success'
 * @param {string} props.message - Message text
 * @param {Function} props.onClose - Close handler
 * @param {number} props.autoClose - Auto close delay in ms (0 to disable)
 */
export function Message({ type, message, onClose, autoClose = 5000 }) {
  const [visible, setVisible] = useState(!!message);

  useEffect(() => {
    setVisible(!!message);
    if (message && autoClose > 0) {
      const timer = setTimeout(() => {
        setVisible(false);
        if (onClose) onClose();
      }, autoClose);
      return () => clearTimeout(timer);
    }
  }, [message, autoClose, onClose]);

  if (!visible || !message) return null;

  const bgColor = type === 'error'
    ? 'bg-red-100 text-red-800'
    : 'bg-green-100 text-green-800';

  return (
    <div className={`p-4 rounded mb-5 ${bgColor} flex justify-between items-center`}>
      <span>{message}</span>
      <button
        onClick={() => {
          setVisible(false);
          if (onClose) onClose();
        }}
        className="ml-4 text-lg hover:opacity-70"
      >
        ×
      </button>
    </div>
  );
}
