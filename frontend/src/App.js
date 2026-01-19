import React, { createContext, useState, useContext, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Toaster } from 'sonner';
import LoginPage from './pages/LoginPage';
import AdminLoginPage from './pages/AdminLoginPage';
import TherapistApplicationPage from './pages/TherapistApplicationPage';
import TherapistDashboard from './pages/TherapistDashboard';
import ClientDashboard from './pages/ClientDashboard';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import AssistantDashboard from './pages/AssistantDashboard';
import { applyTheme, getStoredTheme } from './config/themes';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Apply stored theme on initial load
  useEffect(() => {
    applyTheme(getStoredTheme());
  }, []);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    setToken(token);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    if (allowedRoles?.includes('super_admin')) {
      return <Navigate to="/admin-login" replace />;
    }
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard
    if (user.role === 'super_admin') {
      return <Navigate to="/admin" replace />;
    } else if (user.role === 'therapist') {
      return <Navigate to="/therapist" replace />;
    } else if (user.role === 'assistant') {
      return <Navigate to="/assistant" replace />;
    } else if (user.role === 'client') {
      return <Navigate to="/client" replace />;
    }
    return <Navigate to="/" replace />;
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <div className="noise-overlay" />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/admin-login" element={<AdminLoginPage />} />
            <Route path="/therapist-application" element={<TherapistApplicationPage />} />
            <Route
              path="/therapist/*"
              element={
                <ProtectedRoute allowedRoles={['therapist']}>
                  <TherapistDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/client/*"
              element={
                <ProtectedRoute allowedRoles={['client']}>
                  <ClientDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assistant/*"
              element={
                <ProtectedRoute allowedRoles={['assistant']}>
                  <AssistantDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/*"
              element={
                <ProtectedRoute allowedRoles={['super_admin']}>
                  <SuperAdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </AuthProvider>
  );
}

export default App;
export { API };
