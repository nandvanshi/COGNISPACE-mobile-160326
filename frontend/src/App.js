import React, { createContext, useState, useContext, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Toaster } from 'sonner';
import LoginPage from './pages/LoginPage';
import AdminLoginPage from './pages/AdminLoginPage';
import ForgotPassword from './pages/ForgotPassword';
import TherapistApplicationPage from './pages/TherapistApplicationPage';
import TherapistDashboard from './pages/TherapistDashboard';
import ClientDashboard from './pages/ClientDashboard';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import AssistantDashboard from './pages/AssistantDashboard';
import ClientRegisterPage from './pages/ClientRegisterPage';
import PublicBookingPage from './pages/PublicBookingPage';
import AboutPage from './pages/AboutPage';
import PrivacyPolicy from './pages/PrivacyPolicy';
import TermsConditions from './pages/TermsConditions';
import ClinicalDisclaimer from './pages/ClinicalDisclaimer';
import RefundPolicy from './pages/RefundPolicy';
import ContactSupport from './pages/ContactSupport';
import InstallPWA from './components/InstallPWA';
import { applyTheme, getStoredTheme } from './config/themes';
import { SubscriptionProvider } from './contexts/SubscriptionContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  });
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Apply stored theme on initial load
  useEffect(() => {
    applyTheme(getStoredTheme());
  }, []);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // If we have stored user, don't show loading
      if (user) {
        setLoading(false);
        // Still verify token in background
        verifyToken();
      } else {
        fetchUser();
      }
    } else {
      setLoading(false);
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
      loadUserTheme();
    } catch (error) {
      console.error('Token expired or invalid:', error);
      logout();
    }
  };

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      localStorage.setItem('user', JSON.stringify(response.data));
      loadUserTheme();
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const loadUserTheme = async () => {
    try {
      const response = await axios.get(`${API}/user/preferences`);
      if (response.data?.theme) {
        applyTheme(response.data.theme);
      }
    } catch (error) {
      // Use stored theme if API fails
      applyTheme(getStoredTheme());
    }
  };

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(token);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    // Load user's theme preference after login
    loadUserTheme();
    
    // Clear service worker cache on login to ensure fresh content
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
      // Also trigger service worker update check
      navigator.serviceWorker.ready.then((registration) => {
        registration.update();
      });
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('user-theme');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    // Reset to default theme on logout
    applyTheme('calm-professional');
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
      <SubscriptionProvider>
        <div className="App">
          <div className="noise-overlay" />
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/admin-login" element={<AdminLoginPage />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ForgotPassword />} />
              <Route path="/therapist-application" element={<TherapistApplicationPage />} />
              <Route path="/register/client/:therapistCode" element={<ClientRegisterPage />} />
              {/* Public Booking Calendar */}
              <Route path="/book/:therapistId" element={<PublicBookingPage />} />
              {/* Legal & Compliance Pages */}
              <Route path="/privacy-policy" element={<PrivacyPolicy />} />
              <Route path="/terms-conditions" element={<TermsConditions />} />
              <Route path="/clinical-disclaimer" element={<ClinicalDisclaimer />} />
              <Route path="/refund-policy" element={<RefundPolicy />} />
              <Route path="/contact" element={<ContactSupport />} />
              <Route path="/about" element={<AboutPage />} />
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
          <InstallPWA />
        </div>
      </SubscriptionProvider>
    </AuthProvider>
  );
}

export default App;
export { API };
