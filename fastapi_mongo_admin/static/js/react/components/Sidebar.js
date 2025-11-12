/**
 * Sidebar navigation component
 * @module react/components/Sidebar
 */

import { titleize } from '../utils.js';
import { useTranslation } from '../hooks/useTranslation.js';

const { useState, useMemo } = React;

/**
 * Sidebar component
 * @param {Object} props - Component props
 */
export function Sidebar({
  collections,
  currentCollection,
  currentView,
  onNavigate,
  onToggleSidebar,
  sidebarCollapsed,
  darkMode,
  onToggleDarkMode,
}) {
  const [expandedCollections, setExpandedCollections] = useState(new Set());
  const t = useTranslation();

  const toggleCollection = (collection) => {
    setExpandedCollections(prev => {
      const next = new Set(prev);
      if (next.has(collection)) {
        next.delete(collection);
      } else {
        next.add(collection);
      }
      return next;
    });
  };

  const sortedCollections = useMemo(() => {
    return [...(collections || [])].sort((a, b) =>
      a.toLowerCase().localeCompare(b.toLowerCase())
    );
  }, [collections]);

  if (sidebarCollapsed) {
    return (
      <button
        onClick={onToggleSidebar}
        className="sidebar-toggle-btn bg-gray-100 border border-gray-300 text-gray-700 cursor-pointer px-3 py-2 rounded text-base transition-all items-center justify-center min-w-10 hover:bg-gray-200 hover:text-gray-900 fixed top-4 left-4 z-50 md:hidden"
        title={t('app.showSidebar')}>
        ☰
      </button>
    );
  }

  return (
    <nav
      className="bg-gray-800 text-white flex flex-col overflow-y-auto shadow-lg relative"
      style={{ width: '280px', minWidth: '280px' }}>
      <div className="p-5 bg-gray-900 border-b border-gray-700 flex justify-between items-center">
        <div>
          <h1 className="text-lg text-blue-400 mb-1">🔧 {t('sidebar.adminPanel')}</h1>
          <p className="text-xs text-gray-400">{t('sidebar.mongoCollections')}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleDarkMode}
            className="bg-transparent border-none text-gray-400 cursor-pointer p-1.5 rounded hover:text-white hover:bg-gray-700 transition-colors text-lg"
            title={t('app.toggleDarkMode')}>
            {darkMode ? '☀️' : '🌙'}
          </button>
          <button
            onClick={onToggleSidebar}
            className="bg-transparent border-none text-gray-400 cursor-pointer p-1 rounded hover:text-white hover:bg-gray-700 transition-colors text-lg"
            title={t('app.collapseSidebar')}>
            ◀
          </button>
        </div>
      </div>
      <div className="flex-1 py-2">
        {sortedCollections.length === 0 ? (
          <div className="text-center py-10 text-gray-400">{t('sidebar.loadingCollections')}</div>
        ) : (
          sortedCollections.map(collection => {
            const isExpanded = expandedCollections.has(collection);
            const isActive = currentCollection === collection;
            return (
              <div key={collection} className="border-b border-gray-700">
                <div
                  className="px-5 py-3 cursor-pointer flex justify-between items-center transition-colors hover:bg-gray-700"
                  onClick={() => toggleCollection(collection)}>
                  <span className="font-semibold text-sm">{titleize(collection)}</span>
                  <span className={`text-xs transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                    ▶
                  </span>
                </div>
                {isExpanded && (
                  <div className="bg-gray-900 py-1">
                    <div
                      className={`px-5 py-2 pl-10 cursor-pointer text-sm transition-colors hover:bg-gray-700 flex items-center gap-2 ${isActive && currentView === 'browse' ? 'bg-gray-700 font-semibold' : ''
                        }`}
                      onClick={() => onNavigate(collection, 'browse')}>
                      <span className="w-4 text-center">📋</span>
                      <span>{t('sidebar.browse')}</span>
                    </div>
                    <div
                      className={`px-5 py-2 pl-10 cursor-pointer text-sm transition-colors hover:bg-gray-700 flex items-center gap-2 ${isActive && currentView === 'schema' ? 'bg-gray-700 font-semibold' : ''
                        }`}
                      onClick={() => onNavigate(collection, 'schema')}>
                      <span className="w-4 text-center">📊</span>
                      <span>{t('sidebar.schema')}</span>
                    </div>
                    <div
                      className={`px-5 py-2 pl-10 cursor-pointer text-sm transition-colors hover:bg-gray-700 flex items-center gap-2 ${isActive && currentView === 'analytics' ? 'bg-gray-700 font-semibold' : ''
                        }`}
                      onClick={() => onNavigate(collection, 'analytics')}>
                      <span className="w-4 text-center">📈</span>
                      <span>{t('sidebar.analytics')}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </nav>
  );
}
