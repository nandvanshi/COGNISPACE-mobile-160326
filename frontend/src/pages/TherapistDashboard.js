import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { useSubscription } from '../contexts/SubscriptionContext';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { LogOut, Users, Calendar, FileText, MessageSquare, ClipboardList, BookOpen, DollarSign, Home, AlertTriangle, Clock, Repeat, UserCog, Brain, Settings as SettingsIcon, Sparkles, Menu, X, ChevronDown, CalendarDays, AlertCircle, HandCoins, CheckCircle2, XCircle, Lock, RefreshCw, HelpCircle, UserCircle } from 'lucide-react';
import TherapistOverview from '../components/TherapistOverview';
import ClientManagement from '../components/ClientManagement';
import TherapistSchedule from '../components/TherapistSchedule';
import SessionNotes from '../components/SessionNotes';
import Messaging from '../components/Messaging';
import Assessments from '../components/Assessments';
import Protocols from '../components/Protocols';
import Payments from '../components/Payments';
import AvailabilitySettings from '../components/AvailabilitySettings';
import RecurringAppointments from '../components/RecurringAppointments';
import AssistantManagement from '../components/AssistantManagement';
import AIClinicalSupport from '../components/AIClinicalSupport';
import TherapistProfileSettings from '../components/TherapistProfileSettings';
import SupportTickets from '../components/SupportTickets';
import Settings from '../components/Settings';
import { toast } from 'sonner';
import { formatCurrency } from '../utils/formatUtils';

