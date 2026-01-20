import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { LogOut, Users, Calendar, FileText, MessageSquare, ClipboardList, BookOpen, DollarSign, Home, AlertTriangle, Clock, Repeat, UserCog, Brain, Settings as SettingsIcon, Sparkles, Menu, X, ChevronDown } from 'lucide-react';
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState('Clinical');

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  // Close mobile menu on view change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [currentView]);

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

  // Get current view label for mobile header
  const getCurrentViewLabel = () => {
    for (const group of navGroups) {
      const item = group.items.find(i => i.id === currentView);
      if (item) return item.label;
    }
    return 'Dashboard';
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleNavClick = (viewId) => {
    setCurrentView(viewId);
    setMobileMenuOpen(false);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-surface border-b border-border">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
              <Sparkles size={16} className="text-white" />
            </div>
            <span className="font-serif text-lg text-primary">TheraGenie</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground hidden sm:block">{getCurrentViewLabel()}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2"
              data-testid="mobile-menu-toggle"
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - Desktop: fixed, Mobile: slide-out */}
      <aside className={`
        fixed lg:relative inset-y-0 left-0 z-50
        w-72 lg:w-64 bg-surface border-r border-border flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo Section */}
        <div className="p-5 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
                <Sparkles size={18} className="text-white" />
              </div>
              <h1 className="text-xl font-serif text-primary">TheraGenie</h1>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden p-2"
            >
              <X size={22} />
            </Button>
          </div>
          <p className="text-base text-muted-foreground mt-2 truncate">{user?.full_name}</p>
          {subscriptionStatus && !isReadOnly && (
            <span className="inline-block mt-2 px-2.5 py-1 bg-success/10 text-success text-sm rounded-full">
              {subscriptionStatus.subscription_status === 'trial' ? 'Free Trial' : 'Active'}
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 overflow-y-auto">
          {navGroups.map((group, groupIdx) => (
            <div key={group.label} className={groupIdx > 0 ? 'mt-4' : ''}>
              {/* Collapsible group header for mobile */}
              <button
                onClick={() => setExpandedGroup(expandedGroup === group.label ? '' : group.label)}
                className="w-full flex items-center justify-between px-3 py-2.5 lg:py-0 lg:mb-2 rounded-lg lg:rounded-none hover:bg-muted/50 lg:hover:bg-transparent"
              >
                <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                  {group.label}
                </p>
                <ChevronDown 
                  size={18} 
                  className={`lg:hidden text-muted-foreground transition-transform ${expandedGroup === group.label ? 'rotate-180' : ''}`}
                />
              </button>
              
              {/* Nav items - always visible on desktop, collapsible on mobile */}
              <div className={`space-y-0.5 overflow-hidden transition-all duration-200 ${
                expandedGroup === group.label ? 'max-h-96 opacity-100' : 'max-h-0 lg:max-h-96 opacity-0 lg:opacity-100'
              }`}>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      data-testid={`nav-${item.id}`}
                      onClick={() => handleNavClick(item.id)}
                      className={`w-full flex items-center gap-3 px-3 py-3 lg:py-2.5 rounded-lg transition-all ${
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

        {/* Footer Actions */}
        <div className="p-3 border-t border-border space-y-1">
          <Button
            onClick={() => { setShowSettings(true); setMobileMenuOpen(false); }}
            variant="ghost"
            className="w-full justify-start h-12 lg:h-10"
            data-testid="settings-button"
          >
            <SettingsIcon size={18} className="mr-3" />
            Settings
          </Button>
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start h-12 lg:h-10 text-muted-foreground hover:text-foreground"
            data-testid="logout-button"
          >
            <LogOut size={18} className="mr-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-background pt-14 lg:pt-0">
        {/* Read-Only Banner */}
        {isReadOnly && (
          <div 
            className="bg-warning text-warning-foreground px-4 lg:px-6 py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 sticky top-14 lg:top-0 z-40 shadow-sm"
            data-testid="subscription-expired-banner"
          >
            <div className="flex items-center gap-2 flex-1">
              <AlertTriangle size={20} className="flex-shrink-0" />
              <p className="font-medium text-sm">Subscription expired. Read-only mode.</p>
            </div>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => window.open('mailto:support@theragenie.com?subject=Subscription Renewal', '_blank')}
              data-testid="contact-support-button"
              className="w-full sm:w-auto"
            >
              Contact Support
            </Button>
          </div>
        )}

        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-10">
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
