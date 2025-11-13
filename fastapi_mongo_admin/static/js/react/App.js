/**
 * Main App component
 * @module react/App
 */

import { getCollections } from './services/api.js';
import { useDarkMode } from './hooks/useDarkMode.js';
import { useTranslation } from './hooks/useTranslation.js';
import { titleize } from './utils.js';
import { Sidebar } from './components/Sidebar.js';
import { Message } from './components/Message.js';
import { BrowseView } from './components/BrowseView.js';
import { SchemaView } from './components/SchemaView.js';
import { AnalyticsView } from './components/AnalyticsView.js';
import { CreateModal } from './components/CreateModal.js';
import { CustomView } from './components/CustomView.js';
import { LanguageSelector } from './components/LanguageSelector.js';

const { useState, useEffect, useCallback } = React;

/**
 * Main App component
 */
export function App() {
  const [collections, setCollections] = useState([]);
  const [currentCollection, setCurrentCollection] = useState('');
  const [currentView, setCurrentView] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [darkMode, toggleDarkMode] = useDarkMode();
  const t = useTranslation();

  // Load collections on mount
  useEffect(() => {
    const loadCollections = async () => {
      try {
        const data = await getCollections();
        setCollections(data);
      } catch (error) {
        setErrorMessage(t('app.failedToLoadCollections') + ': ' + error.message);
      }
    };
    loadCollections();
  }, []);

  const handleNavigate = useCallback((collection, view) => {
    setCurrentCollection(collection);
    setCurrentView(view);
    if (view === 'create') {
      setShowCreateModal(true);
    }
  }, []);

  const handleCreateSuccess = useCallback(() => {
    setSuccessMessage(t('create.documentCreated'));
    setShowCreateModal(false);
    // Optionally refresh the browse view if it's open
    if (currentView === 'browse') {
      // Trigger refresh by updating a key or state
    }
  }, [currentView, t]);

  const getPageTitle = () => {
    if (!currentCollection) return t('app.selectCollection');
    const viewTitles = {
      browse: t('app.browseDocuments'),
      create: t('app.createDocument'),
      schema: t('app.schema'),
      analytics: t('app.analytics'),
    };
    return `${titleize(currentCollection)} - ${viewTitles[currentView] || currentView}`;
  };

  const renderView = () => {
    if (!currentCollection) {
      return (
        <div className="h-full w-full flex items-center justify-center text-center text-gray-500">
          <div>
            <div className="text-5xl mb-5">📋</div>
            <h3 className="text-xl font-semibold mb-2">{t('app.selectCollection')}</h3>
            <p>{t('app.chooseCollection')}</p>
          </div>
        </div>
      );
    }

    // Check for custom views first
    if (currentView && currentView.startsWith('custom:')) {
      const viewType = currentView.replace('custom:', '');
      return (
        <CustomView
          collection={currentCollection}
          viewType={viewType}
          viewConfig={{}}
          onNavigate={handleNavigate}
        />
      );
    }

    switch (currentView) {
      case 'browse':
        return (
          <BrowseView
            collection={currentCollection}
            onRefresh={() => { }}
            onShowCreateModal={() => setShowCreateModal(true)}
            onSuccess={(message) => setSuccessMessage(message)}
          />
        );
      case 'schema':
        return <SchemaView collection={currentCollection} />;
      case 'analytics':
        return <AnalyticsView collection={currentCollection} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        collections={collections}
        currentCollection={currentCollection}
        currentView={currentView}
        onNavigate={handleNavigate}
        onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
        sidebarCollapsed={sidebarCollapsed}
        darkMode={darkMode}
        onToggleDarkMode={toggleDarkMode}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="bg-white px-8 py-5 border-b border-gray-200 shadow-sm flex items-center gap-4">
          {sidebarCollapsed && (
            <button
              onClick={() => setSidebarCollapsed(false)}
              className="hidden md:flex bg-gray-100 border border-gray-300 text-gray-700 cursor-pointer px-3 py-2 rounded text-base transition-all items-center justify-center min-w-10 hover:bg-gray-200">
              ☰
            </button>
          )}
          <div className="flex-1">
            <h2 className="text-gray-800 text-2xl mb-1">{getPageTitle()}</h2>
            {currentCollection && (
              <p className="text-gray-500 text-sm">
                {t('common.collection')}: {currentCollection}
              </p>
            )}
          </div>
          <LanguageSelector />
          <button
            onClick={toggleDarkMode}
            className="bg-gray-100 border border-gray-300 text-gray-700 cursor-pointer px-3 py-2 rounded text-base transition-all items-center justify-center min-w-10 hover:bg-gray-200"
            title={t('app.toggleDarkMode')}>
            {darkMode ? '☀️' : '🌙'}
          </button>
        </div>
        <div className="flex-1 overflow-hidden flex flex-col bg-gray-50">
          <Message
            type="error"
            message={errorMessage}
            onClose={() => setErrorMessage('')}
          />
          <Message
            type="success"
            message={successMessage}
            onClose={() => setSuccessMessage('')}
          />
          <div className="flex-1 overflow-y-auto p-8">
            {renderView()}
          </div>
        </div>
        <footer className="bg-white border-t border-gray-200 px-8 py-4 flex items-center justify-center">
          <p className="text-sm text-gray-600">
            {t('app.madeWith')} ❤️ {t('app.by')}{' '}
            <a
              href="https://github.com/tushortz/fastapi-mongo-admin"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline">
              tushortz
            </a>
          </p>
        </footer>
      </div>
      <CreateModal
        collection={currentCollection}
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  );
}
