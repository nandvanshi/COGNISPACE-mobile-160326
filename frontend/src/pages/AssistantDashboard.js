import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { useSubscription } from '../contexts/SubscriptionContext';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { 
  LogOut, Users, CalendarDays, DollarSign, Home, AlertTriangle, 
  Sparkles, Phone, PhoneCall, Clock, CheckCircle2, 
  AlertCircle, UserX, Calendar, CreditCard, Banknote, Plus,
  RefreshCw, ArrowRight, HandCoins, Lock, Send, FileCheck,
  MessageSquare, PhoneOff, CalendarCheck, Sun, Coffee
} from 'lucide-react';
import ClientManagement from '../components/ClientManagement';
import ClientProfilePage from '../components/ClientProfilePage';
import TherapistSchedule from '../components/TherapistSchedule';
import Payments from '../components/Payments';
import NotificationBell from '../components/NotificationBell';
import { toast } from 'sonner';
import { formatDate, formatTime, formatCurrency } from '../utils/formatUtils';

// ============= TODAY FOCUS STRIP =============
const TodayFocusStrip = ({ pendingCalls, todaySessions, cashToCollect }) => {
  const scrollRef = useRef(null);
  
  const focusItems = [
    { 
      id: 'calls', 
      label: 'Pending Calls', 
      value: pendingCalls, 
      icon: Phone, 
      color: pendingCalls > 0 ? 'bg-orange-500' : 'bg-green-500',
      textColor: 'text-white'
    },
    { 
      id: 'sessions', 
      label: "Today's Sessions", 
      value: todaySessions, 
      icon: Calendar, 
      color: 'bg-blue-500',
      textColor: 'text-white'
    },
    { 
      id: 'cash', 
      label: 'Cash to Collect', 
      value: formatCurrency(cashToCollect), 
      icon: Banknote, 
      color: cashToCollect > 0 ? 'bg-amber-500' : 'bg-gray-400',
      textColor: 'text-white'
    },
  ];

  return (
    <div className="w-full" data-testid="today-focus-strip">
      {/* Mobile: Swipeable Cards */}
      <div 
        ref={scrollRef}
        className="lg:hidden flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-hide -mx-4 px-4"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {focusItems.map((item) => {
          const Icon = item.icon;
          return (
            <div 
              key={item.id}
              className={`${item.color} ${item.textColor} rounded-xl p-4 min-w-[140px] snap-center flex-shrink-0`}
              data-testid={`focus-${item.id}`}
            >
              <Icon size={20} className="mb-2 opacity-90" />
              <p className="text-2xl font-bold">{item.value}</p>
              <p className="text-xs opacity-90">{item.label}</p>
            </div>
          );
        })}
      </div>
      
      {/* Desktop: Horizontal Bar */}
      <div className="hidden lg:grid grid-cols-3 gap-4">
        {focusItems.map((item) => {
          const Icon = item.icon;
          return (
            <div 
              key={item.id}
              className={`${item.color} ${item.textColor} rounded-xl p-4 flex items-center gap-4`}
              data-testid={`focus-${item.id}-desktop`}
            >
              <div className="p-3 bg-white/20 rounded-lg">
                <Icon size={24} />
              </div>
              <div>
                <p className="text-2xl font-bold">{item.value}</p>
                <p className="text-sm opacity-90">{item.label}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ============= CALL REMINDER CARD (Enhanced) =============
const CallReminderCard = ({ appointment, onMarkCalled, onAddNote, isPending }) => {
  const [showNoteDialog, setShowNoteDialog] = useState(false);
  const [noteType, setNoteType] = useState('');
  const [customNote, setCustomNote] = useState('');
  
  const quickNotes = [
    { id: 'no_answer', label: 'No Answer', icon: PhoneOff },
    { id: 'rescheduled', label: 'Rescheduled', icon: CalendarCheck },
    { id: 'confirmed', label: 'Confirmed', icon: CheckCircle2 },
  ];
  
  const handleQuickNote = async (type) => {
    setNoteType(type);
    await onAddNote(appointment.id, type, customNote);
    setShowNoteDialog(false);
    setCustomNote('');
  };

  return (
    <>
      <div 
        className={`p-4 rounded-xl border-2 transition-all ${
          isPending 
            ? 'bg-orange-50 border-orange-200' 
            : 'bg-green-50 border-green-200 opacity-80'
        }`}
        data-testid={`call-reminder-${appointment.id}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              {isPending ? (
                <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
              ) : (
                <CheckCircle2 size={16} className="text-green-600" />
              )}
              <span className="font-semibold text-foreground">{appointment.client_name}</span>
            </div>
            <p className="text-sm text-muted-foreground">{formatTime(appointment.start_time)}</p>
            {appointment.call_note && (
              <p className="text-xs text-muted-foreground mt-1 italic">Note: {appointment.call_note}</p>
            )}
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            {/* Tap to Call - Mobile */}
            {appointment.client_mobile && (
              <a
                href={`tel:${appointment.client_mobile}`}
                className="lg:hidden inline-flex items-center justify-center gap-1 px-3 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium"
                data-testid={`tap-call-${appointment.id}`}
              >
                <PhoneCall size={16} />
                Call
              </a>
            )}
            
            {/* Quick Note Button */}
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowNoteDialog(true)}
              className="gap-1"
              data-testid={`quick-note-${appointment.id}`}
            >
              <MessageSquare size={14} />
              <span className="hidden sm:inline">Note</span>
            </Button>
            
            {/* Mark Called Button */}
            {isPending && (
              <Button
                size="sm"
                onClick={() => onMarkCalled(appointment.id)}
                className="gap-1 bg-green-600 hover:bg-green-700"
                data-testid={`mark-called-${appointment.id}`}
              >
                <CheckCircle2 size={14} />
                <span className="hidden sm:inline">Done</span>
              </Button>
            )}
          </div>
        </div>
      </div>
      
      {/* Quick Note Dialog */}
      <Dialog open={showNoteDialog} onOpenChange={setShowNoteDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Quick Note for {appointment.client_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="grid grid-cols-3 gap-2">
              {quickNotes.map((note) => {
                const Icon = note.icon;
                return (
                  <button
                    key={note.id}
                    onClick={() => handleQuickNote(note.id)}
                    className={`p-3 rounded-lg border-2 flex flex-col items-center gap-1 transition-all hover:border-primary ${
                      noteType === note.id ? 'border-primary bg-primary/10' : 'border-border'
                    }`}
                  >
                    <Icon size={20} className="text-muted-foreground" />
                    <span className="text-xs">{note.label}</span>
                  </button>
                );
              })}
            </div>
            <Textarea
              placeholder="Add custom note (optional)..."
              value={customNote}
              onChange={(e) => setCustomNote(e.target.value)}
              rows={2}
            />
            <Button 
              onClick={() => handleQuickNote('custom')} 
              className="w-full"
              disabled={!customNote && !noteType}
            >
              Save Note
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

// ============= CONTEXTUAL QUICK ACTIONS =============
const ContextualQuickActions = ({ onNavigate }) => {
  const currentHour = new Date().getHours();
  const isMorning = currentHour >= 6 && currentHour < 12;
  const isAfternoon = currentHour >= 12 && currentHour < 18;
  
  const morningActions = [
    { id: 'calls', label: 'Call List', icon: Phone, view: 'overview', color: 'bg-orange-100 text-orange-700 border-orange-200' },
    { id: 'schedule', label: "Today Schedule", icon: Calendar, view: 'schedule', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  ];
  
  const afternoonActions = [
    { id: 'payment', label: 'Record Payment', icon: DollarSign, view: 'payments', color: 'bg-green-100 text-green-700 border-green-200' },
    { id: 'settlement', label: 'Cash Settlement', icon: HandCoins, view: 'overview', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  ];
  
  const actions = isMorning ? morningActions : isAfternoon ? afternoonActions : [...morningActions, ...afternoonActions];
  const timeLabel = isMorning ? 'Morning Tasks' : isAfternoon ? 'Afternoon Tasks' : 'Quick Actions';
  const TimeIcon = isMorning ? Sun : Coffee;

  return (
    <div className="mb-6" data-testid="contextual-actions">
      <div className="flex items-center gap-2 mb-3">
        <TimeIcon size={18} className="text-primary" />
        <h3 className="text-sm font-medium text-muted-foreground">{timeLabel}</h3>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.id}
              onClick={() => onNavigate(action.view)}
              className={`p-4 rounded-xl border-2 flex items-center gap-3 transition-all hover:scale-[1.02] active:scale-[0.98] ${action.color}`}
              data-testid={`action-${action.id}`}
            >
              <Icon size={22} />
              <span className="font-medium text-sm">{action.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

// ============= ASSISTANT OVERVIEW COMPONENT (Redesigned) =============
const AssistantOverview = ({ onNavigate }) => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Cash Settlement state
  const [settlement, setSettlement] = useState(null);
  const [showHandoverDialog, setShowHandoverDialog] = useState(false);
  const [handoverNote, setHandoverNote] = useState('');
  const [submittingHandover, setSubmittingHandover] = useState(false);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/assistant/dashboard`);
      setDashboard(res.data);
    } catch (error) {
      toast.error('Failed to load dashboard');
      console.error(error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);
  
  const fetchSettlement = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/settlements/today`);
      setSettlement(res.data);
    } catch (error) {
      console.error('Failed to fetch settlement:', error);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    fetchSettlement();
    const interval = setInterval(() => {
      fetchDashboard();
      fetchSettlement();
    }, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchDashboard, fetchSettlement]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchDashboard();
    fetchSettlement();
  };
  
  const handleCashHandover = async () => {
    setSubmittingHandover(true);
    try {
      await axios.post(`${API}/settlements/handover`, { note: handoverNote || null });
      toast.success('Cash handover submitted successfully');
      setShowHandoverDialog(false);
      setHandoverNote('');
      fetchSettlement();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit handover');
    } finally {
      setSubmittingHandover(false);
    }
  };

  const handleMarkCalled = async (appointmentId) => {
    try {
      await axios.post(`${API}/assistant/call-reminder/${appointmentId}`, {
        status: 'called'
      });
      toast.success('Marked as called');
      fetchDashboard();
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const handleAddCallNote = async (appointmentId, noteType, customNote) => {
    try {
      await axios.post(`${API}/assistant/call-reminder/${appointmentId}`, {
        status: noteType === 'confirmed' ? 'called' : 'pending',
        notes: customNote || noteType
      });
      toast.success('Note saved');
      fetchDashboard();
    } catch (error) {
      toast.error('Failed to save note');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">Failed to load dashboard data</p>
        <Button onClick={fetchDashboard} className="mt-4">Retry</Button>
      </div>
    );
  }

  const { 
    therapist = {}, 
    today_date = new Date().toISOString().split('T')[0], 
    today_day = new Date().toLocaleDateString('en-IN', { weekday: 'long' }),
    todays_appointments = [], 
    inactive_clients = [],
    inactive_clients_count = 0,
    payments_summary = { payments: [], total_collected: 0, cash_total: 0, online_total: 0, total: 0 }
  } = dashboard || {};
  
  const safePaymentsSummary = {
    payments: payments_summary?.payments || [],
    cash_total: payments_summary?.cash_total || 0,
    online_total: payments_summary?.online_total || 0,
    total: payments_summary?.total || 0
  };
  
  const pendingCalls = (todays_appointments || []).filter(a => a?.call_status === 'pending');
  const completedCalls = (todays_appointments || []).filter(a => a?.call_status === 'called');
  const totalSessions = todays_appointments?.length || 0;

  return (
    <div className="space-y-6 pb-24 lg:pb-6" data-testid="assistant-overview">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-serif text-primary">{therapist.full_name}</h1>
          <p className="text-sm text-muted-foreground">{today_day}, {formatDate(today_date)}</p>
        </div>
        <Button 
          variant="ghost" 
          size="icon"
          onClick={handleRefresh}
          disabled={refreshing}
          className="rounded-full"
        >
          <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} />
        </Button>
      </div>

      {/* Today Focus Strip */}
      <TodayFocusStrip 
        pendingCalls={pendingCalls.length}
        todaySessions={totalSessions}
        cashToCollect={safePaymentsSummary.cash_total}
      />
      
      {/* Contextual Quick Actions */}
      <ContextualQuickActions onNavigate={onNavigate} />

      {/* TODAY'S CALL REMINDERS (Enhanced) */}
      <Card className="p-4 lg:p-5" data-testid="call-reminders-section">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Phone className="text-primary" size={20} />
            <h2 className="text-lg font-semibold">Call Reminders</h2>
          </div>
          <Badge 
            className={pendingCalls.length > 0 
              ? 'bg-orange-100 text-orange-700 border-orange-200' 
              : 'bg-green-100 text-green-700 border-green-200'
            }
          >
            {pendingCalls.length > 0 ? `${pendingCalls.length} pending` : 'All done'}
          </Badge>
        </div>

        {totalSessions === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Calendar size={40} className="mx-auto mb-2 opacity-50" />
            <p>No sessions scheduled for today</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Pending Calls First */}
            {pendingCalls.map((appt) => (
              <CallReminderCard 
                key={appt.id}
                appointment={appt}
                onMarkCalled={handleMarkCalled}
                onAddNote={handleAddCallNote}
                isPending={true}
              />
            ))}
            
            {/* Completed Calls */}
            {completedCalls.map((appt) => (
              <CallReminderCard 
                key={appt.id}
                appointment={appt}
                onMarkCalled={handleMarkCalled}
                onAddNote={handleAddCallNote}
                isPending={false}
              />
            ))}
          </div>
        )}
      </Card>

      {/* INACTIVE CLIENTS (Prominent Card) */}
      {(inactive_clients?.length > 0 || inactive_clients_count > 0) && (
        <Card className="p-4 lg:p-5 border-2 border-red-200 bg-red-50/50" data-testid="inactive-clients-section">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <UserX className="text-red-600" size={20} />
              <h2 className="text-lg font-semibold text-red-800">Inactive Clients</h2>
            </div>
            <Badge className="bg-red-100 text-red-700 border-red-200">
              {inactive_clients_count} clients (30+ days)
            </Badge>
          </div>

          <div className="space-y-3">
            {(inactive_clients || []).slice(0, 5).map((client) => (
              <div 
                key={client.id} 
                className="flex items-center justify-between p-3 bg-white rounded-lg border border-red-100"
                data-testid={`inactive-client-${client.id}`}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{client.full_name}</p>
                  <p className="text-sm text-red-600">
                    {client.days_inactive ? `${client.days_inactive} days inactive` : 'No sessions yet'}
                  </p>
                </div>
                <div className="flex gap-2 ml-2">
                  {client.mobile && (
                    <a
                      href={`tel:${client.mobile}`}
                      className="inline-flex items-center justify-center gap-1 px-3 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium"
                    >
                      <PhoneCall size={14} />
                      <span className="hidden sm:inline">Call</span>
                    </a>
                  )}
                  <Button 
                    size="sm" 
                    onClick={() => onNavigate('schedule')}
                    className="gap-1"
                  >
                    <Calendar size={14} />
                    <span className="hidden sm:inline">Schedule</span>
                  </Button>
                </div>
              </div>
            ))}

            {inactive_clients_count > 5 && (
              <Button 
                variant="ghost" 
                className="w-full text-red-700"
                onClick={() => onNavigate('clients')}
              >
                View all {inactive_clients_count} inactive clients
                <ArrowRight size={16} className="ml-2" />
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* TODAY'S PAYMENTS (Productivity View) */}
      <Card className="p-4 lg:p-5" data-testid="payments-summary-section">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CreditCard className="text-green-600" size={20} />
            <h2 className="text-lg font-semibold">Today Payments</h2>
          </div>
        </div>

        {/* Payment Summary Grid */}
        <div className="grid grid-cols-3 gap-2 lg:gap-3 mb-4">
          <div className="p-3 bg-green-50 rounded-xl text-center border border-green-100">
            <Banknote size={18} className="mx-auto text-green-600 mb-1" />
            <p className="text-xs text-green-700">Cash</p>
            <p className="font-bold text-green-800 text-lg">{formatCurrency(safePaymentsSummary.cash_total)}</p>
          </div>
          <div className="p-3 bg-blue-50 rounded-xl text-center border border-blue-100">
            <CreditCard size={18} className="mx-auto text-blue-600 mb-1" />
            <p className="text-xs text-blue-700">Online</p>
            <p className="font-bold text-blue-800 text-lg">{formatCurrency(safePaymentsSummary.online_total)}</p>
          </div>
          <div className="p-3 bg-primary/10 rounded-xl text-center border border-primary/20">
            <DollarSign size={18} className="mx-auto text-primary mb-1" />
            <p className="text-xs text-primary">Total</p>
            <p className="font-bold text-primary text-lg">{formatCurrency(safePaymentsSummary.total)}</p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <Button 
            onClick={() => onNavigate('payments')}
            className="gap-2"
            data-testid="record-payment-btn"
          >
            <Plus size={16} />
            Record Payment
          </Button>
          <Button 
            variant="outline"
            onClick={() => setShowHandoverDialog(true)}
            className="gap-2 border-amber-300 text-amber-700 hover:bg-amber-50"
            disabled={!settlement || settlement.cash_amount === 0}
            data-testid="cash-settlement-btn"
          >
            <HandCoins size={16} />
            Cash Settlement
          </Button>
        </div>

        {/* Settlement Status */}
        {settlement && settlement.status !== 'pending' && (
          <div className={`mt-4 p-3 rounded-lg flex items-center gap-3 ${
            settlement.status === 'handed_over' ? 'bg-blue-50 text-blue-700' :
            settlement.status === 'settled' ? 'bg-green-50 text-green-700' :
            settlement.status === 'disputed' ? 'bg-red-50 text-red-700' : ''
          }`}>
            {settlement.status === 'handed_over' && <Clock size={18} />}
            {settlement.status === 'settled' && <Lock size={18} />}
            {settlement.status === 'disputed' && <AlertTriangle size={18} />}
            <div className="flex-1">
              <p className="text-sm font-medium">
                {settlement.status === 'handed_over' && 'Awaiting therapist confirmation'}
                {settlement.status === 'settled' && 'Settlement complete'}
                {settlement.status === 'disputed' && 'Issue reported - contact therapist'}
              </p>
            </div>
          </div>
        )}
      </Card>

      {/* Cash Handover Dialog */}
      <Dialog open={showHandoverDialog} onOpenChange={setShowHandoverDialog}>
        <DialogContent className="max-w-md mx-4">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <HandCoins className="text-amber-600" size={22} />
              Cash Handover
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 pt-2">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
              <p className="text-sm text-amber-700 mb-1">Cash Amount</p>
              <p className="text-3xl font-bold text-amber-800">
                {settlement && formatCurrency(settlement.cash_amount)}
              </p>
            </div>

            <div>
              <Label htmlFor="handover-note">Note (Optional)</Label>
              <Textarea
                id="handover-note"
                placeholder="Any notes..."
                value={handoverNote}
                onChange={(e) => setHandoverNote(e.target.value)}
                className="mt-1"
                rows={2}
              />
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowHandoverDialog(false)}
                className="flex-1"
                disabled={submittingHandover}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCashHandover}
                className="flex-1 bg-amber-600 hover:bg-amber-700 gap-2"
                disabled={submittingHandover}
                data-testid="confirm-handover-btn"
              >
                {submittingHandover ? (
                  <RefreshCw size={16} className="animate-spin" />
                ) : (
                  <FileCheck size={16} />
                )}
                Confirm
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ============= BOTTOM NAVIGATION (Mobile Only) =============
const BottomNavigation = ({ currentView, onNavigate }) => {
  const navItems = [
    { id: 'overview', label: 'Home', icon: Home },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'schedule', label: 'Schedule', icon: CalendarDays },
    { id: 'payments', label: 'Payments', icon: DollarSign },
  ];

  return (
    <nav 
      className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-border z-50 safe-area-pb"
      data-testid="bottom-navigation"
    >
      <div className="grid grid-cols-4 h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex flex-col items-center justify-center gap-0.5 transition-colors ${
                isActive 
                  ? 'text-primary' 
                  : 'text-muted-foreground'
              }`}
              data-testid={`bottom-nav-${item.id}`}
            >
              <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-[10px] ${isActive ? 'font-semibold' : ''}`}>{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

// ============= MAIN ASSISTANT DASHBOARD =============
const AssistantDashboard = () => {
  const { user, logout } = useAuth();
  const { isReadOnly, refreshStatus } = useSubscription();
  const location = useLocation();
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('overview');
  
  // Check if we're on a client profile page
  const clientProfileMatch = location.pathname.match(/\/assistant\/clients\/([^/]+)/);
  const isClientProfilePage = !!clientProfileMatch;
  const clientIdFromUrl = clientProfileMatch ? clientProfileMatch[1] : null;

  useEffect(() => {
    refreshStatus();
  }, []);

  const navItems = [
    { id: 'overview', label: 'Home', icon: Home },
    { id: 'clients', label: 'Clients', icon: Users },
    { id: 'schedule', label: 'Schedule', icon: CalendarDays },
    { id: 'payments', label: 'Payments', icon: DollarSign },
  ];

  const handleLogout = () => {
    logout();
    window.location.href = '/login';
  };

  const handleNavigate = (view) => {
    if (isClientProfilePage) {
      navigate('/assistant');
    }
    setCurrentView(view);
  };

  // If on client profile page, render full-page client profile
  if (isClientProfilePage && clientIdFromUrl) {
    return <ClientProfilePage clientIdProp={clientIdFromUrl} isReadOnly={isReadOnly} isAssistant={true} />;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed inset-y-0 left-0 w-56 bg-white border-r border-border flex-col z-40">
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <img src="/logo-symbol.png" alt="COGNISPACE" className="h-8 w-auto" />
            <h1 className="text-lg font-serif text-primary">COGNISPACE</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-2 truncate">{user?.full_name}</p>
          <Badge className="mt-1 bg-info/10 text-info border-info/20 text-xs">Assistant</Badge>
        </div>

        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                data-testid={`nav-${item.id}`}
                onClick={() => handleNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
                  currentView === item.id
                    ? 'bg-primary text-white'
                    : 'text-foreground hover:bg-muted'
                }`}
              >
                <Icon size={18} />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="p-3 border-t border-border">
          <Button
            onClick={handleLogout}
            variant="ghost"
            size="sm"
            className="w-full justify-start text-sm"
            data-testid="logout-button"
          >
            <LogOut size={16} className="mr-2" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 bg-white border-b border-border z-40 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo-symbol.png" alt="COGNISPACE" className="h-8 w-auto" />
            <span className="font-serif text-lg text-primary">COGNISPACE</span>
          </div>
          <Button
            onClick={handleLogout}
            variant="ghost"
            size="icon"
            className="rounded-full"
            data-testid="mobile-logout"
          >
            <LogOut size={18} />
          </Button>
        </div>
      </header>

      {/* Read-Only Banner */}
      {isReadOnly && (
        <div 
          className="fixed top-14 lg:top-0 lg:left-56 right-0 bg-amber-500 text-white px-4 py-2 flex items-center gap-2 z-30"
          data-testid="subscription-expired-banner"
        >
          <AlertTriangle size={16} />
          <p className="text-sm font-medium">Subscription expired - Read-only mode</p>
        </div>
      )}

      {/* Main Content */}
      <main className={`lg:ml-56 pt-14 lg:pt-0 ${isReadOnly ? 'pt-24 lg:pt-10' : ''}`}>
        <div className="max-w-3xl mx-auto p-4 lg:p-6">
          {currentView === 'overview' && <AssistantOverview onNavigate={handleNavigate} />}
          {currentView === 'clients' && (
            <div className="pb-20 lg:pb-0">
              <ClientManagement isReadOnly={isReadOnly} isAssistant={true} />
            </div>
          )}
          {currentView === 'schedule' && (
            <div className="pb-20 lg:pb-0">
              <TherapistSchedule isReadOnly={isReadOnly} isAssistant={true} />
            </div>
          )}
          {currentView === 'payments' && (
            <div className="pb-20 lg:pb-0">
              <Payments isReadOnly={isReadOnly} />
            </div>
          )}
        </div>
      </main>

      {/* Bottom Navigation (Mobile Only) */}
      <BottomNavigation currentView={currentView} onNavigate={handleNavigate} />
    </div>
  );
};

export default AssistantDashboard;
