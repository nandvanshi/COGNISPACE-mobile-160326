import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { 
  LogOut, Calendar, ClipboardCheck, BookCheck, 
  FileCheck, Pen, Check, AlertCircle, Loader2, Shield, 
  CalendarPlus, Receipt, CreditCard, Clock, Settings as SettingsIcon,
  Eye, FileText, Sparkles, CheckCircle, User, MessageCircle, Send
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
  if (hour >= 5 && hour < 12) return { text: 'Good Morning', emoji: '🌱' };
  if (hour >= 12 && hour < 17) return { text: 'Good Afternoon', emoji: '☀️' };
  if (hour >= 17 && hour < 21) return { text: 'Good Evening', emoji: '🌸' };
  return { text: 'Good Night', emoji: '🌙' };
};

// ============= MOTIVATION CARD =============
const MotivationCard = ({ lastSessionDate }) => {
  const daysSinceLastSession = lastSessionDate 
    ? Math.floor((new Date() - new Date(lastSessionDate)) / (1000 * 60 * 60 * 24))
    : null;
  
  const needsGentleReminder = daysSinceLastSession && daysSinceLastSession > 14;
  
  return (
    <Card 
      className={`p-5 rounded-2xl border-0 shadow-sm ${
        needsGentleReminder 
          ? 'bg-gradient-to-br from-amber-50 to-orange-50' 
          : 'bg-gradient-to-br from-yellow-50 to-amber-50'
      }`}
      data-testid="motivation-card"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">🌼</span>
        <div>
          <h3 className="font-semibold text-amber-800 mb-1">Consistency matters</h3>
          {needsGentleReminder ? (
            <p className="text-sm text-amber-700">
              It has been {daysSinceLastSession} days since your last session. 
              Regular sessions help you feel better over time.
            </p>
          ) : (
            <p className="text-sm text-amber-700">
              Regular sessions help you feel better over time. 
              Keep up the great work on your journey!
            </p>
          )}
        </div>
      </div>
    </Card>
  );
};

const ClientDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState([]);
  const [homework, setHomework] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [therapistName, setTherapistName] = useState('');
  
  // Assessment taking state
  const [showAssessmentTaker, setShowAssessmentTaker] = useState(false);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);
  const [showSharedReport, setShowSharedReport] = useState(false);
  const [sharedReportData, setSharedReportData] = useState(null);
  
  // Consent state
  const [consentStatus, setConsentStatus] = useState({ exists: false, is_signed: false });
  const [consent, setConsent] = useState(null);
  const [consentLoading, setConsentLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [consentAgreed, setConsentAgreed] = useState(false);

  // Appointment booking state
  const [showBookingDialog, setShowBookingDialog] = useState(false);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [bookingNotes, setBookingNotes] = useState('');
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [booking, setBooking] = useState(false);

  // Receipt view state
  const [showReceiptDialog, setShowReceiptDialog] = useState(false);
  const [selectedPaymentId, setSelectedPaymentId] = useState(null);

  // Settings state
  const [showSettings, setShowSettings] = useState(false);
  
  // Messaging state
  const [showMessaging, setShowMessaging] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Diagnostic Reports state
  const [diagnosticReports, setDiagnosticReports] = useState([]);
  const [showDiagnosticReport, setShowDiagnosticReport] = useState(false);
  const [selectedDiagnosticReport, setSelectedDiagnosticReport] = useState(null);

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
      } else {
        console.error('Error checking consent:', error);
      }
    } finally {
      setConsentLoading(false);
      setLoading(false);
    }
  };

  const fetchDashboardData = async () => {
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
      
      // Fetch unread message count
      try {
        const unreadRes = await axios.get(`${API}/messages/unread-count`);
        setUnreadCount(unreadRes.data?.count || 0);
      } catch (e) { /* ignore */ }
      
      // Fetch shared diagnostic reports
      try {
        const reportsRes = await axios.get(`${API}/diagnostic-reports`);
        setDiagnosticReports(reportsRes.data || []);
      } catch (e) { /* ignore */ }
      
      // Try to get therapist name from consent or user data
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
  };

  const handleSignConsent = async () => {
    if (!consentAgreed) {
      toast.error('Please read and agree to the consent by checking the box');
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
    toast.success('Assessment completed successfully!');
  };

  const handleViewSharedReport = async (assessmentId) => {
    try {
      const res = await axios.get(`${API}/assessments/${assessmentId}/results`);
      setSharedReportData(res.data);
      setShowSharedReport(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Report not available');
    }
  };

  const handleViewDiagnosticReport = async (reportId) => {
    try {
      const res = await axios.get(`${API}/diagnostic-reports/${reportId}`);
      setSelectedDiagnosticReport(res.data);
      setShowDiagnosticReport(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Report not available');
    }
  };

  const handlePrintDiagnosticReport = () => {
    const reportContent = selectedDiagnosticReport?.report_html || selectedDiagnosticReport?.report_content;
    if (reportContent) {
      const printWindow = window.open('', '_blank');
      
      printWindow.document.write(`
<!DOCTYPE html>
<html>
<head>
  <title>Psychodiagnostic Evaluation Report</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    /* Print Settings - Remove ALL Browser Headers/Footers */
    @media print {
      @page { 
        margin: 2cm; 
        size: A4;
      }
      html, body {
        margin: 0 !important;
        padding: 0 !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
      .no-print { display: none !important; }
    }
    
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: 'Inter', Arial, sans-serif;
      font-size: 11pt;
      color: #000;
      line-height: 1.6;
      background: #fff;
      padding: 0;
    }
    
    .clinical-report {
      max-width: 210mm;
      margin: 0 auto;
      padding: 0;
    }
    
    /* Therapist Header - Navy Blue #000080 */
    .therapist-header {
      margin-bottom: 25px;
      padding-bottom: 15px;
      border-bottom: 2px solid #000080;
    }
    .therapist-header h1 {
      font-size: 18pt;
      font-weight: 700;
      margin: 0 0 5px 0;
      color: #000080;
    }
    .therapist-header p {
      margin: 3px 0;
      font-size: 10pt;
      color: #333;
      display: block;
    }
    
    /* Report Title - Navy Blue #000080 */
    .report-title {
      text-align: center;
      font-size: 16pt;
      font-weight: 600;
      letter-spacing: 2px;
      margin: 25px 0;
      color: #000080;
    }
    .report-meta {
      text-align: center;
      font-size: 9pt;
      color: #333;
      margin-bottom: 25px;
    }
    .report-meta p { margin: 3px 0; display: block; }
    
    /* Sections with Grey Dividers - Navy Blue headings */
    .report-section {
      margin-bottom: 20px;
    }
    .section-divider {
      border: none;
      border-top: 1px solid #ccc;
      margin: 20px 0 15px 0;
    }
    .section-heading {
      font-size: 12pt;
      font-weight: 600;
      color: #000080;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    /* Patient Info - Label and Value on SAME LINE */
    .patient-info p {
      margin: 6px 0;
      display: block;
      font-size: 11pt;
    }
    .patient-info strong {
      font-weight: 600;
      color: #000;
    }
    .report-content p {
      margin-bottom: 8px;
      display: block;
      text-align: justify;
    }
    
    /* Assessment Items - Clear formatting */
    .assessment-item {
      margin-bottom: 18px;
      padding: 12px;
      background: #f9f9f9;
      border-left: 3px solid #000080;
      display: block;
    }
    .assessment-item strong {
      font-size: 11pt;
      color: #000080;
      display: block;
      margin-bottom: 5px;
    }
    .assessment-item em {
      font-style: normal;
      font-weight: 600;
    }
    
    /* Recommendation Items - Clear formatting */
    .recommendation-item {
      margin-bottom: 15px;
      padding: 10px 0;
      border-bottom: 1px solid #eee;
      display: block;
    }
    .recommendation-item strong {
      font-size: 11pt;
      color: #000080;
      display: block;
      margin-bottom: 5px;
    }
    
    /* Lists - Each item on NEW LINE */
    ul, ol {
      margin: 10px 0;
      padding-left: 20px;
      list-style-position: outside;
    }
    li {
      display: list-item;
      margin-bottom: 8px;
      text-align: justify;
      padding-left: 5px;
    }
    
    /* Disclaimer */
    .disclaimer-box {
      background: #f8f9fa;
      border: 1px solid #e9ecef;
      border-radius: 4px;
      padding: 12px;
      margin: 25px 0;
      font-size: 8pt;
      color: #333;
    }
    .disclaimer-box p { margin: 5px 0; text-align: justify; display: block; }
    
    /* Signature Block */
    .signature-section {
      margin-top: 40px;
    }
    .signature-space {
      height: 60px;
      border-bottom: 1px solid #000;
      width: 180px;
      margin: 15px 0 8px 0;
    }
    .signature-name {
      font-weight: 600;
      font-size: 11pt;
      margin: 5px 0 2px 0;
      color: #000;
    }
    .signature-details {
      font-size: 9pt;
      color: #333;
      margin: 2px 0;
      display: block;
    }
    
    /* Branded Footer */
    .branded-footer {
      margin-top: 40px;
      padding-top: 15px;
      border-top: 1px solid #ddd;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .footer-logo {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .footer-logo span { font-size: 10pt; color: #666; margin-bottom: 5px; }
    .footer-logo img { height: 100px; width: auto; }
  </style>
</head>
<body>
  ${reportContent}
  
  <!-- Branded Footer - Logo Only -->
  <div class="branded-footer">
    <div class="footer-logo">
      <span>Powered by</span>
      <img src="/logo-cognispace.png" alt="Cognispace" style="height: 100px;" onerror="this.outerHTML=''" />
    </div>
  </div>
</body>
</html>
      `);
      printWindow.document.close();
      
      // Wait for fonts to load then print
      setTimeout(() => {
        printWindow.focus();
        printWindow.print();
      }, 800);
    }
  };

  // Appointment Booking Functions
  const handleOpenBooking = () => {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setBookingNotes('');
    setShowBookingDialog(true);
    fetchAvailableSlots(dateStr);
  };

  const fetchAvailableSlots = async (date) => {
    setLoadingSlots(true);
    try {
      // For clients, use the endpoint without therapist_id - backend will auto-detect from profile
      const response = await axios.get(`${API}/available-slots?date=${date}`);
      const slots = Array.isArray(response.data) ? response.data.map(s => ({
        start: s.start,
        end: s.end
      })) : [];
      setAvailableSlots(slots);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to load available slots';
      toast.error(errorMsg);
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleDateChange = (e) => {
    const date = e.target.value;
    setSelectedDate(date);
    setSelectedSlot(null);
    if (date) {
      fetchAvailableSlots(date);
    }
  };

  const handleBookAppointment = async () => {
    if (!selectedSlot) {
      toast.error('Please select a time slot');
      return;
    }

    setBooking(true);
    try {
      await axios.post(`${API}/appointments/client-request`, {
        start_time: selectedSlot.start,
        end_time: selectedSlot.end,
        notes: bookingNotes,
      });
      toast.success('Appointment request submitted!');
      setShowBookingDialog(false);
      setSelectedSlot(null);
      setBookingNotes('');
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to request appointment');
    } finally {
      setBooking(false);
    }
  };

  const handleViewReceipt = (paymentId) => {
    setSelectedPaymentId(paymentId);
    setShowReceiptDialog(true);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Handle notification navigation
  const handleNotificationNavigate = (link) => {
    if (!link) return;
    
    switch (link) {
      case 'appointments':
        setShowBookingDialog(true);
        break;
      case 'homework':
        // Scroll to homework section
        const hwSection = document.querySelector('[data-testid="homework-card"]');
        if (hwSection) hwSection.scrollIntoView({ behavior: 'smooth' });
        break;
      case 'payments':
        // Scroll to payments section
        const paySection = document.querySelector('[data-testid="payments-card"]');
        if (paySection) paySection.scrollIntoView({ behavior: 'smooth' });
        break;
      case 'reports':
        // Scroll to diagnostic reports section
        const reportsSection = document.querySelector('[data-testid="diagnostic-reports-card"]');
        if (reportsSection) reportsSection.scrollIntoView({ behavior: 'smooth' });
        break;
      case 'messages':
        setShowMessaging(true);
        break;
      default:
        console.log('Unknown navigation link:', link);
    }
  };

  // Loading state
  if (loading || consentLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50">
        <div className="text-center">
          <Loader2 className="inline-block animate-spin h-8 w-8 text-emerald-600" />
          <p className="mt-4 text-emerald-700">Loading your space...</p>
        </div>
      </div>
    );
  }

  // Consent not yet created by therapist
  if (!consentStatus.exists) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50">
        <header className="bg-white/80 backdrop-blur-lg border-b border-emerald-100">
          <div className="max-w-lg mx-auto px-4 py-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <img src="/logo-symbol.png" alt="COGNISPACE" className="h-8 w-auto" />
              <span className="text-xl font-serif text-primary">COGNISPACE</span>
            </div>
            <Button onClick={handleLogout} variant="ghost" size="sm" data-testid="client-logout-button">
              <LogOut size={18} />
            </Button>
          </div>
        </header>

        <main className="max-w-lg mx-auto p-4 pt-8">
          <Card className="p-8 bg-white rounded-3xl shadow-lg text-center border-0">
            <div className="w-16 h-16 mx-auto bg-amber-100 rounded-full flex items-center justify-center mb-6">
              <AlertCircle className="text-amber-600" size={32} />
            </div>
            <h2 className="text-2xl font-serif text-emerald-800 mb-4">Waiting for Your Therapist</h2>
            <p className="text-gray-600 mb-6">
              Your therapist is preparing your documentation. 
              Once complete, you can review and sign your consent form.
            </p>
            <p className="text-sm text-gray-500">
              Please check back later or contact your therapist.
            </p>
          </Card>
        </main>
      </div>
    );
  }

  // Consent exists but not signed
  if (!consentStatus.is_signed) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50">
        <header className="bg-white/80 backdrop-blur-lg border-b border-emerald-100">
          <div className="max-w-lg mx-auto px-4 py-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <img src="/logo-symbol.png" alt="COGNISPACE" className="h-8 w-auto" />
              <span className="text-xl font-serif text-primary">COGNISPACE</span>
            </div>
            <Button onClick={handleLogout} variant="ghost" size="sm" data-testid="client-logout-button">
              <LogOut size={18} />
            </Button>
          </div>
        </header>

        <main className="max-w-lg mx-auto p-4 pt-4">
          <Card className="bg-white rounded-3xl shadow-lg overflow-hidden border-0">
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 p-6 text-white">
              <div className="flex items-center gap-3">
                <FileCheck size={24} />
                <div>
                  <h2 className="text-xl font-serif">Informed Consent</h2>
                  <p className="text-white/80 text-sm">Please review and sign</p>
                </div>
              </div>
            </div>

            <div className="p-5">
              {consent && (
                <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-2xl mb-5">
                  <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                    <Shield className="text-emerald-600" size={18} />
                  </div>
                  <div>
                    <p className="text-xs text-emerald-600">Your Therapist</p>
                    <p className="font-medium text-emerald-800">{consent.therapist_name}</p>
                  </div>
                </div>
              )}

              <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100 max-h-[300px] overflow-y-auto mb-5">
                {consent?.consent_text?.split('\n').map((line, idx) => {
                  if (line.match(/^\d+\.\s/)) {
                    return <h3 key={idx} className="text-base font-semibold text-emerald-700 mt-3 mb-2">{line}</h3>;
                  }
                  if (line.startsWith('•') || line.startsWith('-')) {
                    return <p key={idx} className="ml-3 text-gray-600 text-sm">{line}</p>;
                  }
                  if (line.includes('INFORMED CONSENT')) {
                    return <h2 key={idx} className="text-lg font-bold text-center text-emerald-700 mb-3">{line}</h2>;
                  }
                  if (!line.trim()) return <div key={idx} className="h-2" />;
                  return <p key={idx} className="text-gray-700 text-sm">{line}</p>;
                })}
              </div>

              <div className="bg-emerald-50 p-4 rounded-2xl border border-emerald-100 mb-5">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="consent-agree"
                    checked={consentAgreed}
                    onCheckedChange={setConsentAgreed}
                    className="mt-0.5"
                    data-testid="consent-agree-checkbox"
                  />
                  <label htmlFor="consent-agree" className="text-sm cursor-pointer text-emerald-800">
                    I have read, understood, and agree to the terms above.
                  </label>
                </div>
              </div>

              <Button
                onClick={handleSignConsent}
                disabled={signing || !consentAgreed}
                className="w-full py-5 text-base rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                data-testid="sign-consent-button"
              >
                {signing ? (
                  <><Loader2 className="animate-spin mr-2" size={18} /> Signing...</>
                ) : (
                  <><Pen className="mr-2" size={18} /> Sign Consent</>
                )}
              </Button>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  // CONSENT SIGNED - Show full dashboard
  const greeting = getGreeting();
  const upcomingAppointments = appointments
    .filter((a) => new Date(a.start_time) > new Date() && a.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
    .slice(0, 3);

  const pendingHomework = homework.filter((h) => h.status === 'assigned');
  const completedHomework = homework.filter((h) => h.status === 'completed').slice(0, 3);
  const recentPayments = payments.slice(0, 3);
  
  // Get last session date for motivation card
  const pastSessions = appointments
    .filter((a) => new Date(a.start_time) < new Date() && a.status !== 'cancelled')
    .sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
  const lastSessionDate = pastSessions.length > 0 ? pastSessions[0].start_time : null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50 pb-8">
      {/* Header - Minimal */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-emerald-100 sticky top-0 z-40">
        <div className="max-w-lg mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <img src="/logo-symbol.png" alt="COGNISPACE" className="h-7 w-auto" />
            <span className="font-serif text-lg text-primary">COGNISPACE</span>
          </div>
          <div className="flex items-center gap-1">
            <NotificationBell onNavigate={handleNotificationNavigate} />
            <Button onClick={() => setShowSettings(true)} variant="ghost" size="sm" className="p-2" data-testid="client-settings-button">
              <SettingsIcon size={18} className="text-gray-500" />
            </Button>
            <Button onClick={handleLogout} variant="ghost" size="sm" className="p-2" data-testid="client-logout-button">
              <LogOut size={18} className="text-gray-500" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content - Single Column Mobile Layout */}
      <main className="max-w-lg mx-auto px-4 pt-6 space-y-5">
        
        {/* Greeting Header with Gradient */}
        <div 
          className="rounded-3xl p-6 text-white"
          style={{ background: 'linear-gradient(135deg, #059669 0%, #0d9488 50%, #0ea5e9 100%)' }}
          data-testid="greeting-header"
        >
          <h1 className="text-2xl font-serif mb-1">
            {greeting.text}, {user?.full_name?.split(' ')[0]} {greeting.emoji}
          </h1>
          <p className="text-white/80 text-sm mb-4">How are you feeling today?</p>
          
          {therapistName && (
            <div className="flex items-center gap-2 bg-white/20 rounded-xl px-3 py-2 mt-3">
              <User size={16} className="text-white/80" />
              <span className="text-sm text-white/90">Your Therapist: {therapistName}</span>
            </div>
          )}
        </div>

        {/* Primary CTA - Request Appointment */}
        <div className="text-center">
          <Button 
            onClick={handleOpenBooking}
            className="w-full py-6 text-base rounded-2xl bg-emerald-700 hover:bg-emerald-800 shadow-lg shadow-emerald-200"
            data-testid="request-appointment-button"
          >
            <CalendarPlus size={20} className="mr-2" /> Request Appointment
          </Button>
          <p className="text-xs text-gray-500 mt-2">
            Your appointment request will be reviewed and confirmed soon.
          </p>
        </div>
        
        {/* Message Therapist Card */}
        <Card 
          className="p-4 bg-white rounded-2xl border-0 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => setShowMessaging(true)}
          data-testid="message-therapist-card"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <MessageCircle className="text-blue-600" size={20} />
              </div>
              <div>
                <h3 className="font-medium text-gray-800">Message Your Therapist</h3>
                <p className="text-xs text-gray-500">Send a message anytime</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <Badge className="bg-red-500 text-white border-0 text-xs px-2 py-0.5">
                  {unreadCount} new
                </Badge>
              )}
              <Send size={18} className="text-gray-400" />
            </div>
          </div>
        </Card>

        {/* Motivation Card */}
        <MotivationCard lastSessionDate={lastSessionDate} />

        {/* Upcoming Appointments Section */}
        <Card className="p-5 bg-white rounded-3xl border-0 shadow-sm" data-testid="upcoming-appointments-card">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="text-emerald-600" size={20} />
            <h3 className="text-lg font-semibold text-gray-800">Upcoming Sessions</h3>
          </div>
          
          {upcomingAppointments.length === 0 ? (
            <div className="p-6 bg-gray-50 rounded-2xl text-center">
              <Calendar className="mx-auto text-gray-300 mb-2" size={32} />
              <p className="text-sm text-gray-500">No upcoming sessions scheduled</p>
              <p className="text-xs text-gray-400 mt-1">Request an appointment to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingAppointments.map((appt) => (
                <div
                  key={appt.id}
                  className="p-4 bg-sky-50 rounded-2xl border border-sky-100"
                  data-testid={`appointment-${appt.id}`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-sky-900">{formatDate(appt.start_time)}</p>
                      <p className="text-sm text-sky-700 flex items-center gap-1 mt-1">
                        <Clock size={14} /> {formatTime(appt.start_time)} - {formatTime(appt.end_time)}
                      </p>
                    </div>
                    <Badge className="bg-sky-100 text-sky-700 border-0">
                      {appt.status === 'in_progress' ? 'In Progress' : 'Scheduled'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Homework Section */}
        <Card className="p-5 bg-white rounded-3xl border-0 shadow-sm" data-testid="homework-card">
          <div className="flex items-center gap-2 mb-4">
            <BookCheck className="text-emerald-600" size={20} />
            <h3 className="text-lg font-semibold text-gray-800">Homework</h3>
          </div>
          
          {pendingHomework.length === 0 && completedHomework.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No homework assigned yet</p>
          ) : (
            <div className="space-y-3">
              {/* Pending Homework - Light Orange */}
              {pendingHomework.map((hw) => (
                <div 
                  key={hw.id} 
                  className="p-4 bg-orange-50 rounded-2xl border border-orange-100"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h4 className="font-medium text-orange-900">{hw.title}</h4>
                      <p className="text-sm text-orange-700 mt-1 line-clamp-2">{hw.description}</p>
                      {hw.due_date && (
                        <p className="text-xs text-orange-600 mt-2">
                          Due: {formatDate(hw.due_date)}
                        </p>
                      )}
                    </div>
                    <Badge className="bg-orange-100 text-orange-700 border-0 text-xs">Pending</Badge>
                  </div>
                  <Button
                    onClick={() => handleCompleteHomework(hw.id)}
                    size="sm"
                    className="mt-3 w-full bg-orange-600 hover:bg-orange-700 rounded-xl"
                    data-testid={`complete-homework-${hw.id}`}
                  >
                    Mark Complete
                  </Button>
                </div>
              ))}
              
              {/* Completed Homework - Soft Green */}
              {completedHomework.map((hw) => (
                <div 
                  key={hw.id} 
                  className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2">
                      <CheckCircle className="text-emerald-600 mt-0.5 flex-shrink-0" size={18} />
                      <div>
                        <h4 className="font-medium text-emerald-800">{hw.title}</h4>
                        <p className="text-xs text-emerald-600 mt-1">
                          Completed: {formatDate(hw.completed_at || hw.updated_at)}
                        </p>
                      </div>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">Done</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Assessments Section */}
        <Card className="p-5 bg-white rounded-3xl border-0 shadow-sm" data-testid="assessments-card">
          <div className="flex items-center gap-2 mb-4">
            <ClipboardCheck className="text-emerald-600" size={20} />
            <h3 className="text-lg font-semibold text-gray-800">Assessments</h3>
          </div>
          
          {assessments.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No assessments assigned</p>
          ) : (
            <div className="space-y-3">
              {/* Pending Assessments */}
              {assessments.filter(a => a.status === 'assigned').map((assess) => (
                <div key={assess.id} className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <p className="font-medium text-gray-800">{assess.assessment_type}</p>
                      {assess.due_date && (
                        <p className="text-xs text-gray-500 mt-1">Due: {formatDate(assess.due_date)}</p>
                      )}
                    </div>
                    <Badge className="bg-gray-100 text-gray-600 border-0 text-xs">Pending</Badge>
                  </div>
                  <Button
                    onClick={() => handleCompleteAssessment(assess)}
                    size="sm"
                    className="mt-3 w-full rounded-xl"
                    data-testid={`complete-assessment-${assess.id}`}
                  >
                    Start Assessment
                  </Button>
                </div>
              ))}
              
              {/* Completed Assessments */}
              {assessments.filter(a => a.status === 'completed').slice(0, 3).map((assess) => (
                <div key={assess.id} className="p-4 bg-gray-50 rounded-2xl border border-gray-100">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <p className="font-medium text-gray-800">{assess.assessment_type}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Completed: {assess.completed_at ? formatDate(assess.completed_at) : 'N/A'}
                      </p>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs">Completed</Badge>
                  </div>
                  {assess.report_shared_with_client && (
                    <Button
                      onClick={() => handleViewSharedReport(assess.id)}
                      size="sm"
                      variant="outline"
                      className="mt-3 w-full rounded-xl"
                      data-testid={`view-report-${assess.id}`}
                    >
                      <Eye size={14} className="mr-1" /> View Report
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Payments Section - Minimal & Soft */}
        <Card className="p-5 bg-white rounded-3xl border-0 shadow-sm" data-testid="payments-card">
          <div className="flex items-center gap-2 mb-4">
            <CreditCard className="text-gray-400" size={20} />
            <h3 className="text-lg font-semibold text-gray-600">Payment History</h3>
          </div>
          
          {recentPayments.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-4">No payment records</p>
          ) : (
            <div className="space-y-2">
              {recentPayments.map((payment) => (
                <div 
                  key={payment.id} 
                  className="p-3 bg-gray-50 rounded-xl flex justify-between items-center"
                >
                  <div>
                    <p className="font-medium text-gray-700 text-sm">{formatCurrency(payment.amount)}</p>
                    <p className="text-xs text-gray-400">{formatDate(payment.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-500 capitalize">
                      {payment.payment_status}
                    </span>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="p-1.5"
                      onClick={() => handleViewReceipt(payment.id)}
                      data-testid={`view-receipt-${payment.id}`}
                    >
                      <Receipt size={14} className="text-gray-400" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* My Diagnostic Reports Section */}
        {diagnosticReports.length > 0 && (
          <Card className="p-5 bg-gradient-to-br from-violet-50 to-purple-50 rounded-3xl border-violet-100 shadow-sm" data-testid="diagnostic-reports-card">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 bg-violet-100 rounded-lg">
                <Sparkles className="text-violet-600" size={18} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-violet-800">My Diagnostic Reports</h3>
                <p className="text-xs text-violet-600">Professional assessment reports from your therapist</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {diagnosticReports.map((report) => (
                <div 
                  key={report.id} 
                  className="p-4 bg-white rounded-2xl border border-violet-100 hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start gap-3">
                    <div className="flex-1">
                      <p className="font-semibold text-violet-900">{report.title || 'Diagnostic Report'}</p>
                      <p className="text-xs text-violet-600 mt-1">
                        Generated: {report.created_at ? formatDate(report.created_at) : 'N/A'}
                      </p>
                      {report.shared_at && (
                        <p className="text-xs text-emerald-600 mt-0.5">
                          Shared: {formatDate(report.shared_at)}
                        </p>
                      )}
                    </div>
                    <Badge className="bg-violet-100 text-violet-700 border-0 text-xs flex-shrink-0">
                      <FileText size={12} className="mr-1" /> Report
                    </Badge>
                  </div>
                  <Button
                    onClick={() => handleViewDiagnosticReport(report.id)}
                    size="sm"
                    className="mt-3 w-full rounded-xl bg-violet-600 hover:bg-violet-700"
                    data-testid={`view-diagnostic-report-${report.id}`}
                  >
                    <Eye size={14} className="mr-1" /> View Full Report
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Support Note */}
        <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100">
          <p className="text-xs text-emerald-700 text-center">
            Need support? Reach out to your therapist anytime. We are here for you. 💚
          </p>
        </div>
      </main>

      {/* Request Appointment Dialog */}
      <Dialog open={showBookingDialog} onOpenChange={setShowBookingDialog}>
        <DialogContent className="max-w-md mx-4 rounded-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <CalendarPlus size={20} /> Request an Appointment
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label className="text-gray-700">Select Date</Label>
              <Input
                type="date"
                value={selectedDate}
                onChange={handleDateChange}
                min={new Date().toISOString().split('T')[0]}
                className="mt-1 rounded-xl"
              />
            </div>

            {selectedDate && (
              <div>
                <Label className="mb-2 block text-gray-700">Available Time Slots</Label>
                {loadingSlots ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="animate-spin text-emerald-600" size={24} />
                  </div>
                ) : availableSlots.length > 0 ? (
                  <div className="grid grid-cols-3 gap-2 max-h-[180px] overflow-y-auto">
                    {availableSlots.map((slot, idx) => (
                      <Button
                        key={idx}
                        type="button"
                        variant={selectedSlot?.start === slot.start ? 'default' : 'outline'}
                        size="sm"
                        className={`text-xs rounded-xl ${
                          selectedSlot?.start === slot.start 
                            ? 'bg-emerald-600' 
                            : 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                        }`}
                        onClick={() => setSelectedSlot(slot)}
                      >
                        {formatTime(slot.start)}
                      </Button>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm text-center py-4">
                    No available slots for this date.
                  </p>
                )}
              </div>
            )}

            {selectedSlot && (
              <div className="p-3 bg-emerald-50 rounded-xl text-sm border border-emerald-100">
                <p className="font-medium text-emerald-700">
                  Selected: {formatDate(selectedSlot.start)} at {formatTime(selectedSlot.start)}
                </p>
              </div>
            )}

            <div>
              <Label className="text-gray-700">Notes (optional)</Label>
              <Textarea
                value={bookingNotes}
                onChange={(e) => setBookingNotes(e.target.value)}
                placeholder="What would you like to discuss?"
                rows={2}
                className="mt-1 rounded-xl"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <Button 
                onClick={handleBookAppointment} 
                disabled={!selectedSlot || booking}
                className="flex-1 rounded-xl bg-emerald-700 hover:bg-emerald-800"
              >
                {booking ? (
                  <><Loader2 className="animate-spin mr-2" size={16} /> Requesting...</>
                ) : (
                  'Request Appointment'
                )}
              </Button>
              <Button variant="outline" onClick={() => setShowBookingDialog(false)} className="rounded-xl">
                Cancel
              </Button>
            </div>
            
            <p className="text-xs text-gray-400 text-center">
              Your therapist will confirm your appointment request.
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Receipt View Dialog */}
      <PaymentReceiptView
        paymentId={selectedPaymentId}
        isOpen={showReceiptDialog}
        onClose={() => setShowReceiptDialog(false)}
      />

      {/* Settings Dialog */}
      <Settings isOpen={showSettings} onClose={() => setShowSettings(false)} />

      {/* Assessment Taker Dialog */}
      <Dialog open={showAssessmentTaker} onOpenChange={(open) => {
        if (!open) {
          setShowAssessmentTaker(false);
          setSelectedAssessmentId(null);
        }
      }}>
        <DialogContent className="max-w-2xl max-h-[95vh] overflow-y-auto p-0 rounded-3xl" data-testid="assessment-taker-dialog">
          {selectedAssessmentId && (
            <ClientAssessmentTaker
              assessmentId={selectedAssessmentId}
              onComplete={handleAssessmentComplete}
              onCancel={() => {
                setShowAssessmentTaker(false);
                setSelectedAssessmentId(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Shared Report View Dialog */}
      <Dialog open={showSharedReport} onOpenChange={setShowSharedReport}>
        <DialogContent className="max-w-lg rounded-3xl" data-testid="shared-report-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-700">
              <FileText size={20} /> Assessment Report
            </DialogTitle>
          </DialogHeader>
          {sharedReportData && (
            <div className="space-y-4">
              <div>
                <p className="text-lg font-medium text-gray-800">{sharedReportData.assessment_type}</p>
                <p className="text-sm text-gray-500">
                  Completed: {sharedReportData.completed_at ? formatDate(sharedReportData.completed_at) : 'N/A'}
                </p>
              </div>

              {sharedReportData.therapist_notes && (
                <div>
                  <p className="text-sm font-medium mb-2 text-gray-700">Notes from Your Therapist</p>
                  <Card className="p-4 bg-emerald-50 border-emerald-100 rounded-2xl">
                    <p className="text-sm text-emerald-800">{sharedReportData.therapist_notes}</p>
                  </Card>
                </div>
              )}

              <Card className="p-4 bg-amber-50 border-amber-100 rounded-2xl">
                <p className="text-sm text-amber-800">
                  <AlertCircle className="w-4 h-4 inline mr-2" />
                  Please discuss this report with your therapist for guidance.
                </p>
              </Card>

              <Button onClick={() => setShowSharedReport(false)} className="w-full rounded-xl bg-emerald-700">
                Close
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* Messaging Dialog */}
      <Dialog open={showMessaging} onOpenChange={setShowMessaging}>
        <DialogContent className="max-w-2xl h-[80vh] p-0 rounded-3xl overflow-hidden" data-testid="messaging-dialog">
          <Messaging />
        </DialogContent>
      </Dialog>

      {/* Diagnostic Report View Dialog */}
      <Dialog open={showDiagnosticReport} onOpenChange={setShowDiagnosticReport}>
        <DialogContent className="max-w-4xl max-h-[95vh] overflow-hidden p-0 rounded-3xl" data-testid="diagnostic-report-dialog">
          <DialogHeader className="p-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white">
            <DialogTitle className="flex items-center gap-2">
              <Sparkles size={20} /> 
              <span>Diagnostic Report</span>
            </DialogTitle>
          </DialogHeader>
          
          {selectedDiagnosticReport && (
            <div className="flex flex-col h-[calc(95vh-120px)]">
              {/* Report Info Bar */}
              <div className="px-4 py-2 bg-violet-50 border-b border-violet-100 flex justify-between items-center flex-shrink-0">
                <div>
                  <p className="font-semibold text-violet-900">{selectedDiagnosticReport.title || 'Diagnostic Report'}</p>
                  <p className="text-xs text-violet-600">
                    Generated: {selectedDiagnosticReport.created_at ? formatDate(selectedDiagnosticReport.created_at) : 'N/A'}
                  </p>
                </div>
                <Button
                  onClick={handlePrintDiagnosticReport}
                  size="sm"
                  variant="outline"
                  className="rounded-xl border-violet-300 text-violet-700 hover:bg-violet-100"
                  data-testid="print-diagnostic-report"
                >
                  <FileText size={14} className="mr-1" /> Download PDF
                </Button>
              </div>
              
              {/* Report Content - HTML rendered */}
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
              
              {/* Footer */}
              <div className="p-4 bg-white border-t flex-shrink-0">
                <Card className="p-3 bg-amber-50 border-amber-100 rounded-xl mb-3">
                  <p className="text-xs text-amber-800">
                    <AlertCircle className="w-3 h-3 inline mr-1" />
                    This report is for informational purposes. Please discuss findings with your therapist.
                  </p>
                </Card>
                <Button 
                  onClick={() => setShowDiagnosticReport(false)} 
                  className="w-full rounded-xl bg-violet-600 hover:bg-violet-700"
                >
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

export default ClientDashboard;
