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
  DollarSign, TrendingUp, XCircle, UserX, FileWarning
} from 'lucide-react';
import { toast } from 'sonner';
import { formatTime, formatTimeRange, formatDateLong, getRelativeDate, getTimeUntil, toIST, nowIST, formatCurrency } from '../utils/formatUtils';

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
        paymentsRes
      ] = await Promise.all([
        axios.get(`${API}/clients`),
        axios.get(`${API}/appointments`),
        axios.get(`${API}/messages`).catch(() => ({ data: [] })),
        axios.get(`${API}/auth/subscription-status`),
        axios.get(`${API}/session-notes`).catch(() => ({ data: [] })),
        axios.get(`${API}/payments`).catch(() => ({ data: [] })),
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
            {user?.full_name?.split(' ')[0] || 'Doctor'}
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

      {/* Today at a Glance - Actionable Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Today's Sessions Card */}
        <Card 
          className={`p-5 border-l-4 ${stats.todayAppointments > 0 ? 'border-l-primary bg-primary/5' : 'border-l-muted bg-muted/30'} cursor-pointer hover:shadow-md transition-all active:scale-[0.98]`}
          onClick={() => handleNavigate('schedule')}
          data-testid="today-sessions-card"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-3xl sm:text-4xl font-bold text-foreground">{stats.todayAppointments}</p>
              <p className="text-sm sm:text-base text-muted-foreground font-medium mt-1">Sessions Today</p>
              {stats.todayAppointments > 0 ? (
                <p className="text-sm text-primary mt-2 font-medium">
                  {stats.completedToday} done, {stats.todayAppointments - stats.completedToday} left
                </p>
              ) : (
                <p className="text-sm text-muted-foreground mt-2">
                  No sessions scheduled
                </p>
              )}
            </div>
            <div className={`p-3 rounded-full flex-shrink-0 ${stats.todayAppointments > 0 ? 'bg-primary/10' : 'bg-muted'}`}>
              <Calendar size={24} className={stats.todayAppointments > 0 ? 'text-primary' : 'text-muted-foreground'} />
            </div>
          </div>
        </Card>

        {/* Messages Card */}
        <Card 
          className={`p-5 border-l-4 ${stats.unreadMessages > 0 ? 'border-l-blue-500 bg-blue-50' : 'border-l-muted bg-muted/30'} cursor-pointer hover:shadow-md transition-all active:scale-[0.98]`}
          onClick={() => handleNavigate('messages')}
          data-testid="messages-card"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-3xl sm:text-4xl font-bold text-foreground">{stats.unreadMessages}</p>
              <p className="text-sm sm:text-base text-muted-foreground font-medium mt-1">Unread Messages</p>
              {stats.unreadMessages > 0 ? (
                <p className="text-sm text-blue-600 mt-2 font-medium">
                  Needs attention
                </p>
              ) : (
                <p className="text-sm text-success mt-2 flex items-center gap-1">
                  <CheckCircle size={14} /> All caught up
                </p>
              )}
            </div>
            <div className={`p-3 rounded-full flex-shrink-0 ${stats.unreadMessages > 0 ? 'bg-blue-100' : 'bg-muted'}`}>
              <MessageSquare size={24} className={stats.unreadMessages > 0 ? 'text-blue-500' : 'text-muted-foreground'} />
            </div>
          </div>
        </Card>

        {/* Pending Notes Card */}
        <Card 
          className={`p-5 border-l-4 ${stats.pendingNotes > 0 ? 'border-l-amber-500 bg-amber-50' : 'border-l-muted bg-muted/30'} cursor-pointer hover:shadow-md transition-all active:scale-[0.98]`}
          onClick={() => handleNavigate('notes')}
          data-testid="pending-notes-card"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-3xl sm:text-4xl font-bold text-foreground">{stats.pendingNotes}</p>
              <p className="text-sm sm:text-base text-muted-foreground font-medium mt-1">Pending Notes</p>
              {stats.pendingNotes > 0 ? (
                <p className="text-sm text-amber-600 mt-2 font-medium">
                  Need documentation
                </p>
              ) : (
                <p className="text-sm text-success mt-2 flex items-center gap-1">
                  <CheckCircle size={14} /> All documented
                </p>
              )}
            </div>
            <div className={`p-3 rounded-full flex-shrink-0 ${stats.pendingNotes > 0 ? 'bg-amber-100' : 'bg-muted'}`}>
              <FileText size={24} className={stats.pendingNotes > 0 ? 'text-amber-500' : 'text-muted-foreground'} />
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

          {/* Alerts & Tasks */}
          <Card className="p-5">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <Bell size={18} className="text-amber-500" />
              Needs Attention
            </h3>
            
            {alerts.length === 0 ? (
              <div className="text-center py-6">
                <div className="w-14 h-14 mx-auto bg-success/10 rounded-full flex items-center justify-center mb-3">
                  <CheckCircle size={24} className="text-success" />
                </div>
                <p className="text-base font-medium text-foreground">All caught up!</p>
                <p className="text-sm text-muted-foreground mt-1">No pending tasks</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((alert, idx) => {
                  const Icon = alert.icon;
                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-lg border flex items-start gap-3 ${
                        alert.type === 'warning' 
                          ? 'bg-amber-50 border-amber-200' 
                          : alert.type === 'error'
                            ? 'bg-red-50 border-red-200'
                            : 'bg-blue-50 border-blue-200'
                      }`}
                      data-testid={`alert-${idx}`}
                    >
                      <Icon size={18} className={`flex-shrink-0 mt-0.5 ${
                        alert.type === 'warning' ? 'text-amber-500' : 
                        alert.type === 'error' ? 'text-red-500' : 'text-blue-500'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-foreground">{alert.message}</p>
                        {alert.action && !isReadOnly && (
                          <Button 
                            variant="link" 
                            size="sm" 
                            className="p-0 h-auto text-sm mt-1"
                            onClick={() => handleNavigate(alert.actionNav, alert.actionContext || {})}
                            data-testid={`alert-action-${idx}`}
                          >
                            {alert.action} <ArrowRight size={14} className="ml-1" />
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

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
        </div>
      </div>
    </div>
  );
};

export default TherapistOverview;