const TherapistDashboard = () => {
  const { user, logout } = useAuth();
  const { isFeatureEnabled, isReadOnly, daysRemaining, expiryWarning, refreshStatus } = useSubscription();
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState('overview');
  const [showSettings, setShowSettings] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState('Clinical');
  const [hasAvailability, setHasAvailability] = useState(true);
  
  // Navigation context for passing data between views
  const [navContext, setNavContext] = useState({ selectedClientId: null, clientFilter: null, filterData: null });
  
  // Cash Settlement state
  const [pendingSettlements, setPendingSettlements] = useState([]);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [showDisputeDialog, setShowDisputeDialog] = useState(false);
  const [selectedSettlement, setSelectedSettlement] = useState(null);
  const [disputeReason, setDisputeReason] = useState('');
  const [processingSettlement, setProcessingSettlement] = useState(false);

  // Handle navigation with optional context
  const handleNavigation = (view, context = {}) => {
    setNavContext({ 
      selectedClientId: context.clientId || null, 
      clientFilter: context.filter || null,
      filterData: context.inactiveClientIds || null
    });
    setCurrentView(view);
  };

  const fetchPendingSettlements = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/settlements/pending`);
      setPendingSettlements(res.data.pending_settlements || []);
    } catch (error) {
      console.error('Failed to fetch pending settlements:', error);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    checkAvailability();
    fetchPendingSettlements();
    // Refresh settlements every 2 minutes
    const interval = setInterval(fetchPendingSettlements, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchPendingSettlements]);

  // Close mobile menu on view change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [currentView]);

  const checkAvailability = async () => {
    try {
      const res = await axios.get(`${API}/therapist/availability`);
      const data = res.data;
      // Check if therapist has set up any availability
      const hasSetup = data.weekly_schedule && Object.values(data.weekly_schedule).some(day => day.enabled);
      setHasAvailability(hasSetup);
    } catch (error) {
      console.error('Failed to check availability:', error);
    }
  };

  // Map nav items to feature flags
  const featureMap = {
    'notes': 'session_notes',
    'assessments': 'assessments',
    'ai-support': 'ai_clinical',
    'protocols': 'protocols',
    'messages': 'messaging',
    'payments': 'payments',
    'assistants': 'assistants',
  };

  // Organized navigation - Clinical first, then Operations
  const navGroups = [
    {
      label: 'Clinical',
      items: [
        { id: 'overview', label: 'Dashboard', icon: Home },
        { id: 'clients', label: 'Clients', icon: Users },
        { id: 'schedule', label: 'Schedule', icon: CalendarDays },
        { id: 'notes', label: 'Session Notes', icon: FileText, feature: 'session_notes' },
        { id: 'assessments', label: 'Assessments', icon: ClipboardList, feature: 'assessments' },
        { id: 'protocols', label: 'Protocols', icon: BookOpen, feature: 'protocols' },
        { id: 'ai-support', label: 'AI Clinical', icon: Brain, feature: 'ai_clinical' },
      ]
    },
    {
      label: 'Operations',
      items: [
        { id: 'availability', label: 'Availability', icon: Clock },
        { id: 'recurring', label: 'Recurring', icon: Repeat },
        { id: 'messages', label: 'Messages', icon: MessageSquare, feature: 'messaging' },
        { id: 'payments', label: 'Payments', icon: DollarSign, feature: 'payments' },
        { id: 'assistants', label: 'Assistants', icon: UserCog, feature: 'assistants' },
        { id: 'profile', label: 'My Profile', icon: UserCircle },
        { id: 'support', label: 'Support', icon: HelpCircle },
      ]
    }
  ];

  // Filter nav items based on feature toggles
  const filteredNavGroups = navGroups.map(group => ({
    ...group,
    items: group.items.filter(item => !item.feature || isFeatureEnabled(item.feature))
  }));

  // Get current view label for mobile header
  const getCurrentViewLabel = () => {
    for (const group of filteredNavGroups) {
      const item = group.items.find(i => i.id === currentView);
      if (item) return item.label;
    }
    return 'Dashboard';
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleNavClick = (viewId) => {
    setCurrentView(viewId);
    setMobileMenuOpen(false);
  };

  // Cash Settlement handlers
  const handleConfirmSettlement = async () => {
    if (!selectedSettlement) return;
    setProcessingSettlement(true);
    try {
      await axios.post(`${API}/settlements/${selectedSettlement.id}/confirm`);
      toast.success('Cash settlement confirmed and locked');
      setShowConfirmDialog(false);
      setSelectedSettlement(null);
      fetchPendingSettlements();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to confirm settlement');
    } finally {
      setProcessingSettlement(false);
    }
  };

  const handleDisputeSettlement = async () => {
    if (!selectedSettlement || !disputeReason.trim()) {
      toast.error('Please provide a reason for the dispute');
      return;
    }
    if (disputeReason.trim().length < 5) {
      toast.error('Dispute reason must be at least 5 characters');
      return;
    }
    setProcessingSettlement(true);
    try {
      await axios.post(`${API}/settlements/${selectedSettlement.id}/dispute`, { reason: disputeReason.trim() });
      toast.success('Issue reported successfully');
      setShowDisputeDialog(false);
      setSelectedSettlement(null);
      setDisputeReason('');
      fetchPendingSettlements();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to report issue');
    } finally {
      setProcessingSettlement(false);
    }
  };

  const openConfirmDialog = (settlement) => {
    setSelectedSettlement(settlement);
    setShowConfirmDialog(true);
  };

  const openDisputeDialog = (settlement) => {
    setSelectedSettlement(settlement);
    setDisputeReason('');
    setShowDisputeDialog(true);
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

      {/* Sidebar - Desktop: fixed, Mobile: slide-out */}
      <aside className={`
        fixed lg:relative inset-y-0 left-0 z-50
        w-72 lg:w-64 bg-surface border-r border-border flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo Section */}
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
          {!isReadOnly && (
            <span className="inline-block mt-2 px-2.5 py-1 bg-success/10 text-success text-sm rounded-full">
              Active
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 overflow-y-auto">
          {filteredNavGroups.map((group, groupIdx) => (
            <div key={group.label} className={groupIdx > 0 ? 'mt-4' : ''}>
              {/* Collapsible group header for mobile */}
              <button
                onClick={() => setExpandedGroup(expandedGroup === group.label ? '' : group.label)}
                className="w-full flex items-center justify-between px-3 py-2.5 lg:py-0 lg:mb-2 rounded-lg lg:rounded-none hover:bg-muted/50 lg:hover:bg-transparent"
              >
                <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                  {group.label}
                </p>
                <ChevronDown 
                  size={18} 
                  className={`lg:hidden text-muted-foreground transition-transform ${expandedGroup === group.label ? 'rotate-180' : ''}`}
                />
              </button>
              
              {/* Nav items - always visible on desktop, collapsible on mobile */}
              <div className={`space-y-1 overflow-hidden transition-all duration-200 ${
                expandedGroup === group.label ? 'max-h-[500px] opacity-100' : 'max-h-0 lg:max-h-[500px] opacity-0 lg:opacity-100'
              }`}>
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      data-testid={`nav-${item.id}`}
                      onClick={() => handleNavClick(item.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3.5 lg:py-2.5 rounded-lg transition-all ${
                        currentView === item.id
                          ? 'bg-primary text-white shadow-sm'
                          : 'text-foreground hover:bg-muted/60'
                      }`}
                    >
                      <Icon size={20} />
                      <span className="text-base lg:text-sm font-medium">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer Actions */}
        <div className="p-4 border-t border-border space-y-2">
          <Button
            onClick={() => { setShowSettings(true); setMobileMenuOpen(false); }}
            variant="ghost"
            className="w-full justify-start h-14 lg:h-10 text-base lg:text-sm"
            data-testid="settings-button"
          >
            <SettingsIcon size={20} className="mr-3" />
            Settings
          </Button>
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start h-14 lg:h-10 text-muted-foreground hover:text-foreground text-base lg:text-sm"
            data-testid="logout-button"
          >
            <LogOut size={20} className="mr-3" />
            Logout
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-background pt-14 lg:pt-0">
        {/* Expiry Warning Banner */}
        {expiryWarning && !isReadOnly && (
          <div 
            className="bg-amber-50 border-b border-amber-200 text-amber-800 px-4 lg:px-6 py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 sticky top-14 lg:top-0 z-40"
            data-testid="expiry-warning-banner"
          >
            <div className="flex items-center gap-2 flex-1">
              <AlertCircle size={20} className="flex-shrink-0" />
              <p className="font-medium text-sm">
                Your subscription expires in {daysRemaining} day{daysRemaining !== 1 ? 's' : ''}. Renew now to avoid interruption.
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => window.open('mailto:support@theragenie.com?subject=Subscription Renewal', '_blank')}
              className="w-full sm:w-auto border-amber-300 text-amber-800 hover:bg-amber-100"
            >
              Contact Support
            </Button>
          </div>
        )}

        {/* Read-Only Banner */}
        {isReadOnly && (
          <div 
            className="bg-warning text-warning-foreground px-4 lg:px-6 py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 sticky top-14 lg:top-0 z-40 shadow-sm"
            data-testid="subscription-expired-banner"
          >
            <div className="flex items-center gap-2 flex-1">
              <AlertTriangle size={20} className="flex-shrink-0" />
              <p className="font-medium text-sm">Subscription expired. Read-only mode.</p>
            </div>
            <Button 
              variant="secondary" 
              size="sm"
              onClick={() => window.open('mailto:support@theragenie.com?subject=Subscription Renewal', '_blank')}
              data-testid="contact-support-button"
              className="w-full sm:w-auto"
            >
              Contact Support
            </Button>
          </div>
        )}

        {/* Availability Setup Prompt */}
        {!hasAvailability && currentView === 'overview' && (
          <div 
            className="bg-blue-50 border-b border-blue-200 text-blue-800 px-4 lg:px-6 py-3 flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4"
            data-testid="availability-setup-banner"
          >
            <div className="flex items-center gap-2 flex-1">
              <Clock size={20} className="flex-shrink-0" />
              <p className="font-medium text-sm">
                Set up your availability to start accepting appointments.
              </p>
            </div>
            <Button 
              size="sm"
              onClick={() => setCurrentView('availability')}
              className="w-full sm:w-auto"
            >
              Set Availability
            </Button>
          </div>
        )}

        {/* Pending Cash Settlement Alert */}
        {pendingSettlements.filter(s => s.status === 'handed_over').map((settlement) => (
          <div 
            key={settlement.id}
            className="bg-amber-50 border-b border-amber-200 text-amber-800 px-4 lg:px-6 py-3"
            data-testid="pending-settlement-banner"
          >
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <div className="flex items-center gap-2 flex-1">
                <HandCoins size={20} className="flex-shrink-0 text-amber-600" />
                <div>
                  <p className="font-medium text-sm">
                    Cash handover pending: <span className="font-bold">{formatCurrency(settlement.cash_amount)}</span>
                  </p>
                  <p className="text-xs text-amber-600">
                    From {settlement.assistant_name} • {settlement.date}
                    {settlement.handover_note && ` • Note: "${settlement.handover_note}"`}
                  </p>
                </div>
              </div>
              <div className="flex gap-2 w-full sm:w-auto">
                <Button 
                  size="sm"
                  onClick={() => openConfirmDialog(settlement)}
                  className="flex-1 sm:flex-initial gap-1 bg-green-600 hover:bg-green-700"
                  data-testid="confirm-settlement-btn"
                >
                  <CheckCircle2 size={16} />
                  Confirm Received
                </Button>
                <Button 
                  size="sm"
                  variant="outline"
                  onClick={() => openDisputeDialog(settlement)}
                  className="flex-1 sm:flex-initial gap-1 border-red-300 text-red-700 hover:bg-red-50"
                  data-testid="dispute-settlement-btn"
                >
                  <XCircle size={16} />
                  Report Issue
                </Button>
              </div>
            </div>
          </div>
        ))}

        {/* Disputed Settlement Alert */}
        {pendingSettlements.filter(s => s.status === 'disputed').map((settlement) => (
          <div 
            key={settlement.id}
            className="bg-red-50 border-b border-red-200 text-red-800 px-4 lg:px-6 py-3"
            data-testid="disputed-settlement-banner"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle size={20} className="flex-shrink-0 text-red-600" />
              <div>
                <p className="font-medium text-sm">
                  Disputed settlement: {formatCurrency(settlement.cash_amount)} from {settlement.assistant_name}
                </p>
                <p className="text-xs text-red-600">
                  Reason: "{settlement.disputed_reason}" • Please resolve with your assistant
                </p>
              </div>
            </div>
          </div>
        ))}

        <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-10">
          {currentView === 'overview' && (
            <TherapistOverview 
              isReadOnly={isReadOnly} 
              onNavigate={handleNavigation}
            />
          )}
          {currentView === 'clients' && (
            <ClientManagement 
              isReadOnly={isReadOnly} 
              initialClientId={navContext.selectedClientId}
              initialFilter={navContext.clientFilter}
              filterData={navContext.filterData}
              onClearContext={() => setNavContext({ selectedClientId: null, clientFilter: null, filterData: null })}
            />
          )}
          {currentView === 'schedule' && <TherapistSchedule isReadOnly={isReadOnly} />}
          {currentView === 'availability' && <AvailabilitySettings isReadOnly={isReadOnly} onSave={() => setHasAvailability(true)} />}
          {currentView === 'recurring' && <RecurringAppointments isReadOnly={isReadOnly} />}
          {currentView === 'notes' && <SessionNotes isReadOnly={isReadOnly} />}
          {currentView === 'messages' && <Messaging isReadOnly={isReadOnly} />}
          {currentView === 'assessments' && <Assessments isReadOnly={isReadOnly} />}
          {currentView === 'protocols' && <Protocols isReadOnly={isReadOnly} />}
          {currentView === 'ai-support' && <AIClinicalSupport isReadOnly={isReadOnly} />}
          {currentView === 'payments' && <Payments isReadOnly={isReadOnly} />}
          {currentView === 'assistants' && <AssistantManagement isReadOnly={isReadOnly} />}
          {currentView === 'support' && <SupportTickets />}
        </div>
      </main>

      <Settings isOpen={showSettings} onClose={() => setShowSettings(false)} />

      {/* Confirm Settlement Dialog */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="text-green-600" size={22} />
              Confirm Cash Receipt
            </DialogTitle>
          </DialogHeader>
          
          {selectedSettlement && (
            <div className="space-y-4 pt-2">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-700 mb-1">Cash Amount Received</p>
                <p className="text-2xl font-bold text-green-800">
                  {formatCurrency(selectedSettlement.cash_amount)}
                </p>
                <p className="text-xs text-green-600 mt-2">
                  From: {selectedSettlement.assistant_name} • Date: {selectedSettlement.date}
                </p>
                {selectedSettlement.handover_note && (
                  <p className="text-xs text-green-600 mt-1 italic">
                    Note: "{selectedSettlement.handover_note}"
                  </p>
                )}
              </div>

              <div className="p-3 bg-muted/50 rounded-lg text-sm text-muted-foreground">
                <div className="flex items-start gap-2">
                  <Lock size={16} className="flex-shrink-0 mt-0.5" />
                  <p>Confirming will <strong>lock this settlement record</strong>. This action cannot be undone.</p>
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setShowConfirmDialog(false)}
                  className="flex-1"
                  disabled={processingSettlement}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmSettlement}
                  className="flex-1 bg-green-600 hover:bg-green-700 gap-2"
                  disabled={processingSettlement}
                  data-testid="confirm-receipt-final-btn"
                >
                  {processingSettlement ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={16} />
                      Confirm & Lock
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Dispute Settlement Dialog */}
      <Dialog open={showDisputeDialog} onOpenChange={setShowDisputeDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <XCircle className="text-red-600" size={22} />
              Report Issue
            </DialogTitle>
          </DialogHeader>
          
          {selectedSettlement && (
            <div className="space-y-4 pt-2">
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700 mb-1">Reported Amount</p>
                <p className="text-2xl font-bold text-red-800">
                  {formatCurrency(selectedSettlement.cash_amount)}
                </p>
                <p className="text-xs text-red-600 mt-2">
                  From: {selectedSettlement.assistant_name}
                </p>
              </div>

              <div>
                <Label htmlFor="dispute-reason" className="text-red-700">Reason for Dispute *</Label>
                <Textarea
                  id="dispute-reason"
                  placeholder="Please describe the issue (e.g., amount mismatch, cash not received)..."
                  value={disputeReason}
                  onChange={(e) => setDisputeReason(e.target.value)}
                  className="mt-1 border-red-200 focus:border-red-400"
                  rows={3}
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">Minimum 5 characters required</p>
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setShowDisputeDialog(false)}
                  className="flex-1"
                  disabled={processingSettlement}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleDisputeSettlement}
                  variant="destructive"
                  className="flex-1 gap-2"
                  disabled={processingSettlement || disputeReason.trim().length < 5}
                  data-testid="submit-dispute-btn"
                >
                  {processingSettlement ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <AlertTriangle size={16} />
                      Report Issue
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TherapistDashboard;
