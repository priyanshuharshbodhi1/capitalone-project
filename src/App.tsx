import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './components/Login/Login';
import Dashboard from './components/Dashboard/Dashboard';
import Analytics from './components/Analytics/Analytics';
import Settings from './components/Settings/Settings';
import Chatbot from './components/Chatbot/Chatbot';
import Layout from './components/Layout/Layout';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  console.log('🔒 PrivateRoute: isLoading:', isLoading, 'user:', user?.name || 'none');

  // Authentication is required to access protected routes

  if (isLoading) {
    console.log('⏳ PrivateRoute: Showing loading screen');
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <>{children}</> : <Navigate to="/login" />;
};

const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  
  console.log('🌐 PublicRoute: isLoading:', isLoading, 'user:', user?.name || 'none');
  
  if (isLoading) {
    console.log('⏳ PublicRoute: Showing loading screen');
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
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
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;