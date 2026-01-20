import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../App';

const SubscriptionContext = createContext();

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
};

export const SubscriptionProvider = ({ children }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [featureToggles, setFeatureToggles] = useState({
    session_notes: true,
    assessments: true,
    ai_clinical: true,
    protocols: true,
    messaging: true,
    payments: true,
    assistants: true,
    reports: true
  });
  const [isReadOnly, setIsReadOnly] = useState(false);
  const [daysRemaining, setDaysRemaining] = useState(null);
  const [expiryWarning, setExpiryWarning] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchSubscriptionStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/auth/subscription-status`);
      setSubscriptionStatus(res.data.subscription_status);
      setFeatureToggles(res.data.feature_toggles || {
        session_notes: true,
        assessments: true,
        ai_clinical: true,
        protocols: true,
        messaging: true,
        payments: true,
        assistants: true,
        reports: true
      });
      setIsReadOnly(res.data.is_read_only);
      setDaysRemaining(res.data.days_remaining);
      setExpiryWarning(res.data.expiry_warning);
    } catch (error) {
      console.error('Failed to fetch subscription status:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Only fetch if there's a token
    const token = localStorage.getItem('token');
    if (token) {
      fetchSubscriptionStatus();
    } else {
      setLoading(false);
    }
  }, [fetchSubscriptionStatus]);

  const isFeatureEnabled = useCallback((featureName) => {
    // If toggles not loaded, assume enabled
    if (!featureToggles) return true;
    return featureToggles[featureName] !== false;
  }, [featureToggles]);

  const refreshStatus = useCallback(() => {
    fetchSubscriptionStatus();
  }, [fetchSubscriptionStatus]);

  const value = {
    subscriptionStatus,
    featureToggles,
    isReadOnly,
    daysRemaining,
    expiryWarning,
    loading,
    isFeatureEnabled,
    refreshStatus
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
};

// Higher-order component to protect feature access
export const withFeatureAccess = (WrappedComponent, featureName) => {
  return function FeatureProtectedComponent(props) {
    const { isFeatureEnabled, loading } = useSubscription();
    
    if (loading) {
      return null;
    }

    if (!isFeatureEnabled(featureName)) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-foreground mb-2">Feature Not Available</h3>
          <p className="text-muted-foreground max-w-md">
            This feature is not included in your current subscription plan.
            Please contact support or upgrade your plan to access this feature.
          </p>
        </div>
      );
    }

    return <WrappedComponent {...props} />;
  };
};

export default SubscriptionContext;
