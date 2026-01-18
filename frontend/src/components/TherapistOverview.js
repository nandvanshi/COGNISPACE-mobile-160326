import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { 
  Calendar, Users, FileText, MessageSquare, Clock, 
  Plus, Ban, Bell, AlertTriangle, ChevronRight,
  CheckCircle, BookOpen, User, ClipboardList
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDate, formatTime, formatTimeRange, formatDateLong, getRelativeDate, getTimeUntil, toIST, nowIST } from '../utils/formatUtils';

const TherapistOverview = ({ isReadOnly = false }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    todayAppointments: 0,
    unreadMessages: 0,
    pendingHomework: 0,
    totalClients: 0,
    upcomingAppointments: 0,
    completedToday: 0,
  });
  const [todaySchedule, setTodaySchedule] = useState([]);
  const [activeClients, setActiveClients] = useState([]);
  const [nextAppointment, setNextAppointment] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [subscriptionInfo, setSubscriptionInfo] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [
        clientsRes, 
        apptsRes, 
        messagesRes, 
        subscriptionRes,
        notesRes
      ] = await Promise.all([
        axios.get(`${API}/clients`),
        axios.get(`${API}/appointments`),
        axios.get(`${API}/messages`).catch(() => ({ data: [] })),
        axios.get(`${API}/auth/subscription-status`),
        axios.get(`${API}/session-notes`).catch(() => ({ data: [] })),
      ]);

      // Calculate today's stats
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const now = new Date();

      const allAppts = apptsRes.data;
      const todayAppts = allAppts.filter((appt) => {
        const apptDate = new Date(appt.start_time);
        return apptDate >= today && apptDate < tomorrow && appt.status !== 'cancelled';
      }).sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

      const completedToday = todayAppts.filter(a => a.status === 'completed').length;

      // Find next upcoming appointment
      const upcomingAppts = allAppts
        .filter(a => new Date(a.start_time) > now && a.status === 'scheduled')
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
      
      // Count unread messages
      const unreadCount = messagesRes.data.filter(m => !m.read && m.recipient_id === user?.id).length;

      // Get active clients (clients with appointments in last 30 days)
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      
      const recentApptsMap = {};
      allAppts.forEach(appt => {
        if (appt.status === 'completed' && new Date(appt.start_time) > thirtyDaysAgo) {
          if (!recentApptsMap[appt.client_id] || new Date(appt.start_time) > new Date(recentApptsMap[appt.client_id].start_time)) {
            recentApptsMap[appt.client_id] = appt;
          }
        }
      });

      const activeClientsList = clientsRes.data
        .filter(c => recentApptsMap[c.id])
        .map(c => ({
          ...c,
          lastSession: recentApptsMap[c.id]
        }))
        .sort((a, b) => new Date(b.lastSession.start_time) - new Date(a.lastSession.start_time))
        .slice(0, 5);

      // Generate alerts
      const alertsList = [];
      
      // Alert for clients without recent sessions
      const inactiveClients = clientsRes.data.filter(c => !recentApptsMap[c.id]).length;
      if (inactiveClients > 0) {
        alertsList.push({
          type: 'info',
          message: `${inactiveClients} client(s) haven't had sessions in 30+ days`,
          icon: Users
        });
      }

      // Alert for pending notes
      const completedWithoutNotes = allAppts.filter(a => {
        if (a.status !== 'completed') return false;
        const hasNote = notesRes.data.some(n => n.appointment_id === a.id);
        return !hasNote;
      }).length;
      
      if (completedWithoutNotes > 0) {
        alertsList.push({
          type: 'warning',
          message: `${completedWithoutNotes} completed session(s) need notes`,
          icon: FileText
        });
      }

      // Subscription expiry warning
      if (subscriptionRes.data.subscription_status === 'trial') {
        alertsList.push({
          type: 'info',
          message: 'You are on a free trial',
          icon: Bell
        });
      }

      setStats({
        todayAppointments: todayAppts.length,
        unreadMessages: unreadCount,
        pendingHomework: 0, // Placeholder - would need homework tracking
        totalClients: clientsRes.data.length,
        upcomingAppointments: upcomingAppts.length,
        completedToday,
      });

      setTodaySchedule(todayAppts);
      setActiveClients(activeClientsList);
      setNextAppointment(upcomingAppts[0] || null);
      setAlerts(alertsList);
      setSubscriptionInfo(subscriptionRes.data);

    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getSubscriptionBadge = () => {
    if (!subscriptionInfo) return null;
    const status = subscriptionInfo.subscription_status;
    const plan = subscriptionInfo.subscription_plan;
    
    if (isReadOnly || status === 'expired' || status === 'cancelled') {
      return (
        <span className="px-3 py-1 bg-error/10 text-error text-xs font-medium rounded-full">
          {status === 'expired' ? 'Expired' : status === 'cancelled' ? 'Cancelled' : 'Read-Only'}
        </span>
      );
    }
    if (status === 'trial') {
      return (
        <span className="px-3 py-1 bg-info/10 text-info text-xs font-medium rounded-full">
          Free Trial
        </span>
      );
    }
    return (
      <span className="px-3 py-1 bg-success/10 text-success text-xs font-medium rounded-full">
        {plan || 'Active'}
      </span>
    );
  };

  const formatTime = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  const getTimeUntil = (dateStr) => {
    const now = new Date();
    const target = new Date(dateStr);
    const diff = target - now;
    
    if (diff < 0) return 'Started';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `in ${days} day${days > 1 ? 's' : ''}`;
    }
    if (hours > 0) return `in ${hours}h ${minutes}m`;
    return `in ${minutes}m`;
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div data-testid="therapist-dashboard" className="space-y-6">
      {/* Header with Profile */}
      <div className="flex items-center justify-between flex-wrap gap-4 pb-6 border-b border-border/40">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-primary-700 flex items-center justify-center text-white text-2xl font-serif shadow-lg">
            {user?.full_name?.charAt(0) || 'T'}
          </div>
          <div>
            <h1 className="text-3xl font-serif text-primary">{user?.full_name || 'Therapist'}</h1>
            <div className="flex items-center gap-2 mt-1">
              {getSubscriptionBadge()}
              <span className="text-sm text-muted-foreground">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </span>
            </div>
          </div>
        </div>
        
        {isReadOnly && (
          <div className="flex items-center gap-2 px-4 py-2 bg-warning/10 border border-warning/30 rounded-lg">
            <AlertTriangle size={18} className="text-warning" />
            <span className="text-sm text-warning-foreground">Read-only mode active</span>
          </div>
        )}
      </div>

      {/* Today at a Glance */}
      <div>
        <h2 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
          <Clock size={20} className="text-primary" />
          Today at a Glance
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-5 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-primary">{stats.todayAppointments}</p>
                <p className="text-sm text-muted-foreground">Today's Appointments</p>
                {stats.completedToday > 0 && (
                  <p className="text-xs text-success mt-1">{stats.completedToday} completed</p>
                )}
              </div>
              <div className="p-3 bg-primary/10 rounded-full">
                <Calendar size={24} className="text-primary" />
              </div>
            </div>
          </Card>

          <Card className="p-5 bg-gradient-to-br from-info/5 to-info/10 border-info/20 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-info">{stats.unreadMessages}</p>
                <p className="text-sm text-muted-foreground">Unread Messages</p>
              </div>
              <div className="p-3 bg-info/10 rounded-full">
                <MessageSquare size={24} className="text-info" />
              </div>
            </div>
          </Card>

          <Card className="p-5 bg-gradient-to-br from-warning/5 to-warning/10 border-warning/20 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-warning">{stats.pendingHomework}</p>
                <p className="text-sm text-muted-foreground">Pending Homework</p>
              </div>
              <div className="p-3 bg-warning/10 rounded-full">
                <BookOpen size={24} className="text-warning" />
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Today's Schedule & Quick Actions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Today's Schedule */}
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <Calendar size={20} className="text-primary" />
                Today's Schedule
              </h3>
              <span className="text-sm text-muted-foreground">{stats.todayAppointments} session(s)</span>
            </div>
            
            {todaySchedule.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar size={40} className="mx-auto mb-3 opacity-30" />
                <p>No appointments scheduled for today</p>
                {!isReadOnly && (
                  <Button variant="outline" size="sm" className="mt-3">
                    <Plus size={16} className="mr-2" />
                    Schedule Appointment
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {todaySchedule.map((appt, idx) => {
                  const isPast = new Date(appt.end_time) < new Date();
                  const isNext = !isPast && idx === todaySchedule.findIndex(a => new Date(a.end_time) >= new Date());
                  
                  return (
                    <div
                      key={appt.id}
                      className={`p-4 rounded-xl border transition-all ${
                        appt.status === 'completed' 
                          ? 'bg-success/5 border-success/20' 
                          : isNext 
                            ? 'bg-primary/5 border-primary/30 ring-2 ring-primary/20' 
                            : isPast 
                              ? 'bg-muted/50 border-border/30 opacity-60' 
                              : 'bg-surface border-border/40'
                      }`}
                      data-testid={`schedule-item-${appt.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-1 h-12 rounded-full ${
                            appt.status === 'completed' ? 'bg-success' : isNext ? 'bg-primary' : 'bg-muted-foreground/30'
                          }`} />
                          <div>
                            <p className="font-medium text-foreground">{appt.client_name}</p>
                            <p className="text-sm text-muted-foreground">
                              {formatTime(appt.start_time)} - {formatTime(appt.end_time)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {appt.status === 'completed' ? (
                            <span className="flex items-center gap-1 text-xs text-success">
                              <CheckCircle size={14} />
                              Completed
                            </span>
                          ) : isNext ? (
                            <span className="px-2 py-1 bg-primary text-white text-xs rounded-full">
                              Up Next
                            </span>
                          ) : null}
                        </div>
                      </div>
                      {appt.notes && (
                        <p className="text-sm text-muted-foreground mt-2 ml-4 pl-3 border-l-2 border-border">
                          {appt.notes}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Quick Actions */}
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
              <Plus size={20} className="text-primary" />
              Quick Actions
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Button
                variant="outline"
                className={`h-auto py-4 flex-col gap-2 ${isReadOnly ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary/5 hover:border-primary/30'}`}
                disabled={isReadOnly}
                data-testid="quick-add-client"
              >
                <Users size={24} className="text-primary" />
                <span className="text-sm">Add Client</span>
              </Button>
              <Button
                variant="outline"
                className={`h-auto py-4 flex-col gap-2 ${isReadOnly ? 'opacity-50 cursor-not-allowed' : 'hover:bg-info/5 hover:border-info/30'}`}
                disabled={isReadOnly}
                data-testid="quick-add-appointment"
              >
                <Calendar size={24} className="text-info" />
                <span className="text-sm">Add Appointment</span>
              </Button>
              <Button
                variant="outline"
                className={`h-auto py-4 flex-col gap-2 ${isReadOnly ? 'opacity-50 cursor-not-allowed' : 'hover:bg-warning/5 hover:border-warning/30'}`}
                disabled={isReadOnly}
                data-testid="quick-block-time"
              >
                <Ban size={24} className="text-warning" />
                <span className="text-sm">Block Time</span>
              </Button>
              <Button
                variant="outline"
                className={`h-auto py-4 flex-col gap-2 ${isReadOnly ? 'opacity-50 cursor-not-allowed' : 'hover:bg-success/5 hover:border-success/30'}`}
                disabled={isReadOnly}
                data-testid="quick-add-notes"
              >
                <FileText size={24} className="text-success" />
                <span className="text-sm">Add Notes</span>
              </Button>
            </div>
          </Card>

          {/* Active Clients Snapshot */}
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <Users size={20} className="text-primary" />
                Active Clients
              </h3>
              <span className="text-sm text-muted-foreground">{stats.totalClients} total</span>
            </div>
            
            {activeClients.length === 0 ? (
              <div className="text-center py-6 text-muted-foreground">
                <Users size={40} className="mx-auto mb-3 opacity-30" />
                <p>No recent client sessions</p>
              </div>
            ) : (
              <div className="space-y-3">
                {activeClients.map((client) => (
                  <div
                    key={client.id}
                    className="flex items-center justify-between p-3 bg-surface rounded-lg hover:bg-muted/50 transition-colors"
                    data-testid={`client-snapshot-${client.id}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <User size={18} className="text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{client.full_name}</p>
                        <p className="text-xs text-muted-foreground">
                          Last session: {formatDate(client.lastSession.start_time)}
                        </p>
                      </div>
                    </div>
                    <ChevronRight size={18} className="text-muted-foreground" />
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column - Next Session & Alerts */}
        <div className="space-y-6">
          {/* Session Preparation Panel */}
          <Card className="p-6 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
            <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
              <ClipboardList size={20} className="text-primary" />
              Next Session
            </h3>
            
            {nextAppointment ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                    <User size={24} className="text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold text-lg text-foreground">{nextAppointment.client_name}</p>
                    <p className="text-sm text-primary font-medium">{getTimeUntil(nextAppointment.start_time)}</p>
                  </div>
                </div>
                
                <div className="p-3 bg-white/50 rounded-lg space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Date</span>
                    <span className="font-medium">{formatDate(nextAppointment.start_time)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Time</span>
                    <span className="font-medium">
                      {formatTime(nextAppointment.start_time)} - {formatTime(nextAppointment.end_time)}
                    </span>
                  </div>
                </div>
                
                {nextAppointment.notes && (
                  <div className="p-3 bg-white/50 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Session Notes</p>
                    <p className="text-sm">{nextAppointment.notes}</p>
                  </div>
                )}
                
                <div className="pt-2">
                  <p className="text-xs text-muted-foreground mb-2">Preparation Checklist:</p>
                  <div className="space-y-1.5">
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" className="rounded border-border" />
                      <span>Review previous session notes</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" className="rounded border-border" />
                      <span>Check pending assessments</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" className="rounded border-border" />
                      <span>Prepare session materials</span>
                    </label>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <Calendar size={40} className="mx-auto mb-3 opacity-30" />
                <p>No upcoming appointments</p>
              </div>
            )}
          </Card>

          {/* Alerts & Reminders */}
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
              <Bell size={20} className="text-warning" />
              Alerts & Reminders
            </h3>
            
            {alerts.length === 0 ? (
              <div className="text-center py-6 text-muted-foreground">
                <CheckCircle size={40} className="mx-auto mb-3 text-success opacity-50" />
                <p className="text-sm">All caught up!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert, idx) => {
                  const Icon = alert.icon;
                  return (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border flex items-start gap-3 ${
                        alert.type === 'warning' 
                          ? 'bg-warning/5 border-warning/20' 
                          : alert.type === 'error'
                            ? 'bg-error/5 border-error/20'
                            : 'bg-info/5 border-info/20'
                      }`}
                      data-testid={`alert-${idx}`}
                    >
                      <Icon size={18} className={
                        alert.type === 'warning' ? 'text-warning' : 
                        alert.type === 'error' ? 'text-error' : 'text-info'
                      } />
                      <p className="text-sm">{alert.message}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Practice Stats */}
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <h3 className="text-lg font-semibold text-foreground mb-4">Practice Overview</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Total Clients</span>
                <span className="font-semibold text-foreground">{stats.totalClients}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Upcoming Sessions</span>
                <span className="font-semibold text-foreground">{stats.upcomingAppointments}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Active This Month</span>
                <span className="font-semibold text-foreground">{activeClients.length}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Clinical Disclaimer */}
      <div className="p-4 bg-muted/50 border border-border/40 rounded-xl">
        <p className="text-xs text-muted-foreground text-center">
          <strong>Clinical Support Tool:</strong> This platform provides decision support. 
          All clinical judgments and treatment decisions remain with the licensed therapist.
        </p>
      </div>
    </div>
  );
};

export default TherapistOverview;
