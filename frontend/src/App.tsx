import React, { useState, useEffect } from 'react';
import { useAuthViewModel } from './viewmodels/useAuthViewModel';
import { useJobViewModel } from './viewmodels/useJobViewModel';
import { Navbar } from './views/components/layout/Navbar';
import { LoginPage } from './views/pages/LoginPage';
import { HomePage } from './views/pages/HomePage';
import { MegawanMetronetPage } from './views/pages/MegawanMetronetPage';
import { JobProgressModal } from './views/components/jobs/JobProgressModal';

const getViewFromPathname = (): 'home' | 'megawan' => {
  const path = window.location.pathname;
  if (path.startsWith('/megawan')) {
    return 'megawan';
  }
  return 'home';
};

export const App: React.FC = () => {
  const {
    isAuthenticated,
    currentUser,
    loading: authLoading,
    error: authError,
    login,
    logout,
    isAdmin,
    isOperator,
  } = useAuthViewModel();

  const {
    activeJob,
    isModalOpen: isJobModalOpen,
    jobTitle,
    startTracking,
    closeModal: closeJobModal,
  } = useJobViewModel();

  // Navigation state: 'home' | 'megawan'
  const [currentView, setCurrentView] = useState<'home' | 'megawan'>(getViewFromPathname);

  // Sync state when browser back/forward buttons are pressed
  useEffect(() => {
    const handlePopState = () => {
      setCurrentView(getViewFromPathname());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Sync URL in address bar with auth & view state
  useEffect(() => {
    if (!isAuthenticated) {
      if (window.location.pathname !== '/login') {
        window.history.replaceState(null, '', '/login');
      }
    } else {
      const targetPath = currentView === 'megawan' ? '/megawan' : '/';
      if (window.location.pathname !== targetPath) {
        if (window.location.pathname === '/login') {
          window.history.replaceState(null, '', targetPath);
        } else {
          window.history.pushState(null, '', targetPath);
        }
      }
    }
  }, [isAuthenticated, currentView]);

  const navigateTo = (view: 'home' | 'megawan') => {
    setCurrentView(view);
    const targetPath = view === 'megawan' ? '/megawan' : '/';
    if (window.location.pathname !== targetPath) {
      window.history.pushState(null, '', targetPath);
    }
  };

  const handleLogout = () => {
    logout();
    window.history.replaceState(null, '', '/login');
  };

  if (!isAuthenticated) {
    return (
      <LoginPage
        onLogin={login}
        loading={authLoading}
        error={authError}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navbar */}
      <Navbar
        currentUser={currentUser}
        onLogout={handleLogout}
        onNavigateHome={() => navigateTo('home')}
        currentView={currentView}
        onSelectView={(v) => navigateTo(v)}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {currentView === 'home' && (
          <HomePage
            onSelectReport={(route) => {
              if (route === 'megawan') navigateTo('megawan');
            }}
          />
        )}

        {currentView === 'megawan' && (
          <MegawanMetronetPage
            onBack={() => navigateTo('home')}
            onJobStarted={startTracking}
            isOperator={isOperator}
            isAdmin={isAdmin}
          />
        )}
      </main>

      {/* Real-time Job Progress Modal */}
      <JobProgressModal
        isOpen={isJobModalOpen}
        onClose={closeJobModal}
        title={jobTitle}
        job={activeJob}
      />
    </div>
  );
};

export default App;
