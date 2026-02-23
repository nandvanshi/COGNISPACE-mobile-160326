import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { 
  LogOut, Calendar, ClipboardCheck, BookOpen, 
  FileCheck, Pen, Check, AlertCircle, Loader2, Shield, 
  Receipt, Clock, Settings as SettingsIcon,
  Eye, FileText, Sparkles, CheckCircle, User, MessageCircle, Send,
  Home, CalendarDays, BookMarked, BarChart3, Bell, ChevronRight,
  ExternalLink, Download, Play, Video, FileType, Link2
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDate, formatTime, formatCurrency } from '../utils/formatUtils';
import { PaymentReceiptView } from '../components/PaymentReceipt';
import Settings from '../components/Settings';
import ClientAssessmentTaker from '../components/ClientAssessmentTaker';
import Messaging from '../components/Messaging';
import NotificationBell from '../components/NotificationBell';

// ============= TIME-BASED GREETING =============
const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return { text: 'Good Morning', icon: '🌅' };
  if (hour >= 12 && hour < 17) return { text: 'Good Afternoon', icon: '☀️' };
  if (hour >= 17 && hour < 21) return { text: 'Good Evening', icon: '🌆' };
  return { text: 'Good Night', icon: '🌙' };
};

// ============= BOTTOM NAV ITEMS =============
const NAV_ITEMS = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'appointments', label: 'Schedule', icon: CalendarDays },
  { id: 'tasks', label: 'My Tasks', icon: ClipboardCheck },
  { id: 'reports', label: 'Reports', icon: BarChart3 },
  { id: 'messages', label: 'Messages', icon: MessageCircle },
];

// ============= RESOURCE TYPE ICONS =============
const getResourceIcon = (type) => {
  switch (type?.toLowerCase()) {
    case 'video': return Video;
    case 'pdf': return FileType;
    case 'link': return Link2;
    case 'article': return FileText;
    default: return BookOpen;
  }
};

const ClientDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  // Active tab state
  const [activeTab, setActiveTab] = useState('home');
  
  // Data states
  const [appointments, setAppointments] = useState([]);
  const [homework, setHomework] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [payments, setPayments] = useState([]);
  const [resources, setResources] = useState([]);
  const [diagnosticReports, setDiagnosticReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [therapistName, setTherapistName] = useState('');
  
  // Consent state
  const [consentStatus, setConsentStatus] = useState({ exists: false, is_signed: false });
  const [consent, setConsent] = useState(null);
  const [consentLoading, setConsentLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [consentAgreed, setConsentAgreed] = useState(false);
  
  // Dialog states
  const [showAssessmentTaker, setShowAssessmentTaker] = useState(false);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showMessaging, setShowMessaging] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showReceiptDialog, setShowReceiptDialog] = useState(false);
  const [selectedPaymentId, setSelectedPaymentId] = useState(null);
  const [showDiagnosticReport, setShowDiagnosticReport] = useState(false);
  const [selectedDiagnosticReport, setSelectedDiagnosticReport] = useState(null);
  const [showResourceDetail, setShowResourceDetail] = useState(false);
  const [selectedResource, setSelectedResource] = useState(null);

  useEffect(() => {
    checkConsentStatus();
  }, []);

  const checkConsentStatus = async () => {
    try {
      const response = await axios.get(`${API}/therapy-consent/check/${user?.id}`);
      setConsentStatus(response.data);
      
      if (response.data.exists && !response.data.is_signed) {
        const consentRes = await axios.get(`${API}/therapy-consent/${user?.id}`);
        setConsent(consentRes.data);
        if (consentRes.data?.therapist_name) {
          setTherapistName(consentRes.data.therapist_name);
        }
      }
      
      if (response.data.is_signed) {
        fetchDashboardData();
      }
    } catch (error) {
      if (error.response?.status === 404) {
        setConsentStatus({ exists: false, is_signed: false });
      }
    } finally {
      setConsentLoading(false);
      setLoading(false);
    }
  };

  const fetchDashboardData = useCallback(async () => {
    try {
      const [apptsRes, hwRes, assessRes, paymentsRes] = await Promise.all([
        axios.get(`${API}/appointments`),
        axios.get(`${API}/homework`),
        axios.get(`${API}/assessments`),
        axios.get(`${API}/payments`),
      ]);
      setAppointments(apptsRes.data);
      setHomework(hwRes.data);
      setAssessments(assessRes.data);
      setPayments(paymentsRes.data);
      
      // Fetch shared resources
      try {
        const resourcesRes = await axios.get(`${API}/resources/assignments`);
        setResources(resourcesRes.data || []);
      } catch (e) { console.log('Resources not available'); }
      
      // Fetch unread message count
      try {
        const unreadRes = await axios.get(`${API}/messages/unread-count`);
        setUnreadCount(unreadRes.data?.count || 0);
      } catch (e) { /* ignore */ }
      
      // Fetch diagnostic reports
      try {
        const reportsRes = await axios.get(`${API}/diagnostic-reports`);
        setDiagnosticReports(reportsRes.data || []);
      } catch (e) { /* ignore */ }
      
      // Get therapist name
      if (!therapistName && user?.therapist_id) {
        try {
          const consentRes = await axios.get(`${API}/therapy-consent/${user.id}`);
          if (consentRes.data?.therapist_name) {
            setTherapistName(consentRes.data.therapist_name);
          }
        } catch (e) { /* ignore */ }
      }
    } catch (error) {
      toast.error('Failed to load data');
    }
  }, [therapistName, user]);

  const handleSignConsent = async () => {
    if (!consentAgreed) {
      toast.error('Please agree to the consent');
      return;
    }
    setSigning(true);
    try {
      await axios.post(`${API}/therapy-consent/${user?.id}/sign?signature_method=digital`);
      toast.success('Consent signed successfully!');
      setConsentStatus({ ...consentStatus, is_signed: true });
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sign consent');
    } finally {
      setSigning(false);
    }
  };

  const handleCompleteHomework = async (hwId) => {
    const notes = prompt('Add your notes about this homework:');
    if (!notes) return;
    try {
      await axios.post(`${API}/homework/${hwId}/complete`, { client_notes: notes });
      toast.success('Homework marked as complete');
      fetchDashboardData();
    } catch (error) {
      toast.error('Failed to complete homework');
    }
  };

  const handleCompleteAssessment = (assessment) => {
    if (assessment.status === 'completed') {
      toast.info('Assessment already completed');
      return;
    }
    setSelectedAssessmentId(assessment.id);
    setShowAssessmentTaker(true);
  };

  const handleAssessmentComplete = () => {
    setShowAssessmentTaker(false);
    setSelectedAssessmentId(null);
    fetchDashboardData();
    toast.success('Assessment completed!');
  };

  const handleViewResource = async (resource) => {
    setSelectedResource(resource);
    setShowResourceDetail(true);
    
    // Mark as viewed
    if (!resource.viewed_at) {
      try {
        await axios.post(`${API}/resources/assignments/${resource.id}/view`);
        fetchDashboardData();
      } catch (e) { /* ignore */ }
    }
  };

  const handleMarkResourceComplete = async (resourceId) => {
    try {
      await axios.post(`${API}/resources/assignments/${resourceId}/complete`);
      toast.success('Marked as completed!');
      setShowResourceDetail(false);
      fetchDashboardData();
    } catch (error) {
      toast.error('Failed to mark as complete');
    }
  };

  const handleViewDiagnosticReport = async (reportId) => {
    try {
      const res = await axios.get(`${API}/diagnostic-reports/${reportId}`);
      setSelectedDiagnosticReport(res.data);
      setShowDiagnosticReport(true);
    } catch (error) {
      toast.error('Report not available');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleNotificationNavigate = (view, context) => {
    if (view === 'messages') setActiveTab('messages');
    else if (view === 'appointments') setActiveTab('appointments');
  };

  // Loading state
  if (loading || consentLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 to-teal-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  // Consent not signed - show consent form
  if (consentStatus.exists && !consentStatus.is_signed && consent) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 to-teal-50 p-4">
        <Card className="max-w-lg mx-auto mt-8 p-6 rounded-3xl">
          <div className="text-center mb-6">
            <Shield className="h-12 w-12 text-emerald-600 mx-auto mb-3" />
            <h1 className="text-xl font-serif text-emerald-800">Therapy Consent Required</h1>
            <p className="text-sm text-gray-600 mt-1">
              Please review and sign before continuing
            </p>
          </div>
          
          <div className="bg-gray-50 rounded-2xl p-4 max-h-[50vh] overflow-y-auto mb-4 text-sm">
            {consent?.consent_text?.split('\n').map((line, idx) => {
              if (line.match(/^\d+\.\s/)) {
                return <h3 key={idx} className="font-semibold text-emerald-700 mt-3 mb-1">{line}</h3>;
              }
              if (line.startsWith('•') || line.startsWith('-')) {
                return <p key={idx} className="ml-3 text-gray-600">{line}</p>;
              }
              if (!line.trim()) return <div key={idx} className="h-2" />;
              return <p key={idx} className="text-gray-700">{line}</p>;
            })}
          </div>

          <div className="flex items-start gap-3 p-4 bg-emerald-50 rounded-2xl mb-4">
            <Checkbox
              id="consent-agree"
              checked={consentAgreed}
              onCheckedChange={setConsentAgreed}
              data-testid="consent-agree-checkbox"
            />
            <label htmlFor="consent-agree" className="text-sm cursor-pointer text-emerald-800">
              I have read and agree to the terms above.
            </label>
          </div>

          <Button
            onClick={handleSignConsent}
            disabled={signing || !consentAgreed}
            className="w-full py-5 rounded-2xl bg-emerald-600"
            data-testid="sign-consent-button"
          >
            {signing ? <Loader2 className="animate-spin mr-2" size={18} /> : <Pen className="mr-2" size={18} />}
            Sign Consent
          </Button>
        </Card>
      </div>
    );
  }

  // CONSENT SIGNED - Show dashboard
  const greeting = getGreeting();
  const upcomingAppointments = appointments
    .filter((a) => new Date(a.start_time) > new Date() && a.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
  const pendingHomework = homework.filter((h) => h.status === 'assigned');
  const pendingAssessments = assessments.filter((a) => a.status !== 'completed');
  const unviewedResources = resources.filter((r) => !r.viewed_at);

  // ============= RENDER CONTENT BASED ON ACTIVE TAB =============
  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <HomeTab 
          greeting={greeting}
          user={user}
          therapistName={therapistName}
          upcomingAppointments={upcomingAppointments}
          pendingHomework={pendingHomework}
          pendingAssessments={pendingAssessments}
          unviewedResources={unviewedResources}
          onCompleteHomework={handleCompleteHomework}
          onCompleteAssessment={handleCompleteAssessment}
          onViewResource={handleViewResource}
          setActiveTab={setActiveTab}
        />;
      case 'appointments':
        return <AppointmentsTab 
          appointments={appointments}
          payments={payments}
          onViewReceipt={(id) => { setSelectedPaymentId(id); setShowReceiptDialog(true); }}
        />;
      case 'tasks':
        return <MyTasksTab 
          homework={homework}
          assessments={assessments}
          resources={resources}
          onCompleteHomework={handleCompleteHomework}
          onCompleteAssessment={handleCompleteAssessment}
          onViewResource={handleViewResource}
        />;
      case 'reports':
        return <ReportsTab 
          assessments={assessments}
          diagnosticReports={diagnosticReports}
          onViewReport={handleViewDiagnosticReport}
        />;
      case 'messages':
        return <Messaging />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-white pb-20" data-testid="client-dashboard">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-lg border-b border-emerald-100 sticky top-0 z-40">
        <div className="max-w-lg mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <img src="/logo-symbol.png" alt="COGNISPACE" className="h-7 w-auto" />
            <span className="font-serif text-lg text-emerald-700">COGNISPACE</span>
          </div>
          <div className="flex items-center gap-1">
            <NotificationBell onNavigate={handleNotificationNavigate} />
            <Button onClick={() => setShowSettings(true)} variant="ghost" size="sm" className="p-2">
              <SettingsIcon size={18} className="text-gray-500" />
            </Button>
            <Button onClick={handleLogout} variant="ghost" size="sm" className="p-2" data-testid="client-logout-button">
              <LogOut size={18} className="text-gray-500" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-lg mx-auto px-4 pt-4">
        {renderContent()}
      </main>

      {/* Bottom Navigation Bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 safe-area-bottom" data-testid="bottom-nav">
        <div className="max-w-lg mx-auto px-2">
          <div className="flex justify-around items-center py-2">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              const showBadge = item.id === 'messages' && unreadCount > 0;
              // Tasks badge: pending homework + pending assessments + unviewed resources
              const pendingTasksCount = pendingHomework.length + pendingAssessments.length + unviewedResources.length;
              const showTasksBadge = item.id === 'tasks' && pendingTasksCount > 0;
              
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex flex-col items-center py-2 px-3 rounded-xl transition-all relative ${
                    isActive 
                      ? 'text-emerald-600 bg-emerald-50' 
                      : 'text-gray-500 hover:text-emerald-600'
                  }`}
                  data-testid={`nav-${item.id}`}
                >
                  <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
                  <span className={`text-xs mt-1 ${isActive ? 'font-semibold' : ''}`}>{item.label}</span>
                  {showBadge && (
                    <span className="absolute -top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                  {showTasksBadge && (
                    <span className="absolute -top-1 right-1 w-5 h-5 bg-amber-500 text-white text-xs rounded-full flex items-center justify-center">
                      {pendingTasksCount > 9 ? '9+' : pendingTasksCount}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Dialogs */}
      <PaymentReceiptView
        paymentId={selectedPaymentId}
        isOpen={showReceiptDialog}
        onClose={() => setShowReceiptDialog(false)}
      />
      <Settings isOpen={showSettings} onClose={() => setShowSettings(false)} />
      
      {/* Assessment Taker */}
      <Dialog open={showAssessmentTaker} onOpenChange={(open) => !open && setShowAssessmentTaker(false)}>
        <DialogContent className="max-w-2xl max-h-[95vh] overflow-y-auto p-0 rounded-3xl">
          {selectedAssessmentId && (
            <ClientAssessmentTaker
              assessmentId={selectedAssessmentId}
              onComplete={handleAssessmentComplete}
              onCancel={() => setShowAssessmentTaker(false)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Resource Detail Dialog */}
      <Dialog open={showResourceDetail} onOpenChange={setShowResourceDetail}>
        <DialogContent className="max-w-lg rounded-3xl" data-testid="resource-detail-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <BookMarked size={20} /> Resource Details
            </DialogTitle>
          </DialogHeader>
          {selectedResource && (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">{selectedResource.resource_title}</h3>
                <p className="text-sm text-gray-500 capitalize">{selectedResource.resource_type || 'Resource'}</p>
              </div>
              
              {selectedResource.resource_description && (
                <p className="text-sm text-gray-600">{selectedResource.resource_description}</p>
              )}
              
              {selectedResource.therapist_notes && (
                <Card className="p-3 bg-emerald-50 border-emerald-100 rounded-xl">
                  <p className="text-xs font-medium text-emerald-700 mb-1">Note from your therapist:</p>
                  <p className="text-sm text-emerald-800">{selectedResource.therapist_notes}</p>
                </Card>
              )}
              
              {selectedResource.resource_url && (
                <Button
                  onClick={() => window.open(selectedResource.resource_url, '_blank')}
                  className="w-full rounded-xl bg-emerald-600 gap-2"
                >
                  <ExternalLink size={16} /> Open Resource
                </Button>
              )}
              
              {!selectedResource.completed_at && (
                <Button
                  onClick={() => handleMarkResourceComplete(selectedResource.id)}
                  variant="outline"
                  className="w-full rounded-xl border-emerald-300 text-emerald-700 gap-2"
                >
                  <CheckCircle size={16} /> Mark as Completed
                </Button>
              )}
              
              {selectedResource.completed_at && (
                <div className="flex items-center justify-center gap-2 text-emerald-600 py-2">
                  <CheckCircle size={18} />
                  <span className="text-sm font-medium">Completed on {formatDate(selectedResource.completed_at)}</span>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Diagnostic Report Dialog */}
      <Dialog open={showDiagnosticReport} onOpenChange={setShowDiagnosticReport}>
        <DialogContent className="max-w-4xl max-h-[95vh] overflow-hidden p-0 rounded-3xl">
          <DialogHeader className="p-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white">
            <DialogTitle className="flex items-center gap-2">
              <Sparkles size={20} /> Diagnostic Report
            </DialogTitle>
          </DialogHeader>
          {selectedDiagnosticReport && (
            <div className="flex flex-col h-[calc(95vh-120px)]">
              <div className="px-4 py-2 bg-violet-50 border-b flex justify-between items-center">
                <div>
                  <p className="font-semibold text-violet-900">{selectedDiagnosticReport.title}</p>
                  <p className="text-xs text-violet-600">
                    {selectedDiagnosticReport.created_at && formatDate(selectedDiagnosticReport.created_at)}
                  </p>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
                {(selectedDiagnosticReport.report_html || selectedDiagnosticReport.report_content) ? (
                  <div 
                    className="bg-white rounded-xl shadow-sm border p-6 prose prose-sm max-w-none"
                    dangerouslySetInnerHTML={{ __html: selectedDiagnosticReport.report_html || selectedDiagnosticReport.report_content }}
                  />
                ) : (
                  <div className="text-center py-10 text-gray-500">
                    <FileText size={40} className="mx-auto mb-3 text-gray-300" />
                    <p>Report content not available</p>
                  </div>
                )}
              </div>
              <div className="p-4 bg-white border-t">
                <Button onClick={() => setShowDiagnosticReport(false)} className="w-full rounded-xl bg-violet-600">
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ============= HOME TAB COMPONENT =============
const HomeTab = ({ 
  greeting, user, therapistName, upcomingAppointments, 
  pendingHomework, pendingAssessments, unviewedResources,
  onCompleteHomework, onCompleteAssessment, onViewResource, setActiveTab 
}) => {
  const nextAppointment = upcomingAppointments[0];
  
  return (
    <div className="space-y-4 pb-4" data-testid="home-tab">
      {/* Greeting Card */}
      <Card className="p-5 rounded-3xl bg-gradient-to-br from-emerald-600 to-teal-600 text-white border-0">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-emerald-100 text-sm">{greeting.text}</p>
            <h1 className="text-2xl font-serif mt-1">{user?.full_name?.split(' ')[0]} {greeting.icon}</h1>
            {therapistName && (
              <p className="text-emerald-100 text-sm mt-2">Your therapist: {therapistName}</p>
            )}
          </div>
          <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
            <User size={24} />
          </div>
        </div>
      </Card>

      {/* Next Appointment Quick View */}
      {nextAppointment && (
        <Card 
          className="p-4 rounded-2xl border-emerald-200 bg-emerald-50/50 cursor-pointer hover:bg-emerald-50"
          onClick={() => setActiveTab('appointments')}
          data-testid="next-appointment-card"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                <CalendarDays size={20} className="text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-emerald-600 font-medium">Next Session</p>
                <p className="font-semibold text-gray-800">{formatDate(nextAppointment.start_time)}</p>
                <p className="text-sm text-gray-500">{formatTime(nextAppointment.start_time)}</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-gray-400" />
          </div>
        </Card>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <Card 
          className="p-3 rounded-2xl text-center cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => setActiveTab('appointments')}
        >
          <p className="text-2xl font-bold text-emerald-600">{upcomingAppointments.length}</p>
          <p className="text-xs text-gray-500">Upcoming</p>
        </Card>
        <Card 
          className="p-3 rounded-2xl text-center cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => setActiveTab('resources')}
        >
          <p className="text-2xl font-bold text-blue-600">{unviewedResources.length}</p>
          <p className="text-xs text-gray-500">New Resources</p>
        </Card>
        <Card 
          className="p-3 rounded-2xl text-center cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => setActiveTab('reports')}
        >
          <p className="text-2xl font-bold text-violet-600">{pendingAssessments.length}</p>
          <p className="text-xs text-gray-500">Pending</p>
        </Card>
      </div>

      {/* Pending Homework */}
      {pendingHomework.length > 0 && (
        <Card className="p-4 rounded-2xl" data-testid="homework-section">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <ClipboardCheck size={18} className="text-amber-500" />
              Homework
            </h3>
            <Badge className="bg-amber-100 text-amber-700">{pendingHomework.length} pending</Badge>
          </div>
          <div className="space-y-2">
            {pendingHomework.slice(0, 3).map((hw) => (
              <div key={hw.id} className="flex items-center justify-between p-3 bg-amber-50 rounded-xl">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800 truncate">{hw.title}</p>
                  {hw.due_date && (
                    <p className="text-xs text-amber-600">Due: {formatDate(hw.due_date)}</p>
                  )}
                </div>
                <Button 
                  size="sm" 
                  onClick={() => onCompleteHomework(hw.id)}
                  className="rounded-lg bg-amber-500 hover:bg-amber-600 ml-2"
                >
                  <Check size={14} />
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Pending Assessments */}
      {pendingAssessments.length > 0 && (
        <Card className="p-4 rounded-2xl" data-testid="assessments-section">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <FileCheck size={18} className="text-blue-500" />
              Assessments
            </h3>
          </div>
          <div className="space-y-2">
            {pendingAssessments.slice(0, 2).map((assess) => (
              <div 
                key={assess.id} 
                className="flex items-center justify-between p-3 bg-blue-50 rounded-xl cursor-pointer hover:bg-blue-100"
                onClick={() => onCompleteAssessment(assess)}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-800">{assess.assessment_type}</p>
                  <p className="text-xs text-blue-600">Tap to complete</p>
                </div>
                <ChevronRight size={18} className="text-blue-400" />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* New Resources Preview */}
      {unviewedResources.length > 0 && (
        <Card className="p-4 rounded-2xl" data-testid="new-resources-section">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <BookMarked size={18} className="text-emerald-500" />
              New Resources
            </h3>
            <Button variant="ghost" size="sm" onClick={() => setActiveTab('tasks')} className="text-emerald-600 text-xs">
              View All
            </Button>
          </div>
          <div className="space-y-2">
            {unviewedResources.slice(0, 2).map((resource) => {
              const Icon = getResourceIcon(resource.resource_type);
              return (
                <div 
                  key={resource.id} 
                  className="flex items-center gap-3 p-3 bg-emerald-50 rounded-xl cursor-pointer hover:bg-emerald-100"
                  onClick={() => onViewResource(resource)}
                >
                  <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <Icon size={18} className="text-emerald-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 truncate">{resource.resource_title}</p>
                    <p className="text-xs text-emerald-600 capitalize">{resource.resource_type || 'Resource'}</p>
                  </div>
                  <ChevronRight size={18} className="text-emerald-400" />
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Empty state */}
      {pendingHomework.length === 0 && pendingAssessments.length === 0 && unviewedResources.length === 0 && (
        <Card className="p-6 rounded-2xl text-center bg-gradient-to-br from-emerald-50 to-teal-50">
          <CheckCircle size={40} className="mx-auto text-emerald-400 mb-3" />
          <p className="font-medium text-gray-700">All caught up!</p>
          <p className="text-sm text-gray-500">No pending tasks at the moment</p>
        </Card>
      )}
    </div>
  );
};

// ============= APPOINTMENTS TAB COMPONENT =============
const AppointmentsTab = ({ appointments, payments, onViewReceipt }) => {
  const upcoming = appointments
    .filter((a) => new Date(a.start_time) > new Date() && a.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
  const past = appointments
    .filter((a) => new Date(a.start_time) <= new Date() || a.status === 'cancelled')
    .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
    .slice(0, 10);

  return (
    <div className="space-y-4 pb-4" data-testid="appointments-tab">
      <h2 className="text-lg font-semibold text-gray-800">Your Schedule</h2>
      
      {/* Upcoming */}
      <div>
        <h3 className="text-sm font-medium text-emerald-600 mb-2">Upcoming Sessions</h3>
        {upcoming.length === 0 ? (
          <Card className="p-4 rounded-2xl text-center text-gray-500">
            <CalendarDays size={32} className="mx-auto text-gray-300 mb-2" />
            <p className="text-sm">No upcoming appointments</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {upcoming.map((appt) => (
              <Card key={appt.id} className="p-4 rounded-2xl">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex flex-col items-center justify-center">
                    <span className="text-xs text-emerald-600">{new Date(appt.start_time).toLocaleDateString('en', { month: 'short' })}</span>
                    <span className="text-lg font-bold text-emerald-700">{new Date(appt.start_time).getDate()}</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">{formatTime(appt.start_time)}</p>
                    <p className="text-sm text-gray-500">{appt.session_type || 'Session'}</p>
                  </div>
                  <Badge className="bg-emerald-100 text-emerald-700 capitalize">{appt.status}</Badge>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Past Sessions */}
      {past.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Past Sessions</h3>
          <div className="space-y-2">
            {past.map((appt) => (
              <Card key={appt.id} className="p-3 rounded-xl bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-700">{formatDate(appt.start_time)}</p>
                    <p className="text-xs text-gray-500">{formatTime(appt.start_time)}</p>
                  </div>
                  <Badge variant="outline" className="capitalize text-xs">{appt.status}</Badge>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Recent Payments */}
      {payments.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Recent Payments</h3>
          <div className="space-y-2">
            {payments.slice(0, 5).map((payment) => (
              <Card 
                key={payment.id} 
                className="p-3 rounded-xl cursor-pointer hover:bg-gray-50"
                onClick={() => onViewReceipt(payment.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-700">{formatCurrency(payment.amount)}</p>
                    <p className="text-xs text-gray-500">{formatDate(payment.date || payment.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={payment.transaction_type === 'debit' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}>
                      {payment.transaction_type === 'debit' ? 'Refund' : 'Paid'}
                    </Badge>
                    <Receipt size={16} className="text-gray-400" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ============= MY TASKS TAB COMPONENT =============
const MyTasksTab = ({ homework, assessments, resources, onCompleteHomework, onCompleteAssessment, onViewResource }) => {
  const pendingHomework = homework.filter(h => h.status === 'assigned');
  const completedHomework = homework.filter(h => h.status === 'completed');
  const pendingAssessments = assessments.filter(a => a.status !== 'completed');
  const completedAssessments = assessments.filter(a => a.status === 'completed');
  const unviewedResources = resources.filter(r => !r.viewed_at);
  const viewedResources = resources.filter(r => r.viewed_at && !r.completed_at);
  const completedResources = resources.filter(r => r.completed_at);

  const totalPending = pendingHomework.length + pendingAssessments.length + unviewedResources.length;

  return (
    <div className="space-y-4 pb-4" data-testid="tasks-tab">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">My Tasks</h2>
        {totalPending > 0 && (
          <Badge className="bg-amber-100 text-amber-700">{totalPending} pending</Badge>
        )}
      </div>

      {/* HOMEWORK SECTION */}
      {(pendingHomework.length > 0 || completedHomework.length > 0) && (
        <div>
          <h3 className="text-sm font-medium text-amber-600 mb-2 flex items-center gap-2">
            <ClipboardCheck size={16} /> Homework
          </h3>
          
          {/* Pending Homework */}
          {pendingHomework.length > 0 && (
            <div className="space-y-2 mb-3">
              {pendingHomework.map((hw) => (
                <Card 
                  key={hw.id} 
                  className="p-4 rounded-2xl border-amber-200 bg-amber-50/50"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800">{hw.title}</p>
                      {hw.description && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">{hw.description}</p>
                      )}
                      {hw.due_date && (
                        <p className="text-xs text-amber-600 mt-1">Due: {formatDate(hw.due_date)}</p>
                      )}
                    </div>
                    <Button 
                      size="sm" 
                      onClick={() => onCompleteHomework(hw.id)}
                      className="rounded-xl bg-amber-500 hover:bg-amber-600 ml-3"
                    >
                      <Check size={16} className="mr-1" /> Done
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Completed Homework (collapsed) */}
          {completedHomework.length > 0 && (
            <details className="group">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1">
                <CheckCircle size={12} className="text-green-500" />
                {completedHomework.length} completed
              </summary>
              <div className="space-y-2 mt-2">
                {completedHomework.slice(0, 5).map((hw) => (
                  <Card key={hw.id} className="p-3 rounded-xl bg-gray-50">
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-500" />
                      <p className="text-sm text-gray-600 truncate">{hw.title}</p>
                    </div>
                  </Card>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      {/* ASSESSMENTS SECTION */}
      {(pendingAssessments.length > 0 || completedAssessments.length > 0) && (
        <div>
          <h3 className="text-sm font-medium text-blue-600 mb-2 flex items-center gap-2">
            <FileCheck size={16} /> Assessments
          </h3>
          
          {/* Pending Assessments */}
          {pendingAssessments.length > 0 && (
            <div className="space-y-2 mb-3">
              {pendingAssessments.map((assess) => (
                <Card 
                  key={assess.id} 
                  className="p-4 rounded-2xl border-blue-200 bg-blue-50/50 cursor-pointer hover:bg-blue-100"
                  onClick={() => onCompleteAssessment(assess)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-800">{assess.assessment_type}</p>
                      <p className="text-xs text-blue-600">Tap to complete</p>
                    </div>
                    <ChevronRight size={20} className="text-blue-400" />
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Completed Assessments (collapsed) */}
          {completedAssessments.length > 0 && (
            <details className="group">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1">
                <CheckCircle size={12} className="text-green-500" />
                {completedAssessments.length} completed
              </summary>
              <div className="space-y-2 mt-2">
                {completedAssessments.slice(0, 5).map((assess) => (
                  <Card key={assess.id} className="p-3 rounded-xl bg-gray-50">
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-500" />
                      <p className="text-sm text-gray-600 truncate">{assess.assessment_type}</p>
                    </div>
                  </Card>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      {/* RESOURCES SECTION */}
      {(unviewedResources.length > 0 || viewedResources.length > 0 || completedResources.length > 0) && (
        <div>
          <h3 className="text-sm font-medium text-emerald-600 mb-2 flex items-center gap-2">
            <BookMarked size={16} /> Resources from Therapist
          </h3>
          
          {/* New Resources */}
          {unviewedResources.length > 0 && (
            <div className="space-y-2 mb-3">
              {unviewedResources.map((resource) => {
                const Icon = getResourceIcon(resource.resource_type);
                return (
                  <Card 
                    key={resource.id} 
                    className="p-4 rounded-2xl border-emerald-200 bg-emerald-50/50 cursor-pointer hover:bg-emerald-100"
                    onClick={() => onViewResource(resource)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                        <Icon size={20} className="text-emerald-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-800 truncate">{resource.resource_title}</p>
                        <p className="text-xs text-emerald-600 capitalize">{resource.resource_type || 'Resource'}</p>
                      </div>
                      <Badge className="bg-emerald-100 text-emerald-700 text-xs">New</Badge>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}

          {/* In Progress Resources */}
          {viewedResources.length > 0 && (
            <div className="space-y-2 mb-3">
              {viewedResources.map((resource) => {
                const Icon = getResourceIcon(resource.resource_type);
                return (
                  <Card 
                    key={resource.id} 
                    className="p-3 rounded-xl cursor-pointer hover:bg-gray-50"
                    onClick={() => onViewResource(resource)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Icon size={16} className="text-blue-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-700 truncate">{resource.resource_title}</p>
                        <p className="text-xs text-gray-400">In progress</p>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Completed Resources (collapsed) */}
          {completedResources.length > 0 && (
            <details className="group">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1">
                <CheckCircle size={12} className="text-green-500" />
                {completedResources.length} completed
              </summary>
              <div className="space-y-2 mt-2">
                {completedResources.map((resource) => (
                  <Card key={resource.id} className="p-3 rounded-xl bg-gray-50" onClick={() => onViewResource(resource)}>
                    <div className="flex items-center gap-2">
                      <CheckCircle size={16} className="text-green-500" />
                      <p className="text-sm text-gray-600 truncate">{resource.resource_title}</p>
                    </div>
                  </Card>
                ))}
              </div>
            </details>
          )}
        </div>
      )}

      {/* Empty State */}
      {totalPending === 0 && homework.length === 0 && assessments.length === 0 && resources.length === 0 && (
        <Card className="p-8 rounded-2xl text-center bg-gradient-to-br from-emerald-50 to-teal-50">
          <CheckCircle size={48} className="mx-auto text-emerald-400 mb-3" />
          <p className="font-medium text-gray-700">All caught up!</p>
          <p className="text-sm text-gray-500 mt-1">No tasks assigned yet</p>
        </Card>
      )}

      {/* All Done State */}
      {totalPending === 0 && (homework.length > 0 || assessments.length > 0 || resources.length > 0) && (
        <Card className="p-6 rounded-2xl text-center bg-gradient-to-br from-green-50 to-emerald-50">
          <CheckCircle size={40} className="mx-auto text-green-500 mb-2" />
          <p className="font-medium text-green-700">Great job!</p>
          <p className="text-sm text-green-600">All pending tasks completed</p>
        </Card>
      )}
    </div>
  );
};

// ============= REPORTS TAB COMPONENT =============
const ReportsTab = ({ assessments, diagnosticReports, onViewReport }) => {
  const completed = assessments.filter(a => a.status === 'completed');
  
  return (
    <div className="space-y-4 pb-4" data-testid="reports-tab">
      <h2 className="text-lg font-semibold text-gray-800">Your Reports</h2>
      
      {/* Diagnostic Reports */}
      {diagnosticReports.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-violet-600 mb-2 flex items-center gap-2">
            <Sparkles size={14} /> Diagnostic Reports
          </h3>
          <div className="space-y-2">
            {diagnosticReports.map((report) => (
              <Card 
                key={report.id} 
                className="p-4 rounded-2xl border-violet-200 bg-violet-50/50 cursor-pointer hover:bg-violet-50"
                onClick={() => onViewReport(report.id)}
              >
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-violet-100 rounded-xl flex items-center justify-center">
                    <Sparkles size={22} className="text-violet-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800">{report.title || 'Diagnostic Report'}</p>
                    <p className="text-xs text-violet-600">{formatDate(report.created_at)}</p>
                  </div>
                  <ChevronRight size={20} className="text-violet-400" />
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Assessment Results */}
      {completed.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-blue-600 mb-2">Assessment Results</h3>
          <div className="space-y-2">
            {completed.map((assess) => (
              <Card key={assess.id} className="p-3 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileCheck size={18} className="text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 text-sm">{assess.assessment_type}</p>
                    <p className="text-xs text-gray-500">Completed {formatDate(assess.completed_at)}</p>
                  </div>
                  {assess.report_shared_with_client && (
                    <Badge className="bg-green-100 text-green-700 text-xs">Shared</Badge>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {diagnosticReports.length === 0 && completed.length === 0 && (
        <Card className="p-8 rounded-2xl text-center">
          <BarChart3 size={40} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">No reports available yet</p>
          <p className="text-sm text-gray-400 mt-1">Reports will appear here after assessments</p>
        </Card>
      )}
    </div>
  );
};

export default ClientDashboard;
