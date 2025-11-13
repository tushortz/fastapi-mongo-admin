/**
 * Custom view component wrapper
 * @module react/components/CustomView
 */

import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useEffect } = React;

/**
 * Custom view component - allows registering custom view components
 * @param {Object} props - Component props
 */
export function CustomView({ collection, viewType, viewConfig, onNavigate }) {
  const [customComponent, setCustomComponent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const t = useTranslation();

  useEffect(() => {
    // Check if custom view is registered
    if (window.CUSTOM_VIEWS && window.CUSTOM_VIEWS[viewType]) {
      try {
        const ViewComponent = window.CUSTOM_VIEWS[viewType];
        setCustomComponent(() => ViewComponent);
        setLoading(false);
      } catch (err) {
        setError(t('customView.failedToLoad', { error: err.message }) || `Failed to load custom view: ${err.message}`);
        setLoading(false);
      }
    } else {
      setError(t('customView.notFound', { viewType }) || `Custom view "${viewType}" not found. Register it using window.CUSTOM_VIEWS['${viewType}'] = YourComponent`);
      setLoading(false);
    }
  }, [viewType, t]);

  if (loading) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <div>{t('customView.loading') || 'Loading custom view...'}</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <div className="p-4 rounded bg-red-100 text-red-800">{error}</div>
      </div>
    );
  }

  if (!customComponent) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <div className="p-4 rounded bg-yellow-100 text-yellow-800">
          {t('customView.notAvailable') || 'Custom view component not available'}
        </div>
      </div>
    );
  }

  const Component = customComponent;
  return <Component collection={collection} config={viewConfig} onNavigate={onNavigate} />;
}

/**
 * Register a custom view component
 * @param {string} viewType - View type identifier
 * @param {React.Component} component - React component to render
 */
export function registerCustomView(viewType, component) {
  if (!window.CUSTOM_VIEWS) {
    window.CUSTOM_VIEWS = {};
  }
  window.CUSTOM_VIEWS[viewType] = component;
}

