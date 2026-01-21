import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { useSubscription } from '../contexts/SubscriptionContext';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { 
  LogOut, Users, CalendarDays, DollarSign, Home, AlertTriangle, 
  Sparkles, Menu, X, Phone, PhoneCall, Clock, CheckCircle2, 
  AlertCircle, UserX, Calendar, CreditCard, Banknote, Plus,
  ChevronDown, ChevronUp, RefreshCw, ArrowRight, HandCoins, 
  Lock, Send, FileCheck
} from 'lucide-react';
import ClientManagement from '../components/ClientManagement';
import ClientProfilePage from '../components/ClientProfilePage';
import TherapistSchedule from '../components/TherapistSchedule';
import Payments from '../components/Payments';
import { toast } from 'sonner';
import { formatDate, formatTime, formatCurrency } from '../utils/formatUtils';

// ============= ASSISTANT OVERVIEW COMPONENT =============
const AssistantOverview = ({ onNavigate }) => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAccessInfo, setShowAccessInfo] = useState(false);
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
    // Refresh every 5 minutes
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
      await axios.post(`${API}/assistant/call-reminder/${appointmentId}`);
      toast.success('Marked as called');
      fetchDashboard();
    } catch (error) {
      toast.error('Failed to update');
    }
  };

  const handleUnmarkCalled = async (appointmentId) => {
    try {
      await axios.delete(`${API}/assistant/call-reminder/${appointmentId}`);
      toast.success('Call reminder reset');
      fetchDashboard();
    } catch (error) {
      toast.error('Failed to update');
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

  // Destructure with defaults to handle missing fields - DEFENSIVE CODING
  const { 
    therapist = {}, 
    today_date = new Date().toISOString().split('T')[0], 
    today_day = new Date().toLocaleDateString('en-IN', { weekday: 'long' }),
    todays_appointments = [], 
    needs_attention = { upcoming_sessions: [], pending_checkins: [], pending_payments_count: 0 }, 
    inactive_clients = [],
    inactive_clients_count = 0,
    payments_summary = { payments: [], total_collected: 0, cash_total: 0, online_total: 0, total: 0 }
  } = dashboard || {};
  
  // Safe access for needs_attention nested properties
  const safeNeedsAttention = {
    upcoming_sessions: needs_attention?.upcoming_sessions || [],
    pending_checkins: needs_attention?.pending_checkins || [],
    pending_payments_count: needs_attention?.pending_payments_count || 0
  };
  
  // Safe access for payments_summary nested properties
  const safePaymentsSummary = {
    payments: payments_summary?.payments || [],
    cash_total: payments_summary?.cash_total || 0,
    online_total: payments_summary?.online_total || 0,
    total: payments_summary?.total || 0
  };
  
  const pendingCalls = (todays_appointments || []).filter(a => a?.call_status === 'pending');
  const completedCalls = (todays_appointments || []).filter(a => a?.call_status === 'called');

  return (
    <div className="space-y-6" data-testid="assistant-overview">
      {/* Header with Therapist Name */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-serif text-primary">{therapist.full_name}</h1>
          <p className="text-muted-foreground mt-1">{today_day}, {today_date}</p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleRefresh}
          disabled={refreshing}
          className="self-start sm:self-auto"
        >
          <RefreshCw size={16} className={`mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-3 gap-3">
        <Button 
          variant="outline" 
          className="h-auto py-4 flex-col gap-2"
          onClick={() => onNavigate('clients')}
          data-testid="quick-add-client"
        >
          <Plus size={20} className="text-primary" />
          <span className="text-sm">Add Client</span>
        </Button>
        <Button 
          variant="outline" 
          className="h-auto py-4 flex-col gap-2"
          onClick={() => onNavigate('schedule')}
          data-testid="quick-schedule"
        >
          <Calendar size={20} className="text-primary" />
          <span className="text-sm">Today's Schedule</span>
        </Button>
        <Button 
          variant="outline" 
          className="h-auto py-4 flex-col gap-2"
          onClick={() => onNavigate('payments')}
          data-testid="quick-payment"
        >
          <DollarSign size={20} className="text-primary" />
          <span className="text-sm">Record Payment</span>
        </Button>
      </div>

      {/* 1. TODAY'S CALL REMINDERS */}
      <Card className="p-5 bg-white/70 backdrop-blur-xl border border-border/40" data-testid="call-reminders-section">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Phone className="text-primary" size={20} />
            <h2 className="text-lg font-semibold">Today's Call Reminders</h2>
          </div>
          <Badge variant={pendingCalls.length > 0 ? "destructive" : "outline"}>
            {pendingCalls.length} pending
          </Badge>
        </div>

        {(todays_appointments?.length || 0) === 0 ? (
          <p className="text-muted-foreground text-center py-6">No sessions scheduled for today</p>
        ) : (
          <div className="space-y-2">
            {/* Pending Calls First */}
            {pendingCalls.map((appt) => (
              <div 
                key={appt?.id || Math.random()} 
                className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg"
                data-testid={`call-reminder-${appt?.id}`}
              >
                <div className="flex items-center gap-3">
                  <Phone size={18} className="text-amber-600" />
                  <div>
                    <p className="font-medium">{appt?.client_name || 'Unknown Client'}</p>
                    <p className="text-sm text-muted-foreground">{formatTime(appt?.start_time)}</p>
                  </div>
                </div>
                <Button 
                  size="sm" 
                  onClick={() => handleMarkCalled(appt?.id)}
                  className="gap-1"
                  data-testid={`mark-called-${appt?.id}`}
                >
                  <CheckCircle2 size={14} />
                  Mark Called
                </Button>
              </div>
            ))}

            {/* Completed Calls */}
            {completedCalls.map((appt) => (
              <div 
                key={appt?.id || Math.random()} 
                className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg opacity-75"
                data-testid={`call-completed-${appt?.id}`}
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 size={18} className="text-green-600" />
                  <div>
                    <p className="font-medium text-green-800">{appt?.client_name || 'Unknown Client'}</p>
                    <p className="text-sm text-green-600">{formatTime(appt?.start_time)} • Called</p>
                  </div>
                </div>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={() => handleUnmarkCalled(appt?.id)}
                  className="text-muted-foreground text-xs"
                >
                  Undo
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 2. NEEDS ATTENTION TODAY */}
      <Card className="p-5 bg-white/70 backdrop-blur-xl border border-border/40" data-testid="needs-attention-section">
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle className="text-warning" size={20} />
          <h2 className="text-lg font-semibold">Needs Attention</h2>
        </div>

        <div className="space-y-3">
          {/* Upcoming Sessions (next 4 hours) */}
          {safeNeedsAttention.upcoming_sessions.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Upcoming Sessions</p>
              {safeNeedsAttention.upcoming_sessions.map((session) => (
                <div 
                  key={session?.id || Math.random()} 
                  className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg cursor-pointer hover:bg-blue-100"
                  onClick={() => onNavigate('schedule')}
                >
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="text-blue-600" />
                    <span className="font-medium">{session?.client_name || 'Unknown Client'}</span>
                    <span className="text-sm text-blue-600">{formatTime(session?.start_time)}</span>
                  </div>
                  <ArrowRight size={16} className="text-muted-foreground" />
                </div>
              ))}
            </div>
          )}

          {/* Pending Check-ins */}
          {safeNeedsAttention.pending_checkins.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">In Progress - Need Check-out</p>
              {safeNeedsAttention.pending_checkins.map((session) => (
                <div 
                  key={session?.id || Math.random()} 
                  className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg cursor-pointer hover:bg-amber-100"
                  onClick={() => onNavigate('schedule')}
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={16} className="text-amber-600" />
                    <span className="font-medium">{session?.client_name || 'Unknown Client'}</span>
                    <Badge variant="outline" className="bg-amber-100 text-amber-700">In Progress</Badge>
                  </div>
                  <ArrowRight size={16} className="text-muted-foreground" />
                </div>
              ))}
            </div>
          )}

          {/* Pending Payments */}
          {safeNeedsAttention.pending_payments_count > 0 && (
            <div 
              className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg cursor-pointer hover:bg-red-100"
              onClick={() => onNavigate('payments')}
            >
              <div className="flex items-center gap-2">
                <DollarSign size={16} className="text-red-600" />
                <span className="font-medium">{safeNeedsAttention.pending_payments_count} Pending Payment{safeNeedsAttention.pending_payments_count > 1 ? 's' : ''}</span>
              </div>
              <ArrowRight size={16} className="text-muted-foreground" />
            </div>
          )}

          {safeNeedsAttention.upcoming_sessions.length === 0 && 
           safeNeedsAttention.pending_checkins.length === 0 && 
           safeNeedsAttention.pending_payments_count === 0 && (
            <p className="text-muted-foreground text-center py-4">All caught up! Nothing needs attention right now.</p>
          )}
        </div>
      </Card>

      {/* 3. INACTIVE CLIENTS FOLLOW-UP */}
      <Card className="p-5 bg-white/70 backdrop-blur-xl border border-border/40" data-testid="inactive-clients-section">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <UserX className="text-muted-foreground" size={20} />
            <h2 className="text-lg font-semibold">Inactive Clients (30+ days)</h2>
          </div>
          {inactive_clients_count > 0 && (
            <Badge variant="outline">{inactive_clients_count} clients</Badge>
          )}
        </div>

        {(inactive_clients?.length || 0) === 0 ? (
          <p className="text-muted-foreground text-center py-6">All clients are active!</p>
        ) : (
          <div className="space-y-2">
            {(inactive_clients || []).slice(0, 5).map((client) => (
              <div 
                key={client?.id || Math.random()} 
                className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border"
                data-testid={`inactive-client-${client?.id}`}
              >
                <div>
                  <p className="font-medium">{client?.full_name || 'Unknown Client'}</p>
                  <p className="text-sm text-muted-foreground">
                    {client?.days_inactive !== null && client?.days_inactive !== undefined
                      ? `${client.days_inactive} days since last session`
                      : 'No sessions yet'
                    }
                  </p>
                </div>
                <div className="flex gap-2">
                  {client?.mobile && (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => window.open(`tel:${client.mobile}`, '_blank')}
                      className="gap-1"
                    >
                      <PhoneCall size={14} />
                      Call
                    </Button>
                  )}
                  <Button 
                    size="sm" 
                    onClick={() => onNavigate('schedule')}
                    className="gap-1"
                  >
                    <Calendar size={14} />
                    Schedule
                  </Button>
                </div>
              </div>
            ))}

            {(inactive_clients?.length || 0) > 5 && (
              <Button 
                variant="ghost" 
                className="w-full mt-2"
                onClick={() => onNavigate('clients')}
              >
                View all {inactive_clients_count} inactive clients
              </Button>
            )}
          </div>
        )}
      </Card>

      {/* 4. DAILY PAYMENTS SUMMARY */}
      <Card className="p-5 bg-white/70 backdrop-blur-xl border border-border/40" data-testid="payments-summary-section">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CreditCard className="text-success" size={20} />
            <h2 className="text-lg font-semibold">Today's Payments</h2>
          </div>
          <Button 
            size="sm" 
            onClick={() => onNavigate('payments')}
            className="gap-1"
          >
            <Plus size={14} />
            Record Payment
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-3 bg-green-50 rounded-lg text-center">
            <Banknote size={20} className="mx-auto text-green-600 mb-1" />
            <p className="text-xs text-green-700">Cash</p>
            <p className="font-bold text-green-800">{formatCurrency(safePaymentsSummary.cash_total)}</p>
          </div>
          <div className="p-3 bg-blue-50 rounded-lg text-center">
            <CreditCard size={20} className="mx-auto text-blue-600 mb-1" />
            <p className="text-xs text-blue-700">Online</p>
            <p className="font-bold text-blue-800">{formatCurrency(safePaymentsSummary.online_total)}</p>
          </div>
          <div className="p-3 bg-primary/10 rounded-lg text-center">
            <DollarSign size={20} className="mx-auto text-primary mb-1" />
            <p className="text-xs text-primary">Total</p>
            <p className="font-bold text-primary">{formatCurrency(safePaymentsSummary.total)}</p>
          </div>
        </div>

        {/* Payment List */}
        {safePaymentsSummary.payments.length === 0 ? (
          <p className="text-muted-foreground text-center py-4">No payments recorded today</p>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {safePaymentsSummary.payments.map((payment) => (
              <div 
                key={payment?.id || Math.random()} 
                className="flex items-center justify-between p-2 bg-surface rounded-lg border border-border"
              >
                <div>
                  <p className="font-medium text-sm">{payment?.client_name || 'Unknown Client'}</p>
                  <p className="text-xs text-muted-foreground capitalize">{payment?.payment_method || 'N/A'}</p>
                </div>
                <p className="font-semibold text-success">{formatCurrency(payment?.amount || 0)}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 5. CASH SETTLEMENT */}
      <Card className="p-5 bg-white/70 backdrop-blur-xl border border-border/40" data-testid="cash-settlement-section">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <HandCoins className="text-amber-600" size={20} />
            <h2 className="text-lg font-semibold">End-of-Day Cash Settlement</h2>
          </div>
          {settlement && (
            <Badge 
              variant="outline" 
              className={`
                ${settlement.status === 'pending' ? 'bg-amber-50 text-amber-700 border-amber-200' : ''}
                ${settlement.status === 'handed_over' ? 'bg-blue-50 text-blue-700 border-blue-200' : ''}
                ${settlement.status === 'settled' ? 'bg-green-50 text-green-700 border-green-200' : ''}
                ${settlement.status === 'disputed' ? 'bg-red-50 text-red-700 border-red-200' : ''}
              `}
            >
              {settlement.status === 'pending' && 'Pending'}
              {settlement.status === 'handed_over' && 'Awaiting Confirmation'}
              {settlement.status === 'settled' && 'Settled'}
              {settlement.status === 'disputed' && 'Disputed'}
            </Badge>
          )}
        </div>

        {settlement ? (
          <>
            {/* Settlement Summary */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="p-3 bg-green-50 rounded-lg text-center">
                <Banknote size={18} className="mx-auto text-green-600 mb-1" />
                <p className="text-xs text-green-700">Cash to Hand Over</p>
                <p className="font-bold text-green-800">{formatCurrency(settlement.cash_amount)}</p>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg text-center">
                <CreditCard size={18} className="mx-auto text-blue-600 mb-1" />
                <p className="text-xs text-blue-700">Online (Auto-settled)</p>
                <p className="font-bold text-blue-800">{formatCurrency(settlement.online_amount)}</p>
              </div>
              <div className="p-3 bg-primary/10 rounded-lg text-center">
                <DollarSign size={18} className="mx-auto text-primary mb-1" />
                <p className="text-xs text-primary">Total Today</p>
                <p className="font-bold text-primary">{formatCurrency(settlement.total_amount)}</p>
              </div>
            </div>

            {/* Status-based content */}
            {settlement.status === 'pending' && settlement.cash_amount > 0 && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800 mb-3">
                  You have <span className="font-semibold">{formatCurrency(settlement.cash_amount)}</span> in cash to hand over to the therapist.
                </p>
                <Button 
                  onClick={() => setShowHandoverDialog(true)}
                  className="gap-2 bg-amber-600 hover:bg-amber-700"
                  data-testid="mark-cash-handover-btn"
                >
                  <Send size={16} />
                  Mark Cash Handed Over
                </Button>
              </div>
            )}

            {settlement.status === 'pending' && settlement.cash_amount === 0 && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-center">
                <CheckCircle2 size={24} className="mx-auto text-blue-600 mb-2" />
                <p className="text-sm text-blue-800">No cash to settle today. All payments were online.</p>
              </div>
            )}

            {settlement.status === 'handed_over' && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <Clock size={20} className="text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-800">Handover submitted</p>
                    <p className="text-sm text-blue-600 mt-1">
                      Waiting for {settlement.therapist_name} to confirm receipt of {formatCurrency(settlement.cash_amount)}
                    </p>
                    {settlement.handover_note && (
                      <p className="text-sm text-blue-600 mt-2 italic">Note: "{settlement.handover_note}"</p>
                    )}
                    <p className="text-xs text-blue-500 mt-2">
                      Submitted at {new Date(settlement.handover_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {settlement.status === 'settled' && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <Lock size={20} className="text-green-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-green-800">Settlement Complete</p>
                    <p className="text-sm text-green-600 mt-1">
                      {settlement.therapist_name} confirmed receipt of {formatCurrency(settlement.cash_amount)}
                    </p>
                    <p className="text-xs text-green-500 mt-2">
                      Confirmed at {new Date(settlement.confirmed_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {settlement.status === 'disputed' && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle size={20} className="text-red-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800">Issue Reported</p>
                    <p className="text-sm text-red-600 mt-1">
                      {settlement.therapist_name} reported an issue with the handover.
                    </p>
                    {settlement.disputed_reason && (
                      <p className="text-sm text-red-700 mt-2 p-2 bg-red-100 rounded">
                        Reason: "{settlement.disputed_reason}"
                      </p>
                    )}
                    <p className="text-xs text-red-500 mt-2">Please contact the therapist to resolve this.</p>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-muted-foreground text-center py-4">Loading settlement info...</p>
        )}
      </Card>

      {/* Cash Handover Dialog */}
      <Dialog open={showHandoverDialog} onOpenChange={setShowHandoverDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <HandCoins className="text-amber-600" size={22} />
              Confirm Cash Handover
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 pt-2">
            {/* Amount Summary */}
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-700 mb-1">Cash Amount to Hand Over</p>
              <p className="text-2xl font-bold text-amber-800">
                {settlement && formatCurrency(settlement.cash_amount)}
              </p>
              <p className="text-xs text-amber-600 mt-2">
                This amount is auto-calculated from today's cash payments
              </p>
            </div>

            {/* Note */}
            <div>
              <Label htmlFor="handover-note">Note (Optional)</Label>
              <Textarea
                id="handover-note"
                placeholder="Any notes about the handover..."
                value={handoverNote}
                onChange={(e) => setHandoverNote(e.target.value)}
                className="mt-1"
                rows={3}
              />
            </div>

            {/* Warning */}
            <div className="p-3 bg-muted/50 rounded-lg text-sm text-muted-foreground">
              <p>By clicking "Confirm Handover", you confirm that you have handed over the cash amount to the therapist.</p>
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
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
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <FileCheck size={16} />
                    Confirm Handover
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 6. ACCESS INFO (Collapsible) */}
      <Card className="p-4 bg-info/5 border border-info/20" data-testid="access-info-section">
        <button 
          onClick={() => setShowAccessInfo(!showAccessInfo)}
          className="w-full flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <AlertCircle size={18} className="text-info" />
            <span className="font-medium text-info">Assistant Access Permissions</span>
          </div>
          {showAccessInfo ? <ChevronUp size={18} className="text-info" /> : <ChevronDown size={18} className="text-info" />}
        </button>

        {showAccessInfo && (
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-success mb-2">You CAN:</p>
              <ul className="list-disc list-inside text-muted-foreground space-y-1">
                <li>View and create clients</li>
                <li>View therapist availability</li>
                <li>Schedule and cancel appointments</li>
                <li>Block calendar time</li>
                <li>View and record payments</li>
                <li>Check in/out sessions</li>
                <li>Submit cash handover</li>
              </ul>
            </div>
            <div>
              <p className="font-medium text-destructive mb-2">You CANNOT:</p>
              <ul className="list-disc list-inside text-muted-foreground space-y-1">
                <li>View session notes</li>
                <li>Access assessments or protocols</li>
                <li>Access AI clinical features</li>
                <li>Create/edit/delete availability</li>
                <li>Delete clients permanently</li>
              </ul>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

// ============= MAIN ASSISTANT DASHBOARD =============
const AssistantDashboard = () => {
  const { user, logout } = useAuth();
  const { isReadOnly, refreshStatus } = useSubscription();
  const location = useLocation();
  const [currentView, setCurrentView] = useState('overview');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Check if we're on a client profile page using useLocation for reactivity
  const clientProfileMatch = location.pathname.match(/\/assistant\/clients\/([^/]+)/);
  const isClientProfilePage = !!clientProfileMatch;
  const clientIdFromUrl = clientProfileMatch ? clientProfileMatch[1] : null;

  useEffect(() => {
    refreshStatus();
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [currentView]);

  // Nav items for assistants
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
    if (isClientProfilePage) return 'Client Profile';
    const item = navItems.find(i => i.id === currentView);
    return item ? item.label : 'Dashboard';
  };
  
  // If on client profile page, render full-page client profile with assistant restrictions
  if (isClientProfilePage && clientIdFromUrl) {
    return <ClientProfilePage clientIdProp={clientIdFromUrl} isReadOnly={isReadOnly} isAssistant={true} />;
  }

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
          <Badge className="mt-2 bg-info/10 text-info border-info/20">Assistant</Badge>
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

        <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
          {currentView === 'overview' && <AssistantOverview onNavigate={setCurrentView} />}
          {currentView === 'clients' && <ClientManagement isReadOnly={isReadOnly} isAssistant={true} />}
          {currentView === 'schedule' && (
            <TherapistSchedule 
              isReadOnly={isReadOnly} 
              isAssistant={true}
            />
          )}
          {currentView === 'payments' && <Payments isReadOnly={isReadOnly} />}
        </div>
      </main>
    </div>
  );
};

export default AssistantDashboard;
