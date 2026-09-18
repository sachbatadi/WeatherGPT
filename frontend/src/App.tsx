import React, { useState, useEffect } from 'react';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Header } from './components/Header';
import { CommandCenterView } from './components/CommandCenterView';
import { SimpleVisualHome } from './components/SimpleVisualHome';
import { RiskMapView } from './components/RiskMapView';
import { DisasterEmergencyView } from './components/DisasterEmergencyView';
import { AgricultureView } from './components/AgricultureView';
import { WeatherGPTView } from './components/WeatherGPTView';
import { AgentCopilotDrawer } from './components/AgentCopilotDrawer';
import { LoginPage } from './components/LoginPage';
import { NavigationTab, UserRole } from './types';

function AppContent() {
  const { t } = useLanguage();
  const { user, isLoginModalOpen, setIsLoginModalOpen } = useAuth();
  const [activeTab, setActiveTab] = useState<NavigationTab>('weathergpt');
  const [selectedLocation, setSelectedLocation] = useState<string>('Patiala, Punjab');
  const [isCopilotOpen, setIsCopilotOpen] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleLoginSuccess = (_role: UserRole) => {
    setActiveTab('weathergpt');
  };

  const handleRefresh = () => {
    setToastMessage(t('header.toastRefreshed', 'Live hydro-telemetry and agent feeds refreshed.'));
    setTimeout(() => setToastMessage(null), 2500);
  };

  // Starting Login experience for citizens and officers (like ChatGPT / Gemini)
  if (!user) {
    return (
      <LoginPage
        isOpen={true}
        isInitialScreen={true}
        onLoginSuccess={handleLoginSuccess}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-blue-100 selection:text-blue-900">
      {/* Login / Role Switching Modal */}
      <LoginPage
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {/* Top Application Header */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenCopilot={() => setIsCopilotOpen(true)}
        onRefresh={handleRefresh}
        selectedLocation={selectedLocation}
        onLocationChange={setSelectedLocation}
      />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white text-xs font-medium px-4 py-2.5 rounded-lg shadow-lg border border-slate-700 animate-in fade-in slide-in-from-bottom-2 duration-200">
          {toastMessage}
        </div>
      )}

      {/* Main View Area */}
      <main className={`flex-1 max-w-[1500px] w-full mx-auto px-3 sm:px-6 ${activeTab === 'weathergpt' ? 'pt-2 sm:pt-3' : 'pt-5'}`}>
        {activeTab === 'citizen' && (
          <SimpleVisualHome
            onNavigateTab={setActiveTab}
            selectedLocation={selectedLocation}
          />
        )}

        {activeTab === 'command' && (
          <CommandCenterView
            onNavigateTab={setActiveTab}
            selectedLocation={selectedLocation}
          />
        )}

        {activeTab === 'weathergpt' && <WeatherGPTView />}
        {activeTab === 'risk' && <RiskMapView />}
        {activeTab === 'emergency' && <DisasterEmergencyView />}
        {activeTab === 'agriculture' && <AgricultureView />}
      </main>

      {/* WeatherGPT Slide-out Drawer */}
      <AgentCopilotDrawer
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}
