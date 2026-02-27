import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth, API } from '../../App';
import { useSubscription } from '../../contexts/SubscriptionContext';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { 
  Home, Users, Calendar, DollarSign, MoreHorizontal, 
  Search, Plus, Bell, ChevronRight, Clock, FileText,
  Phone, MessageSquare, Play, CheckCircle, AlertCircle,
  TrendingUp, User, LogOut, Settings, HelpCircle,
  BookOpen, ClipboardList, Repeat, UserCog, Brain, Loader2, X
} from 'lucide-react';
import { toast } from 'sonner';
import { formatCurrency, formatDate, formatTime } from '../../utils/formatUtils';
import NotificationBell from '../NotificationBell';

// ============= BOTTOM NAVIGATION =============
const BottomNav = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'payments', label: 'Payments', icon: DollarSign },
    { id: 'more', label: 'More', icon: MoreHorizontal },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 safe-area-bottom">
      <div className="flex justify-around items-center h-16">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                isActive 
                  ? 'text-violet-600' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
              data-testid={`nav-${tab.id}`}
            >
              <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-xs mt-1 ${isActive ? 'font-medium' : ''}`}>
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

// ============= HOME TAB =============
const HomeTab = ({ stats, upcomingAppointments, pendingTasks, onStartSession, onViewClient, onQuickAction }) => {
  const { user } = useAuth();
  
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  return (
    <div className="space-y-4 pb-4">
      {/* Greeting */}
      <div className="bg-gradient-to-r from-violet-600 to-indigo-600 rounded-2xl p-4 text-white">
        <p className="text-violet-200 text-sm">{getGreeting()}</p>
        <h1 className="text-xl font-bold">{user?.full_name || 'Doctor'}</h1>
        <p className="text-violet-200 text-sm mt-1">
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
        </p>
      </div>

      {/* Today's Stats */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="p-3 text-center rounded-xl">
          <p className="text-2xl font-bold text-violet-600">{stats.todayAppointments || 0}</p>
          <p className="text-xs text-gray-500">Sessions</p>
        </Card>
        <Card className="p-3 text-center rounded-xl">
          <p className="text-2xl font-bold text-emerald-600">{formatCurrency(stats.todayRevenue || 0)}</p>
          <p className="text-xs text-gray-500">Revenue</p>
        </Card>
        <Card className="p-3 text-center rounded-xl">
          <p className="text-2xl font-bold text-amber-600">{stats.pendingNotes || 0}</p>
          <p className="text-xs text-gray-500">Pending</p>
        </Card>
      </div>

      {/* Next Appointment */}
      {upcomingAppointments.length > 0 && (
        <Card className="p-4 rounded-2xl border-l-4 border-l-violet-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-violet-600 font-medium">NEXT SESSION</p>
              <p className="font-semibold text-gray-900">{upcomingAppointments[0].client_name}</p>
              <p className="text-sm text-gray-500">
                {formatTime(upcomingAppointments[0].start_time)}
              </p>
            </div>
            <Button 
              onClick={() => onStartSession(upcomingAppointments[0])}
              className="rounded-xl bg-violet-600 hover:bg-violet-700"
              size="sm"
            >
              <Play size={16} className="mr-1" /> Start
            </Button>
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Quick Actions</h3>
        <div className="grid grid-cols-4 gap-2">
          {[
            { icon: Plus, label: 'Client', action: 'add-client', color: 'bg-blue-50 text-blue-600' },
            { icon: Calendar, label: 'Book', action: 'book', color: 'bg-green-50 text-green-600' },
            { icon: DollarSign, label: 'Payment', action: 'payment', color: 'bg-amber-50 text-amber-600' },
            { icon: FileText, label: 'Note', action: 'note', color: 'bg-purple-50 text-purple-600' },
          ].map((item) => (
            <button
              key={item.action}
              onClick={() => onQuickAction(item.action)}
              className={`flex flex-col items-center p-3 rounded-xl ${item.color} transition-transform active:scale-95`}
            >
              <item.icon size={20} />
              <span className="text-xs mt-1 font-medium">{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Pending Tasks */}
      {pendingTasks.length > 0 && (
        <Card className="p-4 rounded-2xl">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-gray-900">Pending Tasks</h3>
            <Badge variant="secondary" className="bg-amber-100 text-amber-700">
              {pendingTasks.length}
            </Badge>
          </div>
          <div className="space-y-2">
            {pendingTasks.slice(0, 3).map((task, idx) => (
              <div key={idx} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                <AlertCircle size={16} className="text-amber-500" />
                <span className="text-sm text-gray-700 flex-1">{task.title}</span>
                <ChevronRight size={16} className="text-gray-400" />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Today's Schedule */}
      <Card className="p-4 rounded-2xl">
        <h3 className="font-medium text-gray-900 mb-3">Today's Schedule</h3>
        {upcomingAppointments.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No appointments today</p>
        ) : (
          <div className="space-y-2">
            {upcomingAppointments.map((appt) => (
              <div 
                key={appt.id} 
                onClick={() => onViewClient(appt.client_id)}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100 transition-colors"
              >
                <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                  <User size={18} className="text-violet-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{appt.client_name}</p>
                  <p className="text-xs text-gray-500">{formatTime(appt.start_time)}</p>
                </div>
                <Badge 
                  className={appt.status === 'checked_in' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}
                >
                  {appt.status === 'checked_in' ? 'Checked In' : 'Scheduled'}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

// ============= CLIENTS TAB =============
const ClientsTab = ({ clients, loading, onViewClient, onAddClient }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredClients = clients.filter(client => 
    client.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    client.mobile?.includes(searchQuery)
  );

  return (
    <div className="space-y-4 pb-4">
      {/* Header with Add Button */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <Input
            placeholder="Search clients..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 rounded-xl bg-gray-50 border-0"
          />
        </div>
        <Button 
          onClick={onAddClient}
          className="rounded-xl bg-violet-600 hover:bg-violet-700"
          size="icon"
          data-testid="add-client-btn"
        >
          <Plus size={20} />
        </Button>
      </div>

      {/* Client List */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : filteredClients.length === 0 ? (
        <div className="text-center py-8">
          <Users size={48} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">{searchQuery ? 'No clients found' : 'No clients yet'}</p>
          <Button 
            onClick={onAddClient}
            variant="outline"
            className="mt-4 rounded-xl"
          >
            <Plus size={16} className="mr-2" /> Add First Client
          </Button>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredClients.map((client) => (
            <Card 
              key={client.id}
              onClick={() => onViewClient(client.id)}
              className="p-4 rounded-xl cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-violet-100 flex items-center justify-center">
                  <span className="text-lg font-semibold text-violet-600">
                    {client.full_name?.charAt(0) || 'C'}
                  </span>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{client.full_name}</p>
                  <p className="text-sm text-gray-500">{client.mobile}</p>
                </div>
                <ChevronRight size={20} className="text-gray-400" />
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// ============= MORE TAB =============
const MoreTab = ({ onNavigate, onLogout }) => {
  const menuItems = [
    { id: 'homework-templates', label: 'Homework Templates', icon: ClipboardList },
    { id: 'resource-library', label: 'Resource Library', icon: BookOpen },
    { divider: true },
    { id: 'availability', label: 'Availability', icon: Clock },
    { id: 'recurring', label: 'Recurring Sessions', icon: Repeat },
    { id: 'assistants', label: 'Assistants', icon: UserCog },
    { divider: true },
    { id: 'profile', label: 'My Profile', icon: User },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'support', label: 'Help & Support', icon: HelpCircle },
  ];

  return (
    <div className="space-y-2 pb-4">
      {menuItems.map((item, idx) => 
        item.divider ? (
          <div key={idx} className="h-px bg-gray-200 my-2" />
        ) : (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className="w-full flex items-center gap-3 p-4 bg-white rounded-xl hover:bg-gray-50 transition-colors"
          >
            <item.icon size={20} className="text-gray-600" />
            <span className="flex-1 text-left font-medium text-gray-900">{item.label}</span>
            <ChevronRight size={18} className="text-gray-400" />
          </button>
        )
      )}
      
      <button
        onClick={onLogout}
        className="w-full flex items-center gap-3 p-4 bg-red-50 rounded-xl mt-4"
      >
        <LogOut size={20} className="text-red-600" />
        <span className="flex-1 text-left font-medium text-red-600">Logout</span>
      </button>
    </div>
  );
};

// ============= MAIN MOBILE VIEW COMPONENT =============
const MobileTherapistView = ({ 
  onViewChange, 
  onClientSelect, 
  currentView,
  setCurrentView 
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('home');
  const [stats, setStats] = useState({});
  const [upcomingAppointments, setUpcomingAppointments] = useState([]);
  const [pendingTasks, setPendingTasks] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddClient, setShowAddClient] = useState(false);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      const [statsRes, appointmentsRes, clientsRes] = await Promise.all([
        axios.get(`${API}/therapist/dashboard-stats`).catch(() => ({ data: {} })),
        axios.get(`${API}/appointments?date=${new Date().toISOString().split('T')[0]}`).catch(() => ({ data: [] })),
        axios.get(`${API}/clients`).catch(() => ({ data: [] })),
      ]);

      setStats(statsRes.data || {});
      
      const now = new Date();
      const upcoming = (appointmentsRes.data || [])
        .filter(a => new Date(a.start_time) >= now && a.status !== 'cancelled')
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
      setUpcomingAppointments(upcoming);
      
      setClients(clientsRes.data || []);
      
      // Generate pending tasks
      const tasks = [];
      if (statsRes.data?.pending_notes > 0) {
        tasks.push({ title: `${statsRes.data.pending_notes} session notes pending` });
      }
      if (statsRes.data?.pending_payments > 0) {
        tasks.push({ title: `${statsRes.data.pending_payments} payments pending` });
      }
      setPendingTasks(tasks);
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'schedule') {
      onViewChange('schedule');
    } else if (tab === 'payments') {
      onViewChange('payments');
    }
  };

  const handleViewClient = (clientId) => {
    onClientSelect(clientId);
  };

  const handleStartSession = (appointment) => {
    handleViewClient(appointment.client_id);
  };

  const handleAddClient = () => {
    // Navigate to clients page with hash for add client
    navigate('/therapist#clients');
    onViewChange('clients');
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'add-client':
        handleAddClient();
        break;
      case 'book':
        onViewChange('schedule');
        setActiveTab('schedule');
        break;
      case 'payment':
        onViewChange('payments');
        setActiveTab('payments');
        break;
      case 'note':
        onViewChange('notes');
        break;
      default:
        break;
    }
  };

  const handleMoreNavigate = (id) => {
    onViewChange(id);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // If schedule or payments tab is active, let parent handle rendering
  if (activeTab === 'schedule' || activeTab === 'payments') {
    return (
      <>
        <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white border-b border-gray-100 px-4 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">
            {activeTab === 'home' && 'Dashboard'}
            {activeTab === 'clients' && 'Clients'}
            {activeTab === 'more' && 'More'}
          </h1>
          <div className="flex items-center gap-2">
            <NotificationBell />
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="px-4 py-4">
        {activeTab === 'home' && (
          <HomeTab
            stats={stats}
            upcomingAppointments={upcomingAppointments}
            pendingTasks={pendingTasks}
            onStartSession={handleStartSession}
            onViewClient={handleViewClient}
            onQuickAction={handleQuickAction}
          />
        )}
        {activeTab === 'clients' && (
          <ClientsTab
            clients={clients}
            loading={loading}
            onViewClient={handleViewClient}
            onAddClient={handleAddClient}
          />
        )}
        {activeTab === 'more' && (
          <MoreTab
            onNavigate={handleMoreNavigate}
            onLogout={handleLogout}
          />
        )}
      </main>

      {/* Bottom Navigation */}
      <BottomNav activeTab={activeTab} onTabChange={handleTabChange} />
    </div>
  );
};

export default MobileTherapistView;
