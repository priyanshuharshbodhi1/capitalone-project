import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import Login from './components/Login/Login';
import Dashboard from './components/Dashboard/Dashboard';
import Analytics from './components/Analytics/Analytics';
import Settings from './components/Settings/Settings';
import Chatbot from './components/Chatbot/Chatbot';
import Layout from './components/Layout/Layout';
import MockSensor from './components/MockSensor/MockSensor';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const { t } = useTranslation();

  console.log('🔒 PrivateRoute: isLoading:', isLoading, 'user:', user?.name || 'none');

  // Authentication is required to access protected routes

  if (isLoading) {
    console.log('⏳ PrivateRoute: Showing loading screen');
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
          <p className="mt-4 text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    );
  }

  return user ? <>{children}</> : <Navigate to="/login" />;
};

const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const { t } = useTranslation();
  
  console.log('🌐 PublicRoute: isLoading:', isLoading, 'user:', user?.name || 'none');
  
  if (isLoading) {
    console.log('⏳ PublicRoute: Showing loading screen');
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
          <p className="mt-4 text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    );
  }
  
  return user ? <Navigate to="/" /> : <>{children}</>;
};

const App: React.FC = () => {
  console.log('🚀 App: Component rendered');
  
  return (
    <AuthProvider>
      <LanguageProvider>
        <Toaster 
          position="top-center"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#333',
              color: '#fff',
              padding: '16px',
              borderRadius: '8px',
            },
            success: {
              style: {
                background: '#166534',
              },
            },
            error: {
              style: {
                background: '#991b1b',
              },
            },
          }}
        />
        <Router>
          <Routes>
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Layout />
                </PrivateRoute>
              }
            >
              <Route index element={<Chatbot />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="settings" element={<Settings />} />
              <Route path="mock-sensor" element={<MockSensor />} />
            </Route>
          </Routes>
        </Router>
      </LanguageProvider>
    </AuthProvider>
  );
};

export default App;