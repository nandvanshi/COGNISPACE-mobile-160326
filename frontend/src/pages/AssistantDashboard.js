import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { LogOut, Users, Calendar, DollarSign, Home, AlertTriangle, UserCog } from 'lucide-react';
import ClientManagement from '../components/ClientManagement';
import AppointmentCalendar from '../components/AppointmentCalendar';
import Payments from '../components/Payments';
import { Card } from '../components/ui/card';

const AssistantOverview = ({ therapistInfo }) => {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-4xl font-serif text-primary mb-2">Assistant Dashboard</h2>
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
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="font-medium text-success mb-1">You CAN:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>View and create clients</li>
              <li>Schedule and cancel appointments</li>
              <li>Block calendar time</li>
              <li>View payments</li>
            </ul>
          </div>
          <div>
            <p className="font-medium text-error mb-1">You CANNOT:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>View session notes</li>
              <li>Access assessments or protocols</li>
              <li>Change availability settings</li>
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
  const [currentView, setCurrentView] = useState('overview');
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isReadOnly, setIsReadOnly] = useState(false);
  const [therapistInfo, setTherapistInfo] = useState(null);

  useEffect(() => {
    fetchSubscriptionStatus();
    fetchTherapistInfo();
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

  const fetchTherapistInfo = async () => {
    try {
      // Get therapist info from the therapist_id
      if (user?.therapist_id) {
        // We'll get therapist info from clients endpoint indirectly
        // For now, just show basic info
        setTherapistInfo({
          id: user.therapist_id,
          full_name: 'Your Therapist',
          email: ''
        });
      }
    } catch (error) {
      console.error('Failed to fetch therapist info:', error);
    }
  };

  // Limited nav items for assistants
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'appointments', label: 'Appointments', icon: Calendar },
    { id: 'payments', label: 'Payments', icon: DollarSign },
  ];

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-2xl font-serif text-primary">TheraGenie</h1>
          <p className="text-sm text-muted-foreground mt-1">{user?.full_name}</p>
          <span className="inline-block mt-2 px-2 py-1 bg-info/10 text-info text-xs rounded-full">
            Assistant
          </span>
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
              <p className="font-semibold">The therapist's subscription has expired. Read-only mode is active.</p>
              <p className="text-sm opacity-90">Contact your therapist to renew their subscription.</p>
            </div>
          </div>
        )}

        <div className="max-w-7xl mx-auto p-6 md:p-12">
          {currentView === 'overview' && <AssistantOverview therapistInfo={therapistInfo} />}
          {currentView === 'clients' && <ClientManagement isReadOnly={isReadOnly} isAssistant={true} />}
          {currentView === 'appointments' && <AppointmentCalendar isReadOnly={isReadOnly} />}
          {currentView === 'payments' && <Payments isReadOnly={isReadOnly} />}
        </div>
      </main>
    </div>
  );
};

export default AssistantDashboard;
