import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { LogOut, Users, Calendar, FileText, MessageSquare, ClipboardList, BookOpen, DollarSign, Home, AlertTriangle, Clock, Repeat, UserCog, Brain, Settings as SettingsIcon, Sparkles } from 'lucide-react';
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
import AssistantManagement from '../components/AssistantManagement';
import AIClinicalSupport from '../components/AIClinicalSupport';
import Settings from '../components/Settings';

const TherapistDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('overview');
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isReadOnly, setIsReadOnly] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

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

  // Organized navigation - Clinical first, then Operations
  const navGroups = [
    {
      label: 'Clinical',
      items: [
        { id: 'overview', label: 'Dashboard', icon: Home },
        { id: 'clients', label: 'Clients', icon: Users },
        { id: 'appointments', label: 'Schedule', icon: Calendar },
        { id: 'notes', label: 'Session Notes', icon: FileText },
        { id: 'assessments', label: 'Assessments', icon: ClipboardList },
        { id: 'protocols', label: 'Protocols', icon: BookOpen },
        { id: 'ai-support', label: 'AI Clinical', icon: Brain },
      ]
    },
    {
      label: 'Operations',
      items: [
        { id: 'availability', label: 'Availability', icon: Clock },
        { id: 'recurring', label: 'Recurring', icon: Repeat },
        { id: 'messages', label: 'Messages', icon: MessageSquare },
        { id: 'payments', label: 'Payments', icon: DollarSign },
        { id: 'assistants', label: 'Assistants', icon: UserCog },
      ]
    }
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Organized Navigation */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col">
        <div className="p-5 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
              <Sparkles size={16} className="text-white" />
            </div>
            <h1 className="text-xl font-serif text-primary">TheraGenie</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-2 truncate">{user?.full_name}</p>
          {subscriptionStatus && !isReadOnly && (
            <span className="inline-block mt-2 px-2 py-1 bg-success/10 text-success text-xs rounded-full">
              {subscriptionStatus.subscription_status === 'trial' ? 'Free Trial' : 'Active'}
            </span>
          )}
        </div>

        <nav className="flex-1 p-3 overflow-y-auto">
          {navGroups.map((group, groupIdx) => (
            <div key={group.label} className={groupIdx > 0 ? 'mt-5' : ''}>
              <p className="px-3 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      data-testid={`nav-${item.id}`}
                      onClick={() => setCurrentView(item.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                        currentView === item.id
                          ? 'bg-primary text-white shadow-sm'
                          : 'text-foreground hover:bg-muted/60'
                      }`}
                    >
                      <Icon size={18} />
                      <span className="text-sm font-medium">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="p-3 border-t border-border space-y-1">
          <Button
            onClick={() => setShowSettings(true)}
            variant="ghost"
            className="w-full justify-start h-10"
            data-testid="settings-button"
          >
            <SettingsIcon size={18} className="mr-3" />
            Settings
          </Button>
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start h-10 text-muted-foreground hover:text-foreground"
            data-testid="logout-button"
          >
            <LogOut size={18} className="mr-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-background">
        {/* Read-Only Banner */}
        {isReadOnly && (
          <div 
            className="bg-warning text-warning-foreground px-6 py-3 flex items-center gap-4 sticky top-0 z-50 shadow-sm"
            data-testid="subscription-expired-banner"
          >
            <AlertTriangle size={20} className="flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium text-sm">Your subscription has expired. You are in read-only mode.</p>
            </div>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => window.open('mailto:support@theragenie.com?subject=Subscription Renewal', '_blank')}
              data-testid="contact-support-button"
            >
              Contact Support
            </Button>
          </div>
        )}

        <div className="max-w-7xl mx-auto p-6 lg:p-10">
          {currentView === 'overview' && (
            <TherapistOverview 
              isReadOnly={isReadOnly} 
              onNavigate={setCurrentView}
            />
          )}
          {currentView === 'clients' && <ClientManagement isReadOnly={isReadOnly} />}
          {currentView === 'appointments' && <AppointmentCalendar isReadOnly={isReadOnly} />}
          {currentView === 'availability' && <AvailabilitySettings isReadOnly={isReadOnly} />}
          {currentView === 'recurring' && <RecurringAppointments isReadOnly={isReadOnly} />}
          {currentView === 'notes' && <SessionNotes isReadOnly={isReadOnly} />}
          {currentView === 'messages' && <Messaging isReadOnly={isReadOnly} />}
          {currentView === 'assessments' && <Assessments isReadOnly={isReadOnly} />}
          {currentView === 'protocols' && <Protocols isReadOnly={isReadOnly} />}
          {currentView === 'ai-support' && <AIClinicalSupport isReadOnly={isReadOnly} />}
          {currentView === 'payments' && <Payments isReadOnly={isReadOnly} />}
          {currentView === 'assistants' && <AssistantManagement isReadOnly={isReadOnly} />}
        </div>
      </main>

      <Settings isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
};

export default TherapistDashboard;
