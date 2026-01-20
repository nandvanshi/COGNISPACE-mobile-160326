import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth, API } from '../App';
import { useSubscription } from '../contexts/SubscriptionContext';
import { Button } from '../components/ui/button';
import { LogOut, Users, CalendarDays, DollarSign, Home, AlertTriangle, UserCog, Sparkles, Menu, X } from 'lucide-react';
import ClientManagement from '../components/ClientManagement';
import TherapistSchedule from '../components/TherapistSchedule';
import Payments from '../components/Payments';
import { Card } from '../components/ui/card';

const AssistantOverview = ({ therapistInfo }) => {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl sm:text-4xl font-serif text-primary mb-2">Assistant Dashboard</h2>
        <p className="text-muted-foreground">Manage appointments and clients for your therapist</p>
      </div>

      {therapistInfo && (
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <UserCog size={28} className="text-primary" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-primary">Linked Therapist</h3>
              <p className="text-lg">{therapistInfo.full_name}</p>
              <p className="text-sm text-muted-foreground">{therapistInfo.email}</p>
            </div>
          </div>
        </Card>
      )}

      <Card className="p-6 bg-info/10 border border-info/20 rounded-xl">
        <h3 className="text-lg font-semibold text-info mb-2">Assistant Access</h3>
        <p className="text-sm text-info/80 mb-4">
          As an assistant, you can manage operational tasks but cannot access clinical data.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="font-medium text-success mb-1">You CAN:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>View and create clients</li>
              <li>Schedule and cancel appointments</li>
              <li>Block calendar time</li>
              <li>Modify availability settings</li>
              <li>View and record payments</li>
              <li>Check in/out sessions</li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-error mb-1">You CANNOT:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>View session notes</li>
              <li>Access assessments or protocols</li>
              <li>Access AI clinical features</li>
              <li>Delete clients permanently</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

const AssistantDashboard = () => {
  const { user, logout } = useAuth();
  const { isReadOnly, refreshStatus } = useSubscription();
  const [currentView, setCurrentView] = useState('overview');
  const [therapistInfo, setTherapistInfo] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    refreshStatus();
    fetchTherapistInfo();
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [currentView]);

  const fetchTherapistInfo = async () => {
    try {
      if (user?.therapist_id) {
        // Get therapist info
        const res = await axios.get(`${API}/auth/me`);
        if (res.data.therapist_id) {
          setTherapistInfo({
            id: res.data.therapist_id,
            full_name: 'Your Therapist',
            email: ''
          });
        }
      }
    } catch (error) {
      console.error('Failed to fetch therapist info:', error);
    }
  };

  // Limited nav items for assistants - can book appointments but NOT modify availability
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'schedule', label: 'Schedule', icon: CalendarDays },
    { id: 'payments', label: 'Payments', icon: DollarSign },
  ];

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  const getCurrentViewLabel = () => {
    const item = navItems.find(i => i.id === currentView);
    return item ? item.label : 'Dashboard';
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-surface border-b border-border">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
              <Sparkles size={18} className="text-white" />
            </div>
            <span className="font-serif text-xl text-primary">TheraGenie</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-base text-muted-foreground hidden sm:block">{getCurrentViewLabel()}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2"
              data-testid="mobile-menu-toggle"
            >
              {mobileMenuOpen ? <X size={26} /> : <Menu size={26} />}
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

      {/* Sidebar */}
      <aside className={`
        fixed lg:relative inset-y-0 left-0 z-50
        w-72 lg:w-64 bg-surface border-r border-border flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
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
          <span className="inline-block mt-2 px-2.5 py-1 bg-info/10 text-info text-sm rounded-full">
            Assistant
          </span>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                data-testid={`nav-${item.id}`}
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3.5 lg:py-2.5 rounded-lg transition-colors ${
                  currentView === item.id
                    ? 'bg-primary text-white'
                    : 'text-foreground hover:bg-white/50'
                }`}
              >
                <Icon size={20} />
                <span className="text-base lg:text-sm font-medium">{item.label}</span>
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
      <main className="flex-1 overflow-y-auto pt-14 lg:pt-0">
        {/* Read-Only Banner */}
        {isReadOnly && (
          <div 
            className="bg-warning text-warning-foreground px-4 lg:px-6 py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 sticky top-14 lg:top-0 z-40 shadow-sm"
            data-testid="subscription-expired-banner"
          >
            <div className="flex items-center gap-2 flex-1">
              <AlertTriangle size={20} className="flex-shrink-0" />
              <p className="font-medium text-sm">The therapist's subscription has expired. Read-only mode.</p>
            </div>
          </div>
        )}

        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-10">
          {currentView === 'overview' && <AssistantOverview therapistInfo={therapistInfo} />}
          {currentView === 'clients' && <ClientManagement isReadOnly={isReadOnly} isAssistant={true} />}
          {currentView === 'schedule' && (
            <TherapistSchedule 
              isReadOnly={isReadOnly} 
              isAssistant={false}
            />
          )}
          {currentView === 'availability' && <AvailabilitySettings isReadOnly={isReadOnly} />}
          {currentView === 'payments' && <Payments isReadOnly={isReadOnly} />}
        </div>
      </main>
    </div>
  );
};

export default AssistantDashboard;
