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

  // SVG Icons as components
  const MenuIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );

  const ChevronRightIcon = ({ className = '' }) => (
    <svg className={`w-4 h-4 transition-transform duration-200 ${className}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );

  const DatabaseIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  );

  const BrowseIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
    </svg>
  );

  const SchemaIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );

  const AnalyticsIcon = () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );

  const ChevronLeftIcon = () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  );

  if (sidebarCollapsed) {
    return (
      <button
        onClick={onToggleSidebar}
        className="sidebar-toggle-btn bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 cursor-pointer px-3 py-2.5 rounded-lg text-base transition-all items-center justify-center min-w-10 hover:bg-gray-50 dark:hover:bg-gray-700 hover:shadow-md fixed top-4 left-4 z-50 md:hidden shadow-sm"
        title={t('app.showSidebar')}>
        <MenuIcon />
      </button>
    );
  }

  return (
    <nav
      className="bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white flex flex-col overflow-y-auto shadow-2xl relative border-r border-gray-700/50"
      style={{ width: '280px', minWidth: '280px' }}>
      {/* Header */}
      <div className="p-6 bg-gradient-to-r from-blue-600/10 to-indigo-600/10 border-b border-gray-700/50 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1">
            <div className="p-2 bg-blue-600/20 rounded-lg">
              <DatabaseIcon />
            </div>
            <div className="flex-1">
              <h1 className="text-lg font-bold text-white">{t('sidebar.adminPanel')}</h1>
              <p className="text-xs text-gray-400 mt-0.5">{t('sidebar.mongoCollections')}</p>
            </div>
          </div>
          <button
            onClick={onToggleSidebar}
            className="p-2 hover:bg-gray-700/50 rounded-lg text-gray-300 hover:text-white transition-all duration-200 flex-shrink-0"
            title={t('app.collapseSidebar')}>
            <ChevronLeftIcon />
          </button>
        </div>
      </div>

      {/* Collections List */}
      <div className="flex-1 py-3 px-2">
        {sortedCollections.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <div className="animate-pulse">
              <DatabaseIcon />
            </div>
            <p className="mt-3 text-sm">{t('sidebar.loadingCollections')}</p>
          </div>
        ) : (
            <div className="space-y-1">
              {sortedCollections.map(collection => {
                const isExpanded = expandedCollections.has(collection);
                const isActive = currentCollection === collection;
                return (
                <div key={collection} className="mb-1">
                  {/* Collection Header */}
                  <div
                    className={`px-4 py-3 cursor-pointer flex justify-between items-center transition-all duration-200 rounded-lg group ${isActive
                        ? 'bg-blue-600/20 border border-blue-500/30 shadow-lg shadow-blue-500/10'
                        : 'hover:bg-gray-700/50 border border-transparent hover:border-gray-700/50'
                      }`}
                    onClick={() => toggleCollection(collection)}>
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className={`p-1.5 rounded-md transition-colors ${isActive ? 'bg-blue-600/30 text-blue-300' : 'bg-gray-700/50 text-gray-400 group-hover:bg-gray-600/50 group-hover:text-gray-300'
                        }`}>
                        <DatabaseIcon />
                      </div>
                      <span className={`font-semibold text-sm truncate ${isActive ? 'text-white' : 'text-gray-200 group-hover:text-white'
                        }`}>
                        {titleize(collection)}
                      </span>
                    </div>
                    <ChevronRightIcon className={isExpanded ? 'rotate-90' : ''} />
                  </div>

                  {/* Sub-menu Items */}
                  {isExpanded && (
                    <div className="mt-1 ml-4 pl-4 border-l-2 border-gray-700/50 space-y-0.5">
                      <div
                        className={`px-4 py-2.5 cursor-pointer text-sm transition-all duration-200 rounded-lg flex items-center gap-3 group ${isActive && currentView === 'browse'
                            ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30 shadow-md shadow-blue-500/10'
                            : 'text-gray-400 hover:bg-gray-700/30 hover:text-gray-200 border border-transparent'
                        }`}
                        onClick={() => onNavigate(collection, 'browse')}>
                        <div className={`p-1 rounded ${isActive && currentView === 'browse' ? 'bg-blue-600/30' : 'bg-gray-700/50 group-hover:bg-gray-600/50'
                          }`}>
                          <BrowseIcon />
                        </div>
                        <span className={isActive && currentView === 'browse' ? 'font-semibold' : 'font-medium'}>
                          {t('sidebar.browse')}
                        </span>
                      </div>
                      <div
                        className={`px-4 py-2.5 cursor-pointer text-sm transition-all duration-200 rounded-lg flex items-center gap-3 group ${isActive && currentView === 'schema'
                            ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30 shadow-md shadow-blue-500/10'
                            : 'text-gray-400 hover:bg-gray-700/30 hover:text-gray-200 border border-transparent'
                        }`}
                        onClick={() => onNavigate(collection, 'schema')}>
                        <div className={`p-1 rounded ${isActive && currentView === 'schema' ? 'bg-blue-600/30' : 'bg-gray-700/50 group-hover:bg-gray-600/50'
                          }`}>
                          <SchemaIcon />
                        </div>
                        <span className={isActive && currentView === 'schema' ? 'font-semibold' : 'font-medium'}>
                          {t('sidebar.schema')}
                        </span>
                      </div>
                      <div
                        className={`px-4 py-2.5 cursor-pointer text-sm transition-all duration-200 rounded-lg flex items-center gap-3 group ${isActive && currentView === 'analytics'
                            ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30 shadow-md shadow-blue-500/10'
                            : 'text-gray-400 hover:bg-gray-700/30 hover:text-gray-200 border border-transparent'
                        }`}
                        onClick={() => onNavigate(collection, 'analytics')}>
                        <div className={`p-1 rounded ${isActive && currentView === 'analytics' ? 'bg-blue-600/30' : 'bg-gray-700/50 group-hover:bg-gray-600/50'
                          }`}>
                          <AnalyticsIcon />
                        </div>
                        <span className={isActive && currentView === 'analytics' ? 'font-semibold' : 'font-medium'}>
                          {t('sidebar.analytics')}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            </div>
        )}
      </div>
    </nav>
  );
}
