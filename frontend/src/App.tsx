import React, { useState } from 'react';
import { useAuthViewModel } from './viewmodels/useAuthViewModel';
import { useJobViewModel } from './viewmodels/useJobViewModel';
import { Navbar } from './views/components/layout/Navbar';
import { LoginPage } from './views/pages/LoginPage';
import { HomePage } from './views/pages/HomePage';
import { MegawanMetronetPage } from './views/pages/MegawanMetronetPage';
import { JobProgressModal } from './views/components/jobs/JobProgressModal';

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
  const [currentView, setCurrentView] = useState<'home' | 'megawan'>('home');

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
        onLogout={logout}
        onNavigateHome={() => setCurrentView('home')}
        currentView={currentView}
        onSelectView={(v) => setCurrentView(v)}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {currentView === 'home' && (
          <HomePage
            onSelectReport={(route) => {
              if (route === 'megawan') setCurrentView('megawan');
            }}
          />
        )}

        {currentView === 'megawan' && (
          <MegawanMetronetPage
            onBack={() => setCurrentView('home')}
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

