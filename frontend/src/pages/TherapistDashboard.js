import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { LogOut, Users, Calendar, FileText, MessageSquare, ClipboardList, BookOpen, DollarSign, Home, AlertTriangle, Clock, Repeat } from 'lucide-react';
import TherapistOverview from '../components/TherapistOverview';
import ClientManagement from '../components/ClientManagement';
import AppointmentCalendar from '../components/AppointmentCalendar';
import SessionNotes from '../components/SessionNotes';
import Messaging from '../components/Messaging';
import Assessments from '../components/Assessments';
import Protocols from '../components/Protocols';
import Payments from '../components/Payments';
import AvailabilitySettings from '../components/AvailabilitySettings';
import RecurringAppointments from '../components/RecurringAppointments';

const TherapistDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('overview');
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isReadOnly, setIsReadOnly] = useState(false);

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await axios.get(`${API}/auth/subscription-status`);
      setSubscriptionStatus(response.data);
      setIsReadOnly(response.data.is_read_only);
    } catch (error) {
      console.error('Failed to fetch subscription status:', error);
    }
  };

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'appointments', label: 'Appointments', icon: Calendar },
    { id: 'availability', label: 'Availability', icon: Clock },
    { id: 'recurring', label: 'Recurring', icon: Repeat },
    { id: 'notes', label: 'Session Notes', icon: FileText },
    { id: 'messages', label: 'Messages', icon: MessageSquare },
    { id: 'assessments', label: 'Assessments', icon: ClipboardList },
    { id: 'protocols', label: 'Protocols', icon: BookOpen },
    { id: 'payments', label: 'Payments', icon: DollarSign },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-2xl font-serif text-primary">Haven</h1>
          <p className="text-sm text-muted-foreground mt-1">{user?.full_name}</p>
          {subscriptionStatus && !isReadOnly && (
            <span className="inline-block mt-2 px-2 py-1 bg-success/10 text-success text-xs rounded-full">
              {subscriptionStatus.subscription_status === 'trial' ? 'Free Trial' : 'Active'}
            </span>
          )}
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                data-testid={`nav-${item.id}`}
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  currentView === item.id
                    ? 'bg-primary text-white'
                    : 'text-foreground hover:bg-white/50'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-border">
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start"
            data-testid="logout-button"
          >
            <LogOut size={20} className="mr-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {/* Read-Only Banner */}
        {isReadOnly && (
          <div 
            className="bg-warning text-warning-foreground px-6 py-4 flex items-center gap-4 sticky top-0 z-50 shadow-md"
            data-testid="subscription-expired-banner"
          >
            <AlertTriangle size={24} className="flex-shrink-0" />
            <div className="flex-1">
              <p className="font-semibold">Your subscription has expired. You are currently in read-only mode.</p>
              <p className="text-sm opacity-90">Renew your subscription to regain full access and continue managing your practice.</p>
            </div>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => window.open('mailto:support@haven.com?subject=Subscription Renewal', '_blank')}
              data-testid="contact-support-button"
            >
              Contact Support
            </Button>
          </div>
        )}

        <div className="max-w-7xl mx-auto p-6 md:p-12">
          {currentView === 'overview' && <TherapistOverview isReadOnly={isReadOnly} />}
          {currentView === 'clients' && <ClientManagement isReadOnly={isReadOnly} />}
          {currentView === 'appointments' && <AppointmentCalendar isReadOnly={isReadOnly} />}
          {currentView === 'availability' && <AvailabilitySettings isReadOnly={isReadOnly} />}
          {currentView === 'recurring' && <RecurringAppointments isReadOnly={isReadOnly} />}
          {currentView === 'notes' && <SessionNotes isReadOnly={isReadOnly} />}
          {currentView === 'messages' && <Messaging isReadOnly={isReadOnly} />}
          {currentView === 'assessments' && <Assessments isReadOnly={isReadOnly} />}
          {currentView === 'protocols' && <Protocols isReadOnly={isReadOnly} />}
          {currentView === 'payments' && <Payments isReadOnly={isReadOnly} />}
        </div>
      </main>
    </div>
  );
};

export default TherapistDashboard;
