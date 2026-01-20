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
  LogOut, Calendar, MessageSquare, ClipboardCheck, BookCheck, 
  FileCheck, Pen, Check, AlertCircle, Loader2, Shield, 
  CalendarPlus, Receipt, CreditCard, Clock, ChevronRight, Settings as SettingsIcon,
  Eye, FileText
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDate, formatTime, formatCurrency } from '../utils/formatUtils';
import { PaymentReceiptView } from '../components/PaymentReceipt';
import Settings from '../components/Settings';
import ClientAssessmentTaker from '../components/ClientAssessmentTaker';

const ClientDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState([]);
  const [homework, setHomework] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  
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
      const response = await axios.get(`${API}/available-slots/${user?.therapist_id}?date=${date}`);
      // API returns array directly, transform to {start, end} format
      const slots = Array.isArray(response.data) ? response.data.map(s => ({
        start: s.start_time,
        end: s.end_time
      })) : [];
      setAvailableSlots(slots);
    } catch (error) {
      toast.error('Failed to load available slots');
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
      toast.success('Appointment booked successfully!');
      setShowBookingDialog(false);
      setSelectedSlot(null);
      setBookingNotes('');
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to book appointment');
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

  // Loading state
  if (loading || consentLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="text-center">
          <Loader2 className="inline-block animate-spin h-8 w-8 text-primary" />
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Consent not yet created by therapist
  if (!consentStatus.exists) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <header className="bg-white/80 backdrop-blur-lg border-b border-border/40">
          <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-serif text-primary">TheraGenie</h1>
              <p className="text-sm text-muted-foreground">Welcome, {user?.full_name}</p>
            </div>
            <Button onClick={handleLogout} variant="ghost" data-testid="client-logout-button">
              <LogOut size={20} className="mr-2" /> Logout
            </Button>
          </div>
        </header>

        <main className="max-w-2xl mx-auto p-6 md:p-12">
          <Card className="p-8 bg-white/80 backdrop-blur-xl border border-border/40 rounded-2xl shadow-xl text-center">
            <div className="w-16 h-16 mx-auto bg-amber-100 rounded-full flex items-center justify-center mb-6">
              <AlertCircle className="text-amber-600" size={32} />
            </div>
            <h2 className="text-2xl font-serif text-primary mb-4">Waiting for Your Therapist</h2>
            <p className="text-muted-foreground mb-6">
              Your therapist is preparing your case history and consent documentation. 
              Once complete, you&apos;ll be able to review and sign your informed consent for therapy.
            </p>
            <p className="text-sm text-muted-foreground">
              Please check back later or contact your therapist if you have questions.
            </p>
          </Card>
        </main>
      </div>
    );
  }

  // Consent exists but not signed - SHOW CONSENT FORM
  if (!consentStatus.is_signed) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <header className="bg-white/80 backdrop-blur-lg border-b border-border/40">
          <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-serif text-primary">TheraGenie</h1>
              <p className="text-sm text-muted-foreground">Welcome, {user?.full_name}</p>
            </div>
            <Button onClick={handleLogout} variant="ghost" data-testid="client-logout-button">
              <LogOut size={20} className="mr-2" /> Logout
            </Button>
          </div>
        </header>

        <main className="max-w-3xl mx-auto p-6 md:p-12">
          <Card className="bg-white/80 backdrop-blur-xl border border-border/40 rounded-2xl shadow-xl overflow-hidden">
            <div className="bg-gradient-to-r from-primary to-primary/80 p-6 text-white">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <FileCheck size={24} />
                </div>
                <div>
                  <h2 className="text-2xl font-serif">Informed Consent</h2>
                  <p className="text-white/80 text-sm">Please review and sign to begin your therapy journey</p>
                </div>
              </div>
            </div>

            <div className="p-6 md:p-8">
              {consent && (
                <div className="flex items-center gap-4 p-4 bg-muted/30 rounded-lg mb-6">
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                    <Shield className="text-primary" size={20} />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Your Therapist</p>
                    <p className="font-medium">{consent.therapist_name}</p>
                  </div>
                </div>
              )}

              <div className="prose prose-sm max-w-none mb-8">
                <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 max-h-[400px] overflow-y-auto">
                  {consent?.consent_text?.split('\n').map((line, idx) => {
                    if (line.match(/^\d+\.\s/)) {
                      return <h3 key={idx} className="text-lg font-semibold text-primary mt-4 mb-2">{line}</h3>;
                    }
                    if (line.startsWith('•') || line.startsWith('-')) {
                      return <p key={idx} className="ml-4 text-slate-600">{line}</p>;
                    }
                    if (line.startsWith('  -')) {
                      return <p key={idx} className="ml-8 text-slate-500 text-sm">{line}</p>;
                    }
                    if (line.includes('INFORMED CONSENT')) {
                      return <h2 key={idx} className="text-xl font-bold text-center text-primary mb-4">{line}</h2>;
                    }
                    if (line.startsWith('Client Name:') || line.startsWith('Therapist Name:') || line.startsWith('Date:')) {
                      return <p key={idx} className="text-sm text-slate-500">{line}</p>;
                    }
                    if (!line.trim()) {
                      return <div key={idx} className="h-2" />;
                    }
                    return <p key={idx} className="text-slate-700">{line}</p>;
                  })}
                </div>
              </div>

              <div className="bg-primary/5 p-4 rounded-xl border border-primary/20 mb-6">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="consent-agree"
                    checked={consentAgreed}
                    onCheckedChange={setConsentAgreed}
                    className="mt-1"
                    data-testid="consent-agree-checkbox"
                  />
                  <label htmlFor="consent-agree" className="text-sm cursor-pointer">
                    <span className="font-semibold text-primary">Client Consent Declaration</span>
                    <br />
                    <span className="text-slate-600">
                      I hereby confirm that I have read, understood, and agree to the terms described above 
                      and provide my informed consent to participate in psychotherapy.
                    </span>
                  </label>
                </div>
              </div>

              <Button
                onClick={handleSignConsent}
                disabled={signing || !consentAgreed}
                className="w-full py-6 text-lg bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                data-testid="sign-consent-button"
              >
                {signing ? (
                  <>
                    <Loader2 className="animate-spin mr-2" size={20} />
                    Signing...
                  </>
                ) : (
                  <>
                    <Pen className="mr-2" size={20} />
                    Sign Consent Digitally
                  </>
                )}
              </Button>

              <p className="text-xs text-center text-muted-foreground mt-4">
                By clicking &quot;Sign Consent Digitally&quot;, you are providing your electronic signature 
                which has the same legal effect as a handwritten signature.
              </p>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  // CONSENT SIGNED - Show full dashboard
  const upcomingAppointments = appointments
    .filter((a) => new Date(a.start_time) > new Date() && a.status !== 'cancelled')
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
    .slice(0, 3);

  const pendingHomework = homework.filter((h) => h.status === 'assigned');
  const recentPayments = payments.slice(0, 3);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-border/40 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <div className="min-w-0 flex-1">
            <h1 className="text-xl sm:text-2xl font-serif text-primary">TheraGenie</h1>
            <p className="text-xs sm:text-sm text-muted-foreground truncate">Welcome, {user?.full_name}</p>
          </div>
          <div className="flex items-center gap-1 sm:gap-3 flex-shrink-0">
            <span className="hidden sm:flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
              <Check size={12} /> Consent Signed
            </span>
            <Button onClick={() => setShowSettings(true)} variant="ghost" size="sm" className="p-2" data-testid="client-settings-button">
              <SettingsIcon size={18} />
            </Button>
            <Button onClick={handleLogout} variant="ghost" size="sm" className="p-2 sm:px-3" data-testid="client-logout-button">
              <LogOut size={18} />
              <span className="hidden sm:inline ml-2">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-12">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6 sm:mb-8">
          <div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif text-primary mb-1 sm:mb-2">Your Dashboard</h2>
            <p className="text-sm text-muted-foreground">Manage your therapy journey</p>
          </div>
          <Button 
            onClick={handleOpenBooking}
            className="bg-gradient-to-r from-primary to-primary/80 w-full sm:w-auto"
            data-testid="book-appointment-button"
          >
            <CalendarPlus size={18} className="mr-2" /> Book Appointment
          </Button>
        </div>

        {/* Bento Grid Layout - Mobile optimized */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
          {/* Upcoming Appointments - Span 8 cols on lg */}
          <Card className="lg:col-span-8 p-4 sm:p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="upcoming-appointments-card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 sm:gap-3">
                <Calendar className="text-primary" size={20} />
                <h3 className="text-lg sm:text-xl lg:text-2xl font-serif text-primary">Upcoming</h3>
              </div>
              <Button variant="ghost" size="sm" onClick={handleOpenBooking} className="text-xs sm:text-sm">
                <CalendarPlus size={14} className="mr-1" /> Book
              </Button>
            </div>
            {upcomingAppointments.length === 0 ? (
              <div className="text-center py-6 sm:py-8">
                <Calendar className="mx-auto text-muted-foreground mb-3" size={32} />
                <p className="text-sm text-muted-foreground mb-4">No upcoming appointments</p>
                <Button onClick={handleOpenBooking} variant="outline" size="sm">
                  <CalendarPlus size={14} className="mr-2" /> Schedule Now
                </Button>
              </div>
            ) : (
              <div className="space-y-2 sm:space-y-3">
                {upcomingAppointments.map((appt) => (
                  <div
                    key={appt.id}
                    className="p-3 sm:p-4 bg-surface rounded-lg border border-border hover:border-primary/50 transition-colors"
                    data-testid={`appointment-${appt.id}`}
                  >
                    <div className="flex justify-between items-start sm:items-center gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-sm sm:text-base lg:text-lg">
                          {formatDate(appt.start_time)}
                        </p>
                        <p className="text-xs sm:text-sm text-muted-foreground flex items-center gap-1">
                          <Clock size={12} /> {formatTime(appt.start_time)} - {formatTime(appt.end_time)}
                        </p>
                      </div>
                      <span className={`text-[10px] sm:text-xs px-2 py-1 rounded-full flex-shrink-0 ${
                        appt.status === 'scheduled' ? 'bg-blue-100 text-blue-700' :
                        appt.status === 'in_progress' ? 'bg-amber-100 text-amber-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {appt.status === 'in_progress' ? 'In Progress' : 'Scheduled'}
                      </span>
                    </div>
                    {appt.notes && <p className="text-xs sm:text-sm text-muted-foreground mt-2 line-clamp-2">{appt.notes}</p>}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Pending Assessments - Span 4 cols on lg */}
          <Card className="lg:col-span-4 p-4 sm:p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="pending-assessments-card">
            <div className="flex items-center gap-2 sm:gap-3 mb-4">
              <ClipboardCheck className="text-secondary" size={20} />
              <h3 className="text-lg sm:text-xl font-serif text-primary">Assessments</h3>
            </div>
            {assessments.length === 0 ? (
              <p className="text-xs sm:text-sm text-muted-foreground">No assessments assigned</p>
            ) : (
              <div className="space-y-2">
                {/* Pending Assessments */}
                {assessments.filter(a => a.status === 'assigned').map((assess) => (
                  <div key={assess.id} className="p-3 bg-surface rounded-lg border border-border hover:border-primary/30 transition-colors">
                    <div className="flex justify-between items-start gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-sm">{assess.assessment_type}</p>
                        {assess.due_date && (
                          <p className="text-[10px] text-muted-foreground mt-1">
                            Due: {formatDate(assess.due_date)}
                          </p>
                        )}
                      </div>
                      <Badge variant="outline" className="bg-amber-50 text-amber-700 text-[10px]">
                        Pending
                      </Badge>
                    </div>
                    <Button
                      onClick={() => handleCompleteAssessment(assess)}
                      size="sm"
                      className="mt-2 w-full text-xs"
                      data-testid={`complete-assessment-${assess.id}`}
                    >
                      Start Assessment
                    </Button>
                  </div>
                ))}
                
                {/* Completed Assessments with View Report option */}
                {assessments.filter(a => a.status === 'completed').slice(0, 3).map((assess) => (
                  <div key={assess.id} className="p-3 bg-surface rounded-lg border border-border">
                    <div className="flex justify-between items-start gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-sm">{assess.assessment_type}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          Completed: {assess.completed_at ? formatDate(assess.completed_at) : 'N/A'}
                        </p>
                      </div>
                      <Badge className="bg-success/10 text-success text-[10px]">
                        Done
                      </Badge>
                    </div>
                    {assess.report_shared_with_client && (
                      <Button
                        onClick={() => handleViewSharedReport(assess.id)}
                        size="sm"
                        variant="outline"
                        className="mt-2 w-full text-xs"
                        data-testid={`view-report-${assess.id}`}
                      >
                        <Eye size={12} className="mr-1" /> View Report
                      </Button>
                    )}
                  </div>
                ))}

                {assessments.filter(a => a.status === 'assigned').length === 0 && assessments.filter(a => a.status === 'completed').length > 0 && (
                  <p className="text-xs text-muted-foreground text-center py-2">No pending assessments</p>
                )}
              </div>
            )}
          </Card>

          {/* Homework - Span 6 cols on lg */}
          <Card className="lg:col-span-6 p-4 sm:p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="homework-card">
            <div className="flex items-center gap-2 sm:gap-3 mb-4">
              <BookCheck className="text-info" size={20} />
              <h3 className="text-lg sm:text-xl lg:text-2xl font-serif text-primary">Homework</h3>
            </div>
            {pendingHomework.length === 0 ? (
              <p className="text-sm text-muted-foreground">No pending homework</p>
            ) : (
              <div className="space-y-2 sm:space-y-3">
                {pendingHomework.map((hw) => (
                  <div key={hw.id} className="p-3 sm:p-4 bg-surface rounded-lg border border-border">
                    <h4 className="font-medium text-sm sm:text-base">{hw.title}</h4>
                    <p className="text-xs sm:text-sm text-muted-foreground mt-1 line-clamp-2">{hw.description}</p>
                    {hw.due_date && (
                      <p className="text-[10px] sm:text-xs text-warning mt-2">
                        Due: {formatDate(hw.due_date)}
                      </p>
                    )}
                    <Button
                      onClick={() => handleCompleteHomework(hw.id)}
                      size="sm"
                      className="mt-2 sm:mt-3 text-xs"
                      data-testid={`complete-homework-${hw.id}`}
                    >
                      Mark Complete
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Payments - Span 6 cols on lg */}
          <Card className="lg:col-span-6 p-4 sm:p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="payments-card">
            <div className="flex items-center gap-2 sm:gap-3 mb-4">
              <CreditCard className="text-success" size={20} />
              <h3 className="text-lg sm:text-xl lg:text-2xl font-serif text-primary">Payments</h3>
            </div>
            {recentPayments.length === 0 ? (
              <p className="text-sm text-muted-foreground">No payment records</p>
            ) : (
              <div className="space-y-2 sm:space-y-3">
                {recentPayments.map((payment) => (
                  <div key={payment.id} className="p-3 sm:p-4 bg-surface rounded-lg border border-border flex justify-between items-start sm:items-center gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm sm:text-base">{formatCurrency(payment.amount)}</p>
                      <p className="text-[10px] sm:text-sm text-muted-foreground">
                        {formatDate(payment.created_at)} • {payment.payment_method?.toUpperCase()}
                      </p>
                      {payment.bill_number && (
                        <p className="text-[10px] sm:text-xs text-muted-foreground truncate">Bill #: {payment.bill_number}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                      <span className={`text-[10px] sm:text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full capitalize ${
                        payment.payment_status === 'paid' ? 'bg-green-100 text-green-700' :
                        payment.payment_status === 'partial' ? 'bg-amber-100 text-amber-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {payment.payment_status}
                      </span>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="p-1 sm:p-2"
                        onClick={() => handleViewReceipt(payment.id)}
                        data-testid={`view-receipt-${payment.id}`}
                      >
                        <Receipt size={14} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Disclaimer */}
        <div className="mt-8 sm:mt-12 p-4 sm:p-6 bg-info/10 border border-info/20 rounded-xl">
          <p className="text-xs sm:text-sm text-info">
            <strong>Clinical Support Only:</strong> This platform provides tools to support your therapy journey.
            All clinical decisions and treatment plans are made by your licensed therapist.
          </p>
        </div>
      </main>

      {/* Appointment Booking Dialog */}
      <Dialog open={showBookingDialog} onOpenChange={setShowBookingDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CalendarPlus size={20} /> Book an Appointment
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Select Date</Label>
              <Input
                type="date"
                value={selectedDate}
                onChange={handleDateChange}
                min={new Date().toISOString().split('T')[0]}
                className="mt-1"
              />
            </div>

            {selectedDate && (
              <div>
                <Label className="mb-2 block">Available Time Slots</Label>
                {loadingSlots ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="animate-spin text-primary" size={24} />
                  </div>
                ) : availableSlots.length > 0 ? (
                  <div className="grid grid-cols-3 gap-2 max-h-[200px] overflow-y-auto">
                    {availableSlots.map((slot, idx) => (
                      <Button
                        key={idx}
                        type="button"
                        variant={selectedSlot?.start === slot.start ? 'default' : 'outline'}
                        size="sm"
                        className="text-xs"
                        onClick={() => setSelectedSlot(slot)}
                      >
                        {formatTime(slot.start)}
                      </Button>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm text-center py-4">
                    No available slots for this date. Please try another date.
                  </p>
                )}
              </div>
            )}

            {selectedSlot && (
              <div className="p-3 bg-primary/10 rounded-lg text-sm">
                <p className="font-medium text-primary">
                  Selected: {formatDate(selectedSlot.start)} at {formatTime(selectedSlot.start)}
                </p>
              </div>
            )}

            <div>
              <Label>Notes (optional)</Label>
              <Textarea
                value={bookingNotes}
                onChange={(e) => setBookingNotes(e.target.value)}
                placeholder="Any topics you'd like to discuss..."
                rows={2}
                className="mt-1"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <Button 
                onClick={handleBookAppointment} 
                disabled={!selectedSlot || booking}
                className="flex-1"
              >
                {booking ? (
                  <>
                    <Loader2 className="animate-spin mr-2" size={16} />
                    Booking...
                  </>
                ) : (
                  'Confirm Booking'
                )}
              </Button>
              <Button variant="outline" onClick={() => setShowBookingDialog(false)}>
                Cancel
              </Button>
            </div>
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

      {/* Assessment Taker Dialog - Full Screen for better UX */}
      <Dialog open={showAssessmentTaker} onOpenChange={(open) => {
        if (!open) {
          setShowAssessmentTaker(false);
          setSelectedAssessmentId(null);
        }
      }}>
        <DialogContent className="max-w-2xl max-h-[95vh] overflow-y-auto p-0" data-testid="assessment-taker-dialog">
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
        <DialogContent className="max-w-lg" data-testid="shared-report-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-primary">
              <FileText size={20} /> Assessment Report
            </DialogTitle>
          </DialogHeader>
          {sharedReportData && (
            <div className="space-y-4">
              <div>
                <p className="text-lg font-medium">{sharedReportData.assessment_type}</p>
                <p className="text-sm text-muted-foreground">
                  Completed: {sharedReportData.completed_at ? formatDate(sharedReportData.completed_at) : 'N/A'}
                </p>
              </div>

              {/* Score Display */}
              {sharedReportData.score_details && (
                <Card className="p-4 bg-surface">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Your Score</p>
                      <p className="text-2xl font-bold text-primary">{sharedReportData.score}</p>
                      {sharedReportData.score_details.max_score && (
                        <p className="text-xs text-muted-foreground">out of {sharedReportData.score_details.max_score}</p>
                      )}
                    </div>
                    {sharedReportData.score_details.severity && (
                      <Badge className={`text-sm ${
                        sharedReportData.score_details.severity.color === 'green' ? 'bg-success/10 text-success' :
                        sharedReportData.score_details.severity.color === 'yellow' ? 'bg-warning/10 text-warning' :
                        sharedReportData.score_details.severity.color === 'orange' ? 'bg-orange-100 text-orange-800' :
                        'bg-destructive/10 text-destructive'
                      }`}>
                        {sharedReportData.score_details.severity.label}
                      </Badge>
                    )}
                  </div>
                </Card>
              )}

              {/* Therapist Notes if any */}
              {sharedReportData.therapist_notes && (
                <div>
                  <p className="text-sm font-medium mb-2">Notes from Your Therapist</p>
                  <Card className="p-4 bg-blue-50 border-blue-200">
                    <p className="text-sm text-blue-900">{sharedReportData.therapist_notes}</p>
                  </Card>
                </div>
              )}

              {/* Disclaimer */}
              <Card className="p-4 bg-amber-50 border-amber-200">
                <p className="text-sm text-amber-800">
                  <AlertCircle className="w-4 h-4 inline mr-2" />
                  Please discuss this report with your therapist for proper interpretation.
                </p>
              </Card>

              <Button onClick={() => setShowSharedReport(false)} className="w-full">
                Close
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClientDashboard;
