import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { LogOut, Users, UserCheck, UserCog } from 'lucide-react';
import TherapistApplications from '../components/admin/TherapistApplications';
import TherapistManagement from '../components/admin/TherapistManagement';
import ClientManagement from '../components/admin/ClientManagement';

const SuperAdminDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('applications');

  const navItems = [
    { id: 'applications', label: 'Therapist Applications', icon: UserCheck },
    { id: 'therapists', label: 'Therapist Management', icon: UserCog },
    { id: 'clients', label: 'Client Management', icon: Users },
  ];

  const handleLogout = () => {
    logout();
    navigate('/admin-login');
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-2xl font-serif text-primary">Haven Admin</h1>
          <p className="text-sm text-muted-foreground mt-1">Super Admin</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                data-testid={`admin-nav-${item.id}`}
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
          {currentView === 'applications' && <TherapistApplications />}
          {currentView === 'therapists' && <TherapistManagement />}
          {currentView === 'clients' && <ClientManagement />}
        </div>
      </main>
    </div>
  );
};

export default SuperAdminDashboard;
