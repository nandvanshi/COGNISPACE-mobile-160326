import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { LogOut, Users, UserCheck, UserCog, CreditCard, Tag, Settings as SettingsIcon, MessageSquare, Home, Library, Mail, DatabaseZap, KeyRound, ScrollText } from 'lucide-react';
import { toast } from 'sonner';
import AdminOverview from '../components/admin/AdminOverview';
import TherapistApplications from '../components/admin/TherapistApplications';
import TherapistManagement from '../components/admin/TherapistManagement';
import ClientManagement from '../components/admin/ClientManagement';
import SubscriptionManagement from '../components/admin/SubscriptionManagement';
import CouponManagement from '../components/admin/CouponManagement';
import AdminSupportTickets from '../components/admin/AdminSupportTickets';
import AdminContentLibrary from '../components/admin/AdminContentLibrary';
import AdminEmailBroadcast from '../components/admin/AdminEmailBroadcast';
import AllUsers from '../components/admin/AllUsers';
import SystemConfig from '../components/admin/SystemConfig';
import UpdateLog from '../components/admin/UpdateLog';
import Settings from '../components/Settings';

const SuperAdminDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [currentView, setCurrentView] = useState('overview');
  const [showSettings, setShowSettings] = useState(false);
  const [buildInfo, setBuildInfo] = useState(null);

  // Fetch build info
  useEffect(() => {
    axios.get(`${API}/build-info`).then(r => setBuildInfo(r.data)).catch(() => {});
  }, []);

  // Sync currentView with URL hash for browser back button support
  useEffect(() => {
    const hash = location.hash.replace('#', '') || 'overview';
    if (hash !== currentView) {
      setCurrentView(hash);
    }
  }, [location.hash]);

  // Change view with URL hash update
  const changeView = (view) => {
    navigate(`/admin#${view}`, { replace: false });
    setCurrentView(view);
  };

  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: Home },
    { id: 'applications', label: 'Therapist Applications', icon: UserCheck },
    { id: 'therapists', label: 'Therapist Management', icon: UserCog },
    { id: 'clients', label: 'Client Management', icon: Users },
    { id: 'subscriptions', label: 'Subscription Plans', icon: CreditCard },
    { id: 'coupons', label: 'Coupon Codes', icon: Tag },
    { id: 'support', label: 'Support Tickets', icon: MessageSquare },
    { id: 'content-library', label: 'Content Library', icon: Library },
    { id: 'email-broadcast', label: 'Email Broadcast', icon: Mail },
    { id: 'all-users', label: 'All Users', icon: DatabaseZap },
    { id: 'system-config', label: 'System Config', icon: KeyRound },
    { id: 'update-log', label: 'Update Log', icon: ScrollText },
  ];

  const handleLogout = () => {
    logout();
    navigate('/admin-login');
  };

  // Navigation handler for Client -> Therapist navigation
  const handleViewTherapist = (therapistId, therapistName) => {
    toast.info(`Navigating to therapist: ${therapistName}`);
    changeView('therapists');
  };

  // Navigation handler for Therapist -> Clients navigation
  const handleViewTherapistClients = (therapistId) => {
    changeView('clients');
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-2xl font-serif text-primary">COGNISPACE Admin</h1>
          <p className="text-sm text-muted-foreground mt-1">Super Admin</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                data-testid={`admin-nav-${item.id}`}
                onClick={() => changeView(item.id)}
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

        <div className="p-4 border-t border-border space-y-2">
          {buildInfo?.build_timestamp && (
            <div className="px-3 py-2 bg-muted/50 rounded-lg mb-2" data-testid="build-info">
              <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide">Last Update</p>
              <p className="text-xs font-semibold text-primary">{buildInfo.build_timestamp}</p>
              {buildInfo.build_note && (
                <p className="text-[10px] text-muted-foreground mt-0.5 truncate" title={buildInfo.build_note}>{buildInfo.build_note}</p>
              )}
            </div>
          )}
          <Button
            onClick={() => setShowSettings(true)}
            variant="ghost"
            className="w-full justify-start"
            data-testid="admin-settings-button"
          >
            <SettingsIcon size={20} className="mr-3" />
            Settings
          </Button>
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start"
            data-testid="admin-logout-button"
          >
            <LogOut size={20} className="mr-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-6 md:p-12">
          {currentView === 'overview' && <AdminOverview onNavigate={setCurrentView} />}
          {currentView === 'applications' && <TherapistApplications />}
          {currentView === 'therapists' && <TherapistManagement onViewClients={handleViewTherapistClients} />}
          {currentView === 'clients' && <ClientManagement onViewTherapist={handleViewTherapist} />}
          {currentView === 'subscriptions' && <SubscriptionManagement />}
          {currentView === 'coupons' && <CouponManagement />}
          {currentView === 'support' && <AdminSupportTickets />}
          {currentView === 'content-library' && <AdminContentLibrary />}
          {currentView === 'email-broadcast' && <AdminEmailBroadcast />}
          {currentView === 'all-users' && <AllUsers />}
          {currentView === 'system-config' && <SystemConfig />}
          {currentView === 'update-log' && <UpdateLog />}
        </div>
      </main>

      <Settings isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
};

export default SuperAdminDashboard;
