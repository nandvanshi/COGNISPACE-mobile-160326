import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { 
  Calendar, Users, FileText, MessageSquare, Clock, 
  Plus, Bell, AlertTriangle, ChevronRight, ArrowRight,
  CheckCircle, User, ClipboardList, CalendarDays, 
  CalendarPlus, Sparkles, SunMedium, Moon, Sunset,
  DollarSign, TrendingUp, XCircle, UserX, FileWarning, UserPlus
} from 'lucide-react';
import { toast } from 'sonner';
import { formatTime, formatTimeRange, formatDateLong, getRelativeDate, getTimeUntil, toIST, nowIST, formatCurrency } from '../utils/formatUtils';
import ClientRegistrationLink from './ClientRegistrationLink';

const TherapistOverview = ({ isReadOnly = false, onNavigate }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    todayAppointments: 0,
    unreadMessages: 0,
    totalClients: 0,
    upcomingAppointments: 0,
    completedToday: 0,
    pendingNotes: 0,
    // Week stats
    weekSessions: 0,
    weekCompleted: 0,
    weekCancelled: 0,
    weekNoShows: 0,
    // Payment stats
    paymentsPending: 0,
    paymentsReceived: 0,
    pendingPaymentCount: 0,
    // Documentation stats
    avgNoteDelay: 0,
  });
  const [todaySchedule, setTodaySchedule] = useState([]);
  const [weekSchedule, setWeekSchedule] = useState([]);
  const [nextAppointment, setNextAppointment] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [subscriptionInfo, setSubscriptionInfo] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Get time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return { text: 'Good morning', icon: SunMedium };
    if (hour < 17) return { text: 'Good afternoon', icon: Sunset };
    return { text: 'Good evening', icon: Moon };
  };

  const greeting = getGreeting();
  const GreetingIcon = greeting.icon;

  const fetchDashboardData = async () => {
    try {
      const [
        clientsRes, 
        apptsRes, 
        messagesRes, 
        subscriptionRes,
        notesRes,
        paymentsRes,
        newRegsRes
      ] = await Promise.all([
        axios.get(`${API}/clients`),
        axios.get(`${API}/appointments`),
        axios.get(`${API}/messages`).catch(() => ({ data: [] })),
        axios.get(`${API}/auth/subscription-status`),
        axios.get(`${API}/session-notes`).catch(() => ({ data: [] })),
        axios.get(`${API}/payments`).catch(() => ({ data: [] })),
        axios.get(`${API}/clients/new-registrations`).catch(() => ({ data: [] })),
      ]);

      const today = nowIST();
      today.setHours(0, 0, 0, 0);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const now = nowIST();

      // Calculate week range
      const weekStart = new Date(today);
      weekStart.setDate(weekStart.getDate() - weekStart.getDay()); // Start of week (Sunday)
      const weekEnd = new Date(today);
      weekEnd.setDate(weekEnd.getDate() + 7);

      const allAppts = apptsRes.data;
      
      // Today's appointments
      const todayAppts = allAppts.filter((appt) => {
        const apptDate = toIST(appt.start_time);
        return apptDate >= today && apptDate < tomorrow && appt.status !== 'cancelled';
      }).sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

      // This week's appointments (for stats)
      const thisWeekAppts = allAppts.filter((appt) => {
        const apptDate = toIST(appt.start_time);
        return apptDate >= weekStart && apptDate < weekEnd;
      });

      // Week stats
      const weekSessions = thisWeekAppts.length;
      const weekCompleted = thisWeekAppts.filter(a => a.status === 'completed').length;
      const weekCancelled = thisWeekAppts.filter(a => a.status === 'cancelled').length;
      const weekNoShows = thisWeekAppts.filter(a => a.status === 'no_show').length;

      // Week's appointments (grouped by day) - for display
      const weekAppts = allAppts.filter((appt) => {
        const apptDate = toIST(appt.start_time);
        return apptDate >= today && apptDate < weekEnd && appt.status !== 'cancelled';
      }).sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

      // Group by day for week view
      const weekGrouped = weekAppts.reduce((acc, appt) => {
        const dateKey = toIST(appt.start_time).toDateString();
        if (!acc[dateKey]) acc[dateKey] = [];
        acc[dateKey].push(appt);
        return acc;
      }, {});

      const completedToday = todayAppts.filter(a => a.status === 'completed').length;

      // Find next upcoming appointment
      const upcomingAppts = allAppts
        .filter(a => toIST(a.start_time) > now && a.status === 'scheduled')
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
      
      // Count unread messages
      const unreadCount = messagesRes.data.filter(m => !m.read && m.recipient_id === user?.id).length;

      // Count pending notes (completed sessions without notes)
      const completedWithoutNotes = allAppts.filter(a => {
        if (a.status !== 'completed') return false;
        const hasNote = notesRes.data.some(n => n.appointment_id === a.id);
        return !hasNote;
      }).length;

      // Calculate avg note delay (days between session and note creation)
      let totalDelay = 0;
      let notesWithDelay = 0;
      notesRes.data.forEach(note => {
        if (note.appointment_id) {
          const appt = allAppts.find(a => a.id === note.appointment_id);
          if (appt) {
            const apptDate = new Date(appt.start_time);
            const noteDate = new Date(note.created_at);
            const delayDays = Math.floor((noteDate - apptDate) / (1000 * 60 * 60 * 24));
            if (delayDays >= 0) {
              totalDelay += delayDays;
              notesWithDelay++;
            }
          }
        }
      });
      const avgNoteDelay = notesWithDelay > 0 ? Math.round(totalDelay / notesWithDelay) : 0;

      // Payment stats
      const payments = paymentsRes.data || [];
      const pendingPayments = payments.filter(p => p.payment_status === 'pending');
      const receivedPayments = payments.filter(p => p.payment_status === 'paid' || p.payment_status === 'completed');
      const paymentsReceived = receivedPayments.reduce((sum, p) => sum + (p.amount || 0), 0);
      const paymentsPending = pendingPayments.reduce((sum, p) => sum + (p.amount || 0), 0);

      // Generate alerts
      const alertsList = [];
      
      // Inactive clients alert
      const thirtyDaysAgo = nowIST();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      
      const recentApptsMap = {};
      allAppts.forEach(appt => {
        if (appt.status === 'completed' && new Date(appt.start_time) > thirtyDaysAgo) {
          recentApptsMap[appt.client_id] = true;
        }
      });
      
      const inactiveClients = clientsRes.data.filter(c => !recentApptsMap[c.id]).length;
      const inactiveClientIds = clientsRes.data.filter(c => !recentApptsMap[c.id]).map(c => c.id);
      if (inactiveClients > 0) {
        alertsList.push({
          type: 'info',
          message: `${inactiveClients} client(s) inactive for 30+ days`,
          action: 'View Clients',
          actionNav: 'clients',
          actionContext: { filter: 'inactive', inactiveClientIds },
          icon: Users
        });
      }

      // New client registrations alert
      const newRegistrations = newRegsRes.data || [];
      if (newRegistrations.length > 0) {
        alertsList.unshift({
          type: 'success',
          message: `${newRegistrations.length} new client(s) registered!`,
          action: 'View Clients',
          actionNav: 'clients',
          icon: UserPlus,
          isNewRegistration: true,
          newClients: newRegistrations
        });
      }

      if (completedWithoutNotes > 0) {
        alertsList.push({
          type: 'warning',
          message: `${completedWithoutNotes} session(s) need notes`,
          action: 'Add Notes',
          actionNav: 'notes',
          icon: FileText
        });
      }

      if (subscriptionRes.data.subscription_status === 'trial') {
        alertsList.push({
          type: 'info',
          message: 'You are on a free trial',
          icon: Sparkles
        });
      }

      // Always add subscription info card
      const subData = subscriptionRes.data;
      if (subData) {
        const daysRemaining = subData.days_remaining || 0;
        const planName = subData.plan_name || 'Free Trial';
        const status = subData.subscription_status || 'trial';
        
        let subMessage = '';
        let subType = 'info';
        
        if (status === 'trial') {
          subMessage = `📦 Plan: Free Trial • ${daysRemaining} days remaining`;
          subType = 'info';
        } else if (status === 'active') {
          subMessage = `📦 Plan: ${planName} • ${daysRemaining} days remaining`;
          subType = daysRemaining <= 7 ? 'warning' : 'success';
        } else if (status === 'expired') {
          subMessage = `📦 Plan: ${planName} • Expired`;
          subType = 'error';
        }
        
        if (subMessage) {
          alertsList.push({
            type: subType,
            message: subMessage,
            action: 'Manage Subscription',
            actionNav: 'subscription',
            icon: CreditCard,
            isSubscription: true
          });
        }
      }

      setStats({
        todayAppointments: todayAppts.length,
        unreadMessages: unreadCount,
        totalClients: clientsRes.data.length,
        upcomingAppointments: upcomingAppts.length,
        completedToday,
        pendingNotes: completedWithoutNotes,
        weekSessions,
        weekCompleted,
        weekCancelled,
        weekNoShows,
        paymentsReceived,
        paymentsPending,
        pendingPaymentCount: pendingPayments.length,
        avgNoteDelay,
      });

      setTodaySchedule(todayAppts);
      setWeekSchedule(Object.entries(weekGrouped));
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

  const handleNavigate = (view, context = {}) => {
    if (onNavigate) onNavigate(view, context);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground text-base">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="therapist-dashboard" className="space-y-6 lg:space-y-8">
      {/* Personal Greeting Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <GreetingIcon size={20} />
            <span className="text-base">{greeting.text}</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-4xl font-serif text-foreground">
            {user?.full_name || 'Doctor'}
          </h1>
          <p className="text-base text-muted-foreground mt-1">{formatDateLong(nowIST())}</p>
        </div>
        
        {!isReadOnly && (
          <div className="flex gap-2">
            <Button 
              onClick={() => handleNavigate('schedule')}
              variant="outline"
              className="gap-2 flex-1 sm:flex-none h-11"
              data-testid="header-schedule-btn"
            >
              <CalendarPlus size={18} />
              <span>Schedule</span>
            </Button>
            <Button 
              onClick={() => handleNavigate('clients')}
              className="gap-2 flex-1 sm:flex-none h-11"
              data-testid="header-add-client-btn"
            >
              <Plus size={18} />
              <span>New Client</span>
            </Button>
          </div>
        )}
      </div>

      {/* Insight Cards - Soft Clinical Colors */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Sessions Today - Soft Teal */}
        <Card 
          className="p-4 bg-teal-50 border-teal-200 cursor-pointer hover:shadow-md hover:bg-teal-100/70 transition-all active:scale-[0.98]"
          onClick={() => handleNavigate('schedule')}
          data-testid="today-sessions-card"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-teal-100 rounded-lg">
              <Calendar size={20} className="text-teal-600" />
            </div>
            <ChevronRight size={16} className="text-teal-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-teal-700">{stats.todayAppointments}</p>
          <p className="text-sm text-teal-600 font-medium">Sessions Today</p>
          {stats.todayAppointments > 0 && (
            <p className="text-xs text-teal-500 mt-1">
              {stats.completedToday} completed
            </p>
          )}
        </Card>

        {/* Unread Messages - Soft Blue */}
        <Card 
          className={`p-4 cursor-pointer hover:shadow-md transition-all active:scale-[0.98] ${
            stats.unreadMessages > 0 
              ? 'bg-blue-50 border-blue-200 hover:bg-blue-100/70' 
              : 'bg-slate-50 border-slate-200 hover:bg-slate-100/70'
          }`}
          onClick={() => handleNavigate('messages')}
          data-testid="messages-card"
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`p-2 rounded-lg ${stats.unreadMessages > 0 ? 'bg-blue-100' : 'bg-slate-100'}`}>
              <MessageSquare size={20} className={stats.unreadMessages > 0 ? 'text-blue-600' : 'text-slate-500'} />
            </div>
            <ChevronRight size={16} className={stats.unreadMessages > 0 ? 'text-blue-400' : 'text-slate-400'} />
          </div>
          <p className={`text-2xl sm:text-3xl font-bold ${stats.unreadMessages > 0 ? 'text-blue-700' : 'text-slate-600'}`}>
            {stats.unreadMessages}
          </p>
          <p className={`text-sm font-medium ${stats.unreadMessages > 0 ? 'text-blue-600' : 'text-slate-500'}`}>
            Unread Messages
          </p>
          {stats.unreadMessages === 0 && (
            <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
              <CheckCircle size={12} /> All caught up
            </p>
          )}
        </Card>

        {/* Pending Notes - Soft Amber */}
        <Card 
          className={`p-4 cursor-pointer hover:shadow-md transition-all active:scale-[0.98] ${
            stats.pendingNotes > 0 
              ? 'bg-amber-50 border-amber-200 hover:bg-amber-100/70' 
              : 'bg-slate-50 border-slate-200 hover:bg-slate-100/70'
          }`}
          onClick={() => handleNavigate('notes')}
          data-testid="pending-notes-card"
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`p-2 rounded-lg ${stats.pendingNotes > 0 ? 'bg-amber-100' : 'bg-slate-100'}`}>
              <FileText size={20} className={stats.pendingNotes > 0 ? 'text-amber-600' : 'text-slate-500'} />
            </div>
            <ChevronRight size={16} className={stats.pendingNotes > 0 ? 'text-amber-400' : 'text-slate-400'} />
          </div>
          <p className={`text-2xl sm:text-3xl font-bold ${stats.pendingNotes > 0 ? 'text-amber-700' : 'text-slate-600'}`}>
            {stats.pendingNotes}
          </p>
          <p className={`text-sm font-medium ${stats.pendingNotes > 0 ? 'text-amber-600' : 'text-slate-500'}`}>
            Pending Notes
          </p>
          {stats.pendingNotes === 0 && (
            <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
              <CheckCircle size={12} /> All documented
            </p>
          )}
        </Card>

        {/* Payments Pending - Soft Rose */}
        <Card 
          className={`p-4 cursor-pointer hover:shadow-md transition-all active:scale-[0.98] ${
            stats.pendingPaymentCount > 0 
              ? 'bg-rose-50 border-rose-200 hover:bg-rose-100/70' 
              : 'bg-slate-50 border-slate-200 hover:bg-slate-100/70'
          }`}
          onClick={() => handleNavigate('payments')}
          data-testid="payments-pending-card"
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`p-2 rounded-lg ${stats.pendingPaymentCount > 0 ? 'bg-rose-100' : 'bg-slate-100'}`}>
              <DollarSign size={20} className={stats.pendingPaymentCount > 0 ? 'text-rose-600' : 'text-slate-500'} />
            </div>
            <ChevronRight size={16} className={stats.pendingPaymentCount > 0 ? 'text-rose-400' : 'text-slate-400'} />
          </div>
          <p className={`text-2xl sm:text-3xl font-bold ${stats.pendingPaymentCount > 0 ? 'text-rose-700' : 'text-slate-600'}`}>
            {stats.pendingPaymentCount}
          </p>
          <p className={`text-sm font-medium ${stats.pendingPaymentCount > 0 ? 'text-rose-600' : 'text-slate-500'}`}>
            Payments Pending
          </p>
          {stats.paymentsPending > 0 && (
            <p className="text-xs text-rose-500 mt-1">
              {formatCurrency(stats.paymentsPending)}
            </p>
          )}
        </Card>
      </div>

      {/* NEEDS ATTENTION - Priority Alerts Section (Moved to Top) */}
      {alerts.length > 0 && (
        <Card className="p-5 bg-gradient-to-r from-amber-50/80 to-orange-50/80 border-amber-300 border-2 shadow-md" data-testid="needs-attention-section">
          <h3 className="text-lg font-bold text-amber-800 mb-4 flex items-center gap-2">
            <div className="p-1.5 bg-amber-200 rounded-lg">
              <Bell size={18} className="text-amber-600" />
            </div>
            Needs Attention
            <span className="ml-2 px-2.5 py-1 bg-amber-500 text-white text-xs font-bold rounded-full">{alerts.length}</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {alerts.map((alert, idx) => {
              const Icon = alert.icon;
              // Different bright colors for each alert type
              const colorConfig = alert.isNewRegistration 
                ? { bg: 'bg-gradient-to-br from-emerald-200 to-teal-200', border: 'border-emerald-500', iconBg: 'bg-emerald-400', iconColor: 'text-white', textColor: 'text-emerald-900', linkColor: 'text-emerald-700 hover:text-emerald-900' }
                : alert.type === 'warning' 
                  ? { bg: 'bg-gradient-to-br from-amber-200 to-yellow-200', border: 'border-amber-500', iconBg: 'bg-amber-400', iconColor: 'text-white', textColor: 'text-amber-900', linkColor: 'text-amber-700 hover:text-amber-900' }
                  : alert.type === 'error'
                    ? { bg: 'bg-gradient-to-br from-red-200 to-rose-200', border: 'border-red-500', iconBg: 'bg-red-400', iconColor: 'text-white', textColor: 'text-red-900', linkColor: 'text-red-700 hover:text-red-900' }
                    : alert.type === 'info'
                      ? { bg: 'bg-gradient-to-br from-sky-200 to-blue-200', border: 'border-sky-500', iconBg: 'bg-sky-400', iconColor: 'text-white', textColor: 'text-sky-900', linkColor: 'text-sky-700 hover:text-sky-900' }
                      : { bg: 'bg-gradient-to-br from-violet-200 to-purple-200', border: 'border-violet-500', iconBg: 'bg-violet-400', iconColor: 'text-white', textColor: 'text-violet-900', linkColor: 'text-violet-700 hover:text-violet-900' };
              
              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border-2 flex items-start gap-3 shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all cursor-pointer ${colorConfig.bg} ${colorConfig.border}`}
                  onClick={() => !isReadOnly && handleNavigate(alert.actionNav, alert.actionContext || {})}
                  data-testid={`alert-${idx}`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${colorConfig.iconBg}`}>
                    <Icon size={20} className={colorConfig.iconColor} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold ${colorConfig.textColor}`}>{alert.message}</p>
                    {alert.action && !isReadOnly && (
                      <p className={`text-xs mt-1 font-medium flex items-center gap-1 ${colorConfig.linkColor}`}>
                        {alert.action} <ArrowRight size={12} />
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Lightweight Reporting Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* This Week at a Glance */}
        <Card 
          className="p-5 bg-white border cursor-pointer hover:shadow-md transition-all"
          onClick={() => handleNavigate('schedule')}
          data-testid="week-glance-card"
        >
          <div className="flex items-center gap-2 mb-4">
            <CalendarDays size={18} className="text-primary" />
            <h3 className="font-semibold text-foreground">This Week at a Glance</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Total Sessions</span>
              <span className="font-semibold text-foreground">{stats.weekSessions}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <CheckCircle size={14} className="text-green-500" /> Completed
              </span>
              <span className="font-semibold text-green-600">{stats.weekCompleted}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <XCircle size={14} className="text-red-400" /> Cancelled
              </span>
              <span className="font-semibold text-red-500">{stats.weekCancelled}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <UserX size={14} className="text-amber-500" /> No-shows
              </span>
              <span className="font-semibold text-amber-600">{stats.weekNoShows}</span>
            </div>
          </div>
        </Card>

        {/* Documentation Health */}
        <Card 
          className="p-5 bg-white border cursor-pointer hover:shadow-md transition-all"
          onClick={() => handleNavigate('notes')}
          data-testid="doc-health-card"
        >
          <div className="flex items-center gap-2 mb-4">
            <FileWarning size={18} className="text-amber-500" />
            <h3 className="font-semibold text-foreground">Documentation Health</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Pending Notes</span>
              <span className={`font-semibold ${stats.pendingNotes > 0 ? 'text-amber-600' : 'text-green-600'}`}>
                {stats.pendingNotes}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Avg. Note Delay</span>
              <span className={`font-semibold ${stats.avgNoteDelay > 2 ? 'text-amber-600' : 'text-green-600'}`}>
                {stats.avgNoteDelay === 0 ? 'Same day' : `${stats.avgNoteDelay} day${stats.avgNoteDelay > 1 ? 's' : ''}`}
              </span>
            </div>
            <div className="pt-2 mt-2 border-t">
              {stats.pendingNotes === 0 ? (
                <p className="text-sm text-green-600 flex items-center gap-1">
                  <CheckCircle size={14} /> Great job! All notes up to date
                </p>
              ) : (
                <p className="text-sm text-amber-600">
                  {stats.pendingNotes} session{stats.pendingNotes > 1 ? 's' : ''} need documentation
                </p>
              )}
            </div>
          </div>
        </Card>

        {/* Revenue Snapshot */}
        <Card 
          className="p-5 bg-white border cursor-pointer hover:shadow-md transition-all"
          onClick={() => handleNavigate('payments')}
          data-testid="revenue-snapshot-card"
        >
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} className="text-green-500" />
            <h3 className="font-semibold text-foreground">Revenue Snapshot</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Received</span>
              <span className="font-semibold text-green-600">{formatCurrency(stats.paymentsReceived)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Pending</span>
              <span className={`font-semibold ${stats.paymentsPending > 0 ? 'text-rose-600' : 'text-slate-500'}`}>
                {formatCurrency(stats.paymentsPending)}
              </span>
            </div>
            <div className="pt-2 mt-2 border-t">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Total</span>
                <span className="font-bold text-foreground">
                  {formatCurrency(stats.paymentsReceived + stats.paymentsPending)}
                </span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content Grid - Calendar Centric */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:gap-6">
        {/* Left Column - Today's Schedule (High Priority) */}
        <div className="lg:col-span-2 space-y-5 lg:space-y-6">
          {/* Today's Schedule - Primary Focus */}
          <Card className="overflow-hidden border-2 border-primary/20">
            <div className="bg-gradient-to-r from-primary/10 to-primary/5 px-5 py-4 border-b border-primary/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <CalendarDays size={22} className="text-primary" />
                  </div>
                  <div>
                    <h2 className="text-lg sm:text-xl font-semibold text-foreground">Today's Schedule</h2>
                    <p className="text-sm text-muted-foreground">
                      {stats.todayAppointments} session{stats.todayAppointments !== 1 ? 's' : ''} scheduled
                    </p>
                  </div>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => handleNavigate('schedule')}
                  className="text-primary text-sm"
                >
                  View All <ChevronRight size={18} />
                </Button>
              </div>
            </div>
            
            <div className="p-4">
              {todaySchedule.length === 0 ? (
                <div className="text-center py-10">
                  <div className="w-16 h-16 mx-auto bg-muted/50 rounded-full flex items-center justify-center mb-4">
                    <Calendar size={28} className="text-muted-foreground" />
                  </div>
                  <p className="text-foreground font-medium text-lg mb-1">No sessions today</p>
                  <p className="text-base text-muted-foreground mb-5">Your schedule is clear</p>
                  {!isReadOnly && (
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                      <Button 
                        variant="outline" 
                        onClick={() => handleNavigate('schedule')}
                        className="h-11"
                      >
                        <CalendarPlus size={18} className="mr-2" />
                        Schedule Appointment
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => handleNavigate('availability')}
                        className="h-11"
                      >
                        <Clock size={18} className="mr-2" />
                        Set Availability
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  {todaySchedule.map((appt, idx) => {
                    const now = new Date();
                    const startTime = new Date(appt.start_time);
                    const endTime = new Date(appt.end_time);
                    const isPast = endTime < now;
                    const isNow = startTime <= now && endTime >= now;
                    const isNext = !isPast && !isNow && idx === todaySchedule.findIndex(a => new Date(a.end_time) >= now);
                    
                    return (
                      <div
                        key={appt.id}
                        className={`p-4 rounded-xl border-2 transition-all ${
                          appt.status === 'completed' 
                            ? 'bg-success/5 border-success/30' 
                            : appt.status === 'in_progress' || isNow
                              ? 'bg-primary/10 border-primary/40 ring-2 ring-primary/20' 
                              : isNext 
                                ? 'bg-primary/5 border-primary/30' 
                                : isPast 
                                  ? 'bg-muted/30 border-border/40 opacity-60' 
                                  : 'bg-surface border-border/60'
                        }`}
                        data-testid={`schedule-item-${appt.id}`}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3 min-w-0 flex-1">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-medium flex-shrink-0 ${
                              appt.status === 'completed' ? 'bg-success/20 text-success' : 
                              isNow ? 'bg-primary text-white' : 
                              'bg-primary/10 text-primary'
                            }`}>
                              {appt.client_name?.charAt(0) || 'C'}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="font-semibold text-foreground text-base sm:text-lg truncate">{appt.client_name}</p>
                              <p className="text-sm text-muted-foreground">
                                {formatTimeRange(appt.start_time, appt.end_time)}
                              </p>
                            </div>
                          </div>
                          <div className="flex-shrink-0">
                            {appt.status === 'completed' ? (
                              <span className="flex items-center gap-1.5 text-sm text-success bg-success/10 px-3 py-1.5 rounded-full">
                                <CheckCircle size={14} />
                                Done
                              </span>
                            ) : appt.status === 'in_progress' ? (
                              <span className="px-3 py-1.5 bg-primary text-white text-sm rounded-full font-medium animate-pulse">
                                In Session
                              </span>
                            ) : isNow ? (
                              <span className="px-3 py-1.5 bg-primary text-white text-sm rounded-full font-medium">
                                Starting
                              </span>
                            ) : isNext ? (
                              <span className="px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-full font-medium">
                                Up Next
                              </span>
                            ) : null}
                          </div>
                        </div>
                        {appt.notes && (
                          <p className="text-sm text-muted-foreground mt-3 pl-15 line-clamp-2">
                            {appt.notes}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </Card>

          {/* Week at a Glance */}
          <Card className="p-5 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
                <Calendar size={20} className="text-primary" />
                This Week
              </h3>
              <span className="text-sm text-muted-foreground">
                {stats.upcomingAppointments} upcoming
              </span>
            </div>
            
            {weekSchedule.length === 0 ? (
              <p className="text-center py-6 text-muted-foreground text-base">No appointments this week</p>
            ) : (
              <div className="space-y-3">
                {weekSchedule.slice(0, 5).map(([dateKey, appts]) => {
                  const date = new Date(dateKey);
                  const isToday = date.toDateString() === new Date().toDateString();
                  
                  return (
                    <div 
                      key={dateKey} 
                      className={`flex items-center justify-between p-3 rounded-lg ${isToday ? 'bg-primary/5 border border-primary/20' : 'bg-muted/30'}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-11 h-11 rounded-lg flex flex-col items-center justify-center text-center ${isToday ? 'bg-primary text-white' : 'bg-muted'}`}>
                          <span className="text-xs font-medium leading-none">{date.toLocaleDateString('en-US', { weekday: 'short' })}</span>
                          <span className="text-sm font-bold leading-none mt-0.5">{date.getDate()}</span>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-foreground">
                            {isToday ? 'Today' : date.toLocaleDateString('en-US', { weekday: 'long' })}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {appts.length} session{appts.length !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {appts.slice(0, 3).map((a, i) => (
                          <div 
                            key={i} 
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                              a.status === 'completed' ? 'bg-success/20 text-success' : 'bg-primary/10 text-primary'
                            }`}
                            title={a.client_name}
                          >
                            {a.client_name?.charAt(0)}
                          </div>
                        ))}
                        {appts.length > 3 && (
                          <span className="text-sm text-muted-foreground ml-1">+{appts.length - 3}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column - Next Session & Alerts */}
        <div className="space-y-5 lg:space-y-6">
          {/* Next Session Preparation */}
          {nextAppointment && (
            <Card className="overflow-hidden border-2 border-primary/20">
              <div className="bg-gradient-to-r from-primary to-primary/80 px-5 py-4 text-white">
                <div className="flex items-center gap-2 mb-1">
                  <ClipboardList size={18} />
                  <span className="text-sm font-medium opacity-90">Coming Up</span>
                </div>
                <p className="font-semibold text-xl truncate">{nextAppointment.client_name}</p>
                <p className="text-base opacity-90">{getTimeUntil(nextAppointment.start_time)}</p>
              </div>
              
              <div className="p-5 space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Date</span>
                  <span className="font-medium">{getRelativeDate(nextAppointment.start_time)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Time</span>
                  <span className="font-medium">
                    {formatTimeRange(nextAppointment.start_time, nextAppointment.end_time)}
                  </span>
                </div>
                
                {nextAppointment.notes && (
                  <div className="p-3 bg-muted/50 rounded-lg">
                    <p className="text-xs text-muted-foreground mb-1">Notes</p>
                    <p className="text-sm line-clamp-2">{nextAppointment.notes}</p>
                  </div>
                )}
                
                <Button 
                  variant="outline" 
                  className="w-full h-11"
                  onClick={() => handleNavigate('clients', { clientId: nextAppointment.client_id })}
                  data-testid="view-client-profile-btn"
                >
                  View Client Profile
                </Button>
              </div>
            </Card>
          )}

          {/* Practice Stats - Lower emphasis */}
          <Card className="p-5 bg-muted/30 border-dashed">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">Practice Overview</h3>
            <div className="space-y-3">
              <div 
                className="flex justify-between items-center cursor-pointer hover:text-primary transition-colors"
                onClick={() => handleNavigate('clients')}
              >
                <span className="text-sm text-muted-foreground">Total Clients</span>
                <span className="font-semibold text-lg text-foreground">{stats.totalClients}</span>
              </div>
              <div 
                className="flex justify-between items-center cursor-pointer hover:text-primary transition-colors"
                onClick={() => handleNavigate('schedule')}
              >
                <span className="text-sm text-muted-foreground">Upcoming Sessions</span>
                <span className="font-semibold text-lg text-foreground">{stats.upcomingAppointments}</span>
              </div>
            </div>
          </Card>

          {/* Client Registration Link */}
          {!isReadOnly && <ClientRegistrationLink />}
        </div>
      </div>
    </div>
  );
};

export default TherapistOverview;
