import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { 
  User, Phone, Mail, MapPin, Calendar, FileText, CreditCard, 
  ClipboardCheck, Clock, CheckCircle, AlertCircle, ChevronRight,
  Brain, History, Loader2, Edit, MessageSquare, BookOpen,
  ArrowRight, TrendingUp, FileCheck, Users, Plus, Eye, CalendarPlus,
  Link as LinkIcon, PenSquare, Receipt, PlayCircle, StopCircle
} from 'lucide-react';
import { formatDate, formatTime, formatCurrency } from '../utils/formatUtils';
import CaseHistoryWizard from './CaseHistoryWizard';
import TherapyConsent from './TherapyConsent';
import { SessionActionButtons, AppointmentStatusBadge } from './SessionCheckInOut';
import { PaymentCard } from './PaymentReceipt';

// Helper to safely extract error message from API response
const getErrorMessage = (error, fallback = 'An error occurred') => {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) return detail[0]?.msg || fallback;
  if (typeof detail === 'object' && detail?.msg) return detail.msg;
  return fallback;
};

const ClientProfileView = ({ client, isOpen, onClose, isReadOnly = false, onRefresh, isAssistant = false }) => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [profileData, setProfileData] = useState({
    appointments: [],
    sessionNotes: [],
    payments: [],
    assessments: [],
    homework: [],
    caseHistory: null,
    consent: null
  });
  const [showCaseHistoryDialog, setShowCaseHistoryDialog] = useState(false);
  const [showConsentDialog, setShowConsentDialog] = useState(false);
  
  // Session Note dialogs
  const [showViewNoteDialog, setShowViewNoteDialog] = useState(false);
  const [showEditNoteDialog, setShowEditNoteDialog] = useState(false);
  const [showCreateNoteDialog, setShowCreateNoteDialog] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);
  const [editingNote, setEditingNote] = useState({
    template_type: 'SOAP',
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
    data: '',
  });
  const [newNote, setNewNote] = useState({
    appointment_id: '',
    template_type: 'SOAP',
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
    data: '',
  });
  
  // Appointment booking dialog
  const [showBookAppointmentDialog, setShowBookAppointmentDialog] = useState(false);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [appointmentNotes, setAppointmentNotes] = useState('');
  const [loadingSlots, setLoadingSlots] = useState(false);

  useEffect(() => {
    if (isOpen && client?.id) {
      fetchAllClientData();
    }
  }, [isOpen, client?.id]);

  const fetchAllClientData = async () => {
    setLoading(true);
    try {
      const [appointmentsRes, notesRes, paymentsRes, assessmentsRes, homeworkRes] = await Promise.all([
        axios.get(`${API}/appointments?client_id=${client.id}`).catch(() => ({ data: [] })),
        axios.get(`${API}/session-notes?client_id=${client.id}`).catch(() => ({ data: [] })),
        axios.get(`${API}/payments?client_id=${client.id}`).catch(() => ({ data: [] })),
        axios.get(`${API}/assessments?client_id=${client.id}`).catch(() => ({ data: [] })),
        axios.get(`${API}/homework?client_id=${client.id}`).catch(() => ({ data: [] }))
      ]);

      // Get case history and consent
      let caseHistory = null;
      let consent = null;
      try {
        const caseRes = await axios.get(`${API}/case-history/${client.id}`);
        caseHistory = caseRes.data;
      } catch (e) {
        // Case history doesn't exist
      }
      try {
        const consentRes = await axios.get(`${API}/therapy-consent/${client.id}`);
        consent = consentRes.data;
      } catch (e) {
        // Consent doesn't exist
      }

      setProfileData({
        appointments: appointmentsRes.data || [],
        sessionNotes: notesRes.data || [],
        payments: paymentsRes.data || [],
        assessments: assessmentsRes.data || [],
        homework: homeworkRes.data || [],
        caseHistory,
        consent
      });
    } catch (error) {
      toast.error('Failed to load client data');
    } finally {
      setLoading(false);
    }
  };

  // ========== Session Note Functions ==========
  
  const handleViewNote = (note) => {
    setSelectedNote(note);
    setShowViewNoteDialog(true);
  };

  const handleEditNoteClick = (note) => {
    setSelectedNote(note);
    setEditingNote({
      template_type: note.template_type || 'SOAP',
      subjective: note.subjective || '',
      objective: note.objective || '',
      assessment: note.assessment || '',
      plan: note.plan || '',
      data: note.data || '',
    });
    setShowEditNoteDialog(true);
  };

  const handleEditNoteSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/session-notes/${selectedNote.id}`, editingNote);
      toast.success('Session note updated');
      setShowEditNoteDialog(false);
      setSelectedNote(null);
      fetchAllClientData();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to update session note'));
    }
  };

  const handleStartNewNote = () => {
    // Check if case history is complete first
    if (!profileData.caseHistory?.is_complete) {
      toast.error('Case History must be completed before creating session notes');
      setShowCaseHistoryDialog(true);
      return;
    }
    
    // Check if consent is signed
    if (!profileData.consent?.is_signed) {
      toast.error('Therapy Consent must be signed before creating session notes');
      setShowConsentDialog(true);
      return;
    }

    // Find today's appointment
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const todayAppointments = profileData.appointments.filter(a => {
      const apptDate = new Date(a.start_time);
      return apptDate >= today && apptDate < tomorrow && a.status !== 'cancelled';
    });

    if (todayAppointments.length === 0) {
      toast.warning('No appointment scheduled for today. Please book an appointment first.');
      setShowBookAppointmentDialog(true);
      return;
    }

    // Pre-fill with today's appointment
    setNewNote({
      appointment_id: todayAppointments[0].id,
      template_type: 'SOAP',
      subjective: '',
      objective: '',
      assessment: '',
      plan: '',
      data: '',
    });
    setShowCreateNoteDialog(true);
  };

  const handleCreateNoteSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/session-notes`, {
        client_id: client.id,
        ...newNote,
      });
      toast.success('Session note created');
      setShowCreateNoteDialog(false);
      setNewNote({
        appointment_id: '',
        template_type: 'SOAP',
        subjective: '',
        objective: '',
        assessment: '',
        plan: '',
        data: '',
      });
      fetchAllClientData();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to create session note'));
    }
  };

  // Find the appointment linked to a note
  const getLinkedAppointment = (note) => {
    if (!note.appointment_id) return null;
    return profileData.appointments.find(a => a.id === note.appointment_id);
  };

  // ========== Appointment Booking Functions ==========
  
  const handleBookAppointment = () => {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setAppointmentNotes('');
    setShowBookAppointmentDialog(true);
    fetchAvailableSlots(dateStr);
  };

  const fetchAvailableSlots = async (date) => {
    setLoadingSlots(true);
    try {
      // Get therapist ID from client's assigned therapist
      const response = await axios.get(`${API}/available-slots/${client.therapist_id}?date=${date}`);
      setAvailableSlots(response.data.slots || []);
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

  const handleSlotSelect = (slot) => {
    setSelectedSlot(slot);
  };

  const handleCreateAppointment = async () => {
    if (!selectedSlot) {
      toast.error('Please select a time slot');
      return;
    }

    try {
      await axios.post(`${API}/appointments`, {
        client_id: client.id,
        start_time: selectedSlot.start,
        end_time: selectedSlot.end,
        notes: appointmentNotes,
      });
      toast.success('Appointment booked successfully');
      setShowBookAppointmentDialog(false);
      setSelectedSlot(null);
      setAppointmentNotes('');
      fetchAllClientData();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to book appointment'));
    }
  };

  if (!isOpen) return null;

  // Calculate statistics
  const completedSessions = profileData.appointments.filter(a => a.status === 'completed').length;
  const upcomingAppointments = profileData.appointments.filter(a => 
    new Date(a.start_time) > new Date() && a.status !== 'cancelled'
  ).sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
  const nextAppointment = upcomingAppointments[0];
  const pastAppointments = profileData.appointments.filter(a => 
    new Date(a.start_time) <= new Date() || a.status === 'completed'
  ).sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
  const lastSession = pastAppointments[0];
  
  const completedAssessments = profileData.assessments.filter(a => a.status === 'completed').length;
  const pendingAssessments = profileData.assessments.filter(a => a.status === 'assigned').length;
  
  const totalPayments = profileData.payments.reduce((sum, p) => sum + (p.amount || 0), 0);
  const pendingPayments = profileData.payments.filter(p => p.status === 'pending').reduce((sum, p) => sum + (p.amount || 0), 0);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden p-0">
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <Loader2 className="animate-spin text-primary" size={40} />
          </div>
        ) : (
          <div className="flex flex-col h-[85vh]">
            {/* Header */}
            <div className="bg-gradient-to-r from-primary to-primary/80 p-6 text-white">
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-2xl font-bold">
                  {client.full_name?.charAt(0) || 'C'}
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-serif">{client.full_name}</h2>
                  <p className="text-white/80 text-sm">Client ID: {client.client_id}</p>
                  <div className="flex gap-4 mt-2 text-sm text-white/70">
                    {client.mobile && (
                      <span className="flex items-center gap-1">
                        <Phone size={14} /> {client.mobile}
                      </span>
                    )}
                    {client.email && (
                      <span className="flex items-center gap-1">
                        <Mail size={14} /> {client.email}
                      </span>
                    )}
                  </div>
                  {/* Quick Action Buttons */}
                  <div className="flex gap-2 mt-3">
                    <Button
                      size="sm"
                      variant="secondary"
                      className="bg-white/20 hover:bg-white/30 text-white border-0"
                      onClick={handleBookAppointment}
                      disabled={isReadOnly}
                      data-testid="book-appointment-btn"
                    >
                      <CalendarPlus size={14} className="mr-1" /> Book Appointment
                    </Button>
                    {!isAssistant && (
                      <Button
                        size="sm"
                        variant="secondary"
                        className="bg-white/20 hover:bg-white/30 text-white border-0"
                        onClick={handleStartNewNote}
                        disabled={isReadOnly}
                        data-testid="start-session-note-btn"
                      >
                        <PenSquare size={14} className="mr-1" /> Start Session Note
                      </Button>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2">
                    {profileData.consent?.is_signed ? (
                      <span className="flex items-center gap-1 text-xs bg-green-500/30 px-2 py-1 rounded-full">
                        <CheckCircle size={12} /> Consent Signed
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs bg-amber-500/30 px-2 py-1 rounded-full">
                        <AlertCircle size={12} /> Consent Pending
                      </span>
                    )}
                  </div>
                  {profileData.caseHistory?.is_complete ? (
                    <span className="flex items-center gap-1 text-xs bg-green-500/30 px-2 py-1 rounded-full mt-1">
                      <FileCheck size={12} /> Case History Complete
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs bg-amber-500/30 px-2 py-1 rounded-full mt-1">
                      <FileText size={12} /> Case History Pending
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-5 gap-4 p-4 bg-muted/30 border-b">
              <div className="text-center">
                <p className="text-2xl font-bold text-primary">{completedSessions}</p>
                <p className="text-xs text-muted-foreground">Sessions Done</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-primary">{upcomingAppointments.length}</p>
                <p className="text-xs text-muted-foreground">Upcoming</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-primary">{profileData.sessionNotes.length}</p>
                <p className="text-xs text-muted-foreground">Session Notes</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-primary">{completedAssessments}</p>
                <p className="text-xs text-muted-foreground">Assessments</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-primary">{formatCurrency(totalPayments)}</p>
                <p className="text-xs text-muted-foreground">Total Paid</p>
              </div>
            </div>

            {/* Tabs Content */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
              <TabsList className="mx-4 mt-2 justify-start">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="sessions">Sessions</TabsTrigger>
                <TabsTrigger value="case-history">Case History</TabsTrigger>
                <TabsTrigger value="assessments">Assessments</TabsTrigger>
                <TabsTrigger value="payments">Payments</TabsTrigger>
              </TabsList>

              <div className="flex-1 overflow-y-auto p-4">
                {/* Overview Tab */}
                <TabsContent value="overview" className="mt-0 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {/* Next Appointment */}
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Calendar className="text-primary" size={18} />
                        <h4 className="font-semibold">Next Appointment</h4>
                      </div>
                      {nextAppointment ? (
                        <div className="bg-primary/5 p-3 rounded-lg">
                          <p className="font-medium text-primary">
                            {formatDate(nextAppointment.start_time)}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {formatTime(nextAppointment.start_time)} - {formatTime(nextAppointment.end_time)}
                          </p>
                          {nextAppointment.notes && (
                            <p className="text-xs mt-1 text-muted-foreground">{nextAppointment.notes}</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-muted-foreground text-sm">No upcoming appointments</p>
                      )}
                    </Card>

                    {/* Last Session */}
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <History className="text-secondary" size={18} />
                        <h4 className="font-semibold">Last Session</h4>
                      </div>
                      {lastSession ? (
                        <div className="bg-secondary/5 p-3 rounded-lg">
                          <p className="font-medium">
                            {formatDate(lastSession.start_time)}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Status: <span className="capitalize">{lastSession.status}</span>
                          </p>
                        </div>
                      ) : (
                        <p className="text-muted-foreground text-sm">No past sessions</p>
                      )}
                    </Card>

                    {/* Case History Summary */}
                    <Card className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <FileText className="text-info" size={18} />
                          <h4 className="font-semibold">Case History</h4>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => setShowCaseHistoryDialog(true)}
                        >
                          {profileData.caseHistory ? 'View' : 'Create'} <ChevronRight size={14} />
                        </Button>
                      </div>
                      {profileData.caseHistory ? (
                        <div className="space-y-2 text-sm">
                          <p><span className="text-muted-foreground">Status:</span> {profileData.caseHistory.is_complete ? '✓ Complete' : '⏳ In Progress'}</p>
                          {profileData.caseHistory.presenting_complaints?.main_problems && (
                            <p className="text-muted-foreground line-clamp-2">
                              {profileData.caseHistory.presenting_complaints.main_problems}
                            </p>
                          )}
                        </div>
                      ) : (
                        <p className="text-muted-foreground text-sm">No case history created yet</p>
                      )}
                    </Card>

                    {/* Consent Status */}
                    <Card className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <FileCheck className="text-success" size={18} />
                          <h4 className="font-semibold">Therapy Consent</h4>
                        </div>
                        {profileData.consent && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => setShowConsentDialog(true)}
                          >
                            View <ChevronRight size={14} />
                          </Button>
                        )}
                      </div>
                      {profileData.consent ? (
                        <div className="space-y-2 text-sm">
                          <p>
                            <span className="text-muted-foreground">Status:</span>{' '}
                            {profileData.consent.is_signed ? (
                              <span className="text-green-600">✓ Signed ({profileData.consent.signature_method})</span>
                            ) : (
                              <span className="text-amber-600">⏳ Awaiting Signature</span>
                            )}
                          </p>
                          {profileData.consent.signed_at && (
                            <p><span className="text-muted-foreground">Signed on:</span> {formatDate(profileData.consent.signed_at)}</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-muted-foreground text-sm">Complete case history to generate consent</p>
                      )}
                    </Card>
                  </div>

                  {/* Recent Session Notes */}
                  <Card className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <BookOpen className="text-primary" size={18} />
                        <h4 className="font-semibold">Recent Session Notes</h4>
                      </div>
                      <span className="text-xs text-muted-foreground">{profileData.sessionNotes.length} total</span>
                    </div>
                    {profileData.sessionNotes.length > 0 ? (
                      <div className="space-y-2">
                        {profileData.sessionNotes.slice(0, 3).map((note, idx) => (
                          <div key={idx} className="p-3 bg-muted/30 rounded-lg">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="text-sm font-medium">{formatDate(note.created_at)}</p>
                                <p className="text-xs text-muted-foreground">{note.template_type} Note</p>
                              </div>
                              <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                                {note.template_type}
                              </span>
                            </div>
                            {note.assessment && (
                              <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{note.assessment}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-sm">No session notes yet</p>
                    )}
                  </Card>

                  {/* Pending Items */}
                  {(pendingAssessments > 0 || profileData.homework.filter(h => h.status === 'assigned').length > 0) && (
                    <Card className="p-4 border-amber-200 bg-amber-50/50">
                      <div className="flex items-center gap-2 mb-3">
                        <AlertCircle className="text-amber-600" size={18} />
                        <h4 className="font-semibold text-amber-800">Pending Items</h4>
                      </div>
                      <div className="space-y-2">
                        {pendingAssessments > 0 && (
                          <p className="text-sm text-amber-700">• {pendingAssessments} assessment(s) awaiting completion</p>
                        )}
                        {profileData.homework.filter(h => h.status === 'assigned').length > 0 && (
                          <p className="text-sm text-amber-700">
                            • {profileData.homework.filter(h => h.status === 'assigned').length} homework assignment(s) pending
                          </p>
                        )}
                      </div>
                    </Card>
                  )}
                </TabsContent>

                {/* Sessions Tab */}
                <TabsContent value="sessions" className="mt-0 space-y-4">
                  {/* Action Buttons */}
                  <div className="flex gap-2 justify-end">
                    <Button
                      onClick={handleBookAppointment}
                      disabled={isReadOnly}
                      variant="outline"
                      size="sm"
                      data-testid="sessions-book-appointment-btn"
                    >
                      <CalendarPlus size={14} className="mr-1" /> Book Appointment
                    </Button>
                    {!isAssistant && (
                      <Button
                        onClick={handleStartNewNote}
                        disabled={isReadOnly}
                        size="sm"
                        data-testid="sessions-start-note-btn"
                      >
                        <PenSquare size={14} className="mr-1" /> Start Session Note
                      </Button>
                    )}
                  </div>

                  {/* Stats Cards */}
                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <Card className="p-4 text-center bg-green-50">
                      <p className="text-3xl font-bold text-green-600">{completedSessions}</p>
                      <p className="text-sm text-green-700">Completed</p>
                    </Card>
                    <Card className="p-4 text-center bg-blue-50">
                      <p className="text-3xl font-bold text-blue-600">{upcomingAppointments.length}</p>
                      <p className="text-sm text-blue-700">Upcoming</p>
                    </Card>
                    <Card className="p-4 text-center bg-purple-50">
                      <p className="text-3xl font-bold text-purple-600">{profileData.sessionNotes.length}</p>
                      <p className="text-sm text-purple-700">Session Notes</p>
                    </Card>
                    <Card className="p-4 text-center bg-gray-50">
                      <p className="text-3xl font-bold text-gray-600">
                        {profileData.appointments.filter(a => a.status === 'cancelled').length}
                      </p>
                      <p className="text-sm text-gray-700">Cancelled</p>
                    </Card>
                  </div>

                  {/* Session Notes Section */}
                  {!isAssistant && profileData.sessionNotes.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <FileText size={16} /> Session Notes ({profileData.sessionNotes.length})
                      </h4>
                      <div className="space-y-2 max-h-[200px] overflow-y-auto">
                        {profileData.sessionNotes
                          .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                          .map((note, idx) => {
                            const linkedAppt = getLinkedAppointment(note);
                            return (
                              <Card key={idx} className="p-3 border-purple-200 bg-purple-50/30 hover:bg-purple-50/50 transition-colors">
                                <div className="flex justify-between items-start">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                      <p className="font-medium">{formatDate(note.created_at)}</p>
                                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                                        note.template_type === 'SOAP' ? 'bg-blue-100 text-blue-700' : 'bg-teal-100 text-teal-700'
                                      }`}>
                                        {note.template_type}
                                      </span>
                                      {linkedAppt && (
                                        <span className="flex items-center text-xs text-muted-foreground">
                                          <LinkIcon size={10} className="mr-1" /> Linked to {formatDate(linkedAppt.start_time)}
                                        </span>
                                      )}
                                    </div>
                                    {note.assessment && (
                                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{note.assessment}</p>
                                    )}
                                  </div>
                                  <div className="flex gap-1 ml-2">
                                    <Button 
                                      variant="ghost" 
                                      size="sm" 
                                      onClick={() => handleViewNote(note)}
                                      data-testid={`view-note-${note.id}`}
                                    >
                                      <Eye size={14} />
                                    </Button>
                                    {!isReadOnly && (
                                      <Button 
                                        variant="ghost" 
                                        size="sm" 
                                        onClick={() => handleEditNoteClick(note)}
                                        data-testid={`edit-note-${note.id}`}
                                      >
                                        <Edit size={14} />
                                      </Button>
                                    )}
                                  </div>
                                </div>
                              </Card>
                            );
                          })}
                      </div>
                    </div>
                  )}

                  {/* No Session Notes Message for Therapists */}
                  {!isAssistant && profileData.sessionNotes.length === 0 && (
                    <Card className="p-4 border-dashed border-2 text-center mb-4">
                      <FileText className="mx-auto text-muted-foreground mb-2" size={32} />
                      <p className="text-muted-foreground text-sm">No session notes yet</p>
                      {!isReadOnly && profileData.caseHistory?.is_complete && profileData.consent?.is_signed && (
                        <Button 
                          variant="link" 
                          size="sm" 
                          onClick={handleStartNewNote}
                          className="mt-2"
                        >
                          Create your first session note
                        </Button>
                      )}
                    </Card>
                  )}

                  {/* All Appointments Section */}
                  <h4 className="font-semibold">All Appointments</h4>
                  <div className="space-y-2 max-h-[250px] overflow-y-auto">
                    {profileData.appointments.length > 0 ? (
                      profileData.appointments
                        .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
                        .map((appt, idx) => {
                          // Check if this appointment has a linked session note
                          const linkedNote = profileData.sessionNotes.find(n => n.appointment_id === appt.id);
                          return (
                            <Card key={idx} className={`p-3 ${
                              appt.status === 'completed' ? 'border-green-200 bg-green-50/30' :
                              appt.status === 'cancelled' ? 'border-red-200 bg-red-50/30' :
                              'border-blue-200 bg-blue-50/30'
                            }`}>
                              <div className="flex justify-between items-center">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <p className="font-medium">{formatDate(appt.start_time)}</p>
                                    {linkedNote && !isAssistant && (
                                      <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded flex items-center gap-1">
                                        <FileText size={10} /> Note
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-sm text-muted-foreground">
                                    {formatTime(appt.start_time)} - {formatTime(appt.end_time)}
                                  </p>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className={`text-xs px-2 py-1 rounded-full capitalize ${
                                    appt.status === 'completed' ? 'bg-green-100 text-green-700' :
                                    appt.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                                    appt.status === 'scheduled' ? 'bg-blue-100 text-blue-700' :
                                    'bg-gray-100 text-gray-700'
                                  }`}>
                                    {appt.status}
                                  </span>
                                  {linkedNote && !isAssistant && (
                                    <Button 
                                      variant="ghost" 
                                      size="sm" 
                                      onClick={() => handleViewNote(linkedNote)}
                                      title="View session note"
                                    >
                                      <Eye size={14} />
                                    </Button>
                                  )}
                                </div>
                              </div>
                              {appt.notes && (
                                <p className="text-xs text-muted-foreground mt-1">{appt.notes}</p>
                              )}
                            </Card>
                          );
                        })
                    ) : (
                      <p className="text-muted-foreground text-center py-8">No appointments yet</p>
                    )}
                  </div>
                </TabsContent>

                {/* Case History Tab */}
                <TabsContent value="case-history" className="mt-0">
                  {profileData.caseHistory ? (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <h4 className="font-semibold">Case History</h4>
                          <p className="text-sm text-muted-foreground">
                            Created: {formatDate(profileData.caseHistory.created_at)}
                          </p>
                        </div>
                        <Button onClick={() => setShowCaseHistoryDialog(true)}>
                          <Edit size={14} className="mr-2" /> View / Edit
                        </Button>
                      </div>

                      {/* Basic Info */}
                      {profileData.caseHistory.basic_identification && (
                        <Card className="p-4">
                          <h5 className="font-medium mb-3 flex items-center gap-2">
                            <User size={16} /> Basic Identification
                          </h5>
                          <div className="grid grid-cols-3 gap-3 text-sm">
                            {Object.entries(profileData.caseHistory.basic_identification).map(([key, value]) => (
                              value && (
                                <div key={key}>
                                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}:</span>
                                  <span className="ml-1">{value}</span>
                                </div>
                              )
                            ))}
                          </div>
                        </Card>
                      )}

                      {/* Presenting Complaints */}
                      {profileData.caseHistory.presenting_complaints && (
                        <Card className="p-4">
                          <h5 className="font-medium mb-3">Presenting Complaints</h5>
                          <div className="space-y-2 text-sm">
                            {profileData.caseHistory.presenting_complaints.main_problems && (
                              <div>
                                <span className="text-muted-foreground">Main Problems:</span>
                                <p className="mt-1">{profileData.caseHistory.presenting_complaints.main_problems}</p>
                              </div>
                            )}
                            <div className="grid grid-cols-3 gap-2">
                              {profileData.caseHistory.presenting_complaints.duration && (
                                <p><span className="text-muted-foreground">Duration:</span> {profileData.caseHistory.presenting_complaints.duration}</p>
                              )}
                              {profileData.caseHistory.presenting_complaints.severity && (
                                <p><span className="text-muted-foreground">Severity:</span> {profileData.caseHistory.presenting_complaints.severity}</p>
                              )}
                              {profileData.caseHistory.presenting_complaints.frequency && (
                                <p><span className="text-muted-foreground">Frequency:</span> {profileData.caseHistory.presenting_complaints.frequency}</p>
                              )}
                            </div>
                          </div>
                        </Card>
                      )}

                      {/* MSE Summary */}
                      {profileData.caseHistory.mental_status_examination && (
                        <Card className="p-4">
                          <h5 className="font-medium mb-3 flex items-center gap-2">
                            <Brain size={16} /> Mental Status Examination
                          </h5>
                          <div className="grid grid-cols-4 gap-2 text-sm">
                            {Object.entries(profileData.caseHistory.mental_status_examination).map(([key, value]) => (
                              value && (
                                <div key={key} className="bg-muted/30 p-2 rounded">
                                  <span className="text-xs text-muted-foreground capitalize block">{key.replace(/_/g, ' ')}</span>
                                  <span className="font-medium">{value}</span>
                                </div>
                              )
                            ))}
                          </div>
                        </Card>
                      )}

                      {/* Therapy Plan */}
                      {profileData.caseHistory.initial_therapy_plan && (
                        <Card className="p-4">
                          <h5 className="font-medium mb-3">Initial Therapy Plan</h5>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            {profileData.caseHistory.initial_therapy_plan.therapy_modality && (
                              <p><span className="text-muted-foreground">Modality:</span> {profileData.caseHistory.initial_therapy_plan.therapy_modality}</p>
                            )}
                            {profileData.caseHistory.initial_therapy_plan.session_frequency && (
                              <p><span className="text-muted-foreground">Frequency:</span> {profileData.caseHistory.initial_therapy_plan.session_frequency}</p>
                            )}
                            {profileData.caseHistory.initial_therapy_plan.initial_goals && (
                              <div className="col-span-2">
                                <span className="text-muted-foreground">Goals:</span>
                                <p className="mt-1">{profileData.caseHistory.initial_therapy_plan.initial_goals}</p>
                              </div>
                            )}
                          </div>
                        </Card>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <FileText className="mx-auto text-muted-foreground mb-4" size={48} />
                      <h4 className="font-medium mb-2">No Case History</h4>
                      <p className="text-muted-foreground mb-4">Create a case history to document the client&apos;s background</p>
                      {!isReadOnly && (
                        <Button onClick={() => setShowCaseHistoryDialog(true)}>
                          Create Case History
                        </Button>
                      )}
                    </div>
                  )}
                </TabsContent>

                {/* Assessments Tab */}
                <TabsContent value="assessments" className="mt-0 space-y-4">
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <Card className="p-4 text-center bg-green-50">
                      <p className="text-3xl font-bold text-green-600">{completedAssessments}</p>
                      <p className="text-sm text-green-700">Completed</p>
                    </Card>
                    <Card className="p-4 text-center bg-amber-50">
                      <p className="text-3xl font-bold text-amber-600">{pendingAssessments}</p>
                      <p className="text-sm text-amber-700">Pending</p>
                    </Card>
                  </div>

                  <div className="space-y-2">
                    {profileData.assessments.length > 0 ? (
                      profileData.assessments.map((assess, idx) => (
                        <Card key={idx} className={`p-4 ${
                          assess.status === 'completed' ? 'border-green-200' : 'border-amber-200'
                        }`}>
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium">{assess.assessment_type}</p>
                              <p className="text-sm text-muted-foreground">
                                Assigned: {formatDate(assess.created_at)}
                              </p>
                            </div>
                            <div className="text-right">
                              <span className={`text-xs px-2 py-1 rounded-full capitalize ${
                                assess.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                              }`}>
                                {assess.status}
                              </span>
                              {assess.score !== undefined && assess.score !== null && (
                                <p className="text-lg font-bold text-primary mt-1">Score: {assess.score}</p>
                              )}
                            </div>
                          </div>
                        </Card>
                      ))
                    ) : (
                      <p className="text-muted-foreground text-center py-8">No assessments assigned</p>
                    )}
                  </div>
                </TabsContent>

                {/* Payments Tab */}
                <TabsContent value="payments" className="mt-0 space-y-4">
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <Card className="p-4 text-center bg-green-50">
                      <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPayments)}</p>
                      <p className="text-sm text-green-700">Total Paid</p>
                    </Card>
                    <Card className="p-4 text-center bg-amber-50">
                      <p className="text-2xl font-bold text-amber-600">{formatCurrency(pendingPayments)}</p>
                      <p className="text-sm text-amber-700">Pending</p>
                    </Card>
                    <Card className="p-4 text-center bg-blue-50">
                      <p className="text-2xl font-bold text-blue-600">{profileData.payments.length}</p>
                      <p className="text-sm text-blue-700">Transactions</p>
                    </Card>
                  </div>

                  <div className="space-y-2">
                    {profileData.payments.length > 0 ? (
                      profileData.payments
                        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                        .map((payment, idx) => (
                          <Card key={idx} className="p-4">
                            <div className="flex justify-between items-center">
                              <div>
                                <p className="font-medium">{formatCurrency(payment.amount)}</p>
                                <p className="text-sm text-muted-foreground">
                                  {formatDate(payment.created_at)}
                                </p>
                                {payment.description && (
                                  <p className="text-xs text-muted-foreground">{payment.description}</p>
                                )}
                              </div>
                              <span className={`text-xs px-2 py-1 rounded-full capitalize ${
                                payment.status === 'completed' ? 'bg-green-100 text-green-700' :
                                payment.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {payment.status || 'recorded'}
                              </span>
                            </div>
                          </Card>
                        ))
                    ) : (
                      <p className="text-muted-foreground text-center py-8">No payment records</p>
                    )}
                  </div>
                </TabsContent>
              </div>
            </Tabs>
          </div>
        )}

        {/* Case History Dialog */}
        <Dialog open={showCaseHistoryDialog} onOpenChange={setShowCaseHistoryDialog}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Case History - {client.full_name}</DialogTitle>
            </DialogHeader>
            <CaseHistoryWizard
              clientId={client.id}
              clientName={client.full_name}
              isReadOnly={isReadOnly}
              onComplete={() => {
                setShowCaseHistoryDialog(false);
                fetchAllClientData();
                if (onRefresh) onRefresh();
              }}
              onClose={() => setShowCaseHistoryDialog(false)}
            />
          </DialogContent>
        </Dialog>

        {/* Consent Dialog */}
        <TherapyConsent
          clientId={client.id}
          clientName={client.full_name}
          isOpen={showConsentDialog}
          onClose={() => {
            setShowConsentDialog(false);
            fetchAllClientData();
          }}
          isReadOnly={isReadOnly}
          userRole="therapist"
        />

        {/* View Session Note Dialog */}
        <Dialog open={showViewNoteDialog} onOpenChange={setShowViewNoteDialog}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText size={20} /> Session Note - {selectedNote?.template_type}
              </DialogTitle>
            </DialogHeader>
            {selectedNote && (
              <div className="space-y-4">
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>Created: {formatDate(selectedNote.created_at)}</span>
                  {getLinkedAppointment(selectedNote) && (
                    <span className="flex items-center gap-1">
                      <LinkIcon size={12} /> Linked: {formatDate(getLinkedAppointment(selectedNote).start_time)}
                    </span>
                  )}
                </div>
                
                {selectedNote.template_type === 'SOAP' ? (
                  <>
                    {selectedNote.subjective && (
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <h4 className="font-semibold text-blue-800 mb-1">Subjective</h4>
                        <p className="text-sm whitespace-pre-wrap">{selectedNote.subjective}</p>
                      </div>
                    )}
                    {selectedNote.objective && (
                      <div className="p-3 bg-green-50 rounded-lg">
                        <h4 className="font-semibold text-green-800 mb-1">Objective</h4>
                        <p className="text-sm whitespace-pre-wrap">{selectedNote.objective}</p>
                      </div>
                    )}
                    {selectedNote.assessment && (
                      <div className="p-3 bg-yellow-50 rounded-lg">
                        <h4 className="font-semibold text-yellow-800 mb-1">Assessment</h4>
                        <p className="text-sm whitespace-pre-wrap">{selectedNote.assessment}</p>
                      </div>
                    )}
                    {selectedNote.plan && (
                      <div className="p-3 bg-purple-50 rounded-lg">
                        <h4 className="font-semibold text-purple-800 mb-1">Plan</h4>
                        <p className="text-sm whitespace-pre-wrap">{selectedNote.plan}</p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    {selectedNote.data && (
                      <div className="p-3 bg-teal-50 rounded-lg">
                        <h4 className="font-semibold text-teal-800 mb-1">Data</h4>
                        <p className="text-sm whitespace-pre-wrap">{selectedNote.data}</p>
                      </div>
                    )}
                    {selectedNote.assessment && (
                      <div className="p-3 bg-yellow-50 rounded-lg">
                        <h4 className="font-semibold text-yellow-800 mb-1">Assessment</h4>
                        <p className="text-sm whitespace-pre-wrap">{selectedNote.assessment}</p>
                      </div>
                    )}
                    {selectedNote.plan && (
                      <div className="p-3 bg-purple-50 rounded-lg">
                        <h4 className="font-semibold text-purple-800 mb-1">Plan</h4>
                        <p className="text-sm whitespace-pre-wrap">{selectedNote.plan}</p>
                      </div>
                    )}
                  </>
                )}

                <div className="flex gap-2 pt-4 border-t">
                  {!isReadOnly && (
                    <Button onClick={() => {
                      setShowViewNoteDialog(false);
                      handleEditNoteClick(selectedNote);
                    }}>
                      <Edit size={14} className="mr-1" /> Edit Note
                    </Button>
                  )}
                  <Button variant="outline" onClick={() => setShowViewNoteDialog(false)}>
                    Close
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Edit Session Note Dialog */}
        <Dialog open={showEditNoteDialog} onOpenChange={setShowEditNoteDialog}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit size={20} /> Edit Session Note
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleEditNoteSubmit} className="space-y-4">
              <div>
                <Label>Note Type</Label>
                <Select value={editingNote.template_type} onValueChange={(v) => setEditingNote({ ...editingNote, template_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SOAP">SOAP Note</SelectItem>
                    <SelectItem value="DAP">DAP Note</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {editingNote.template_type === 'SOAP' ? (
                <>
                  <div>
                    <Label className="text-blue-700">Subjective</Label>
                    <Textarea
                      value={editingNote.subjective}
                      onChange={(e) => setEditingNote({ ...editingNote, subjective: e.target.value })}
                      placeholder="Client's reported symptoms, concerns, experiences..."
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label className="text-green-700">Objective</Label>
                    <Textarea
                      value={editingNote.objective}
                      onChange={(e) => setEditingNote({ ...editingNote, objective: e.target.value })}
                      placeholder="Observable behaviors, mental status, appearance..."
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label className="text-yellow-700">Assessment</Label>
                    <Textarea
                      value={editingNote.assessment}
                      onChange={(e) => setEditingNote({ ...editingNote, assessment: e.target.value })}
                      placeholder="Clinical impressions, progress, interpretations..."
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label className="text-purple-700">Plan</Label>
                    <Textarea
                      value={editingNote.plan}
                      onChange={(e) => setEditingNote({ ...editingNote, plan: e.target.value })}
                      placeholder="Treatment plan, interventions, homework, next steps..."
                      rows={3}
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <Label className="text-teal-700">Data</Label>
                    <Textarea
                      value={editingNote.data}
                      onChange={(e) => setEditingNote({ ...editingNote, data: e.target.value })}
                      placeholder="Observations and information gathered..."
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label className="text-yellow-700">Assessment</Label>
                    <Textarea
                      value={editingNote.assessment}
                      onChange={(e) => setEditingNote({ ...editingNote, assessment: e.target.value })}
                      placeholder="Clinical impressions and interpretations..."
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label className="text-purple-700">Plan</Label>
                    <Textarea
                      value={editingNote.plan}
                      onChange={(e) => setEditingNote({ ...editingNote, plan: e.target.value })}
                      placeholder="Treatment plan and next steps..."
                      rows={3}
                    />
                  </div>
                </>
              )}

              <div className="flex gap-2 pt-2">
                <Button type="submit">Save Changes</Button>
                <Button type="button" variant="outline" onClick={() => setShowEditNoteDialog(false)}>Cancel</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Create Session Note Dialog */}
        <Dialog open={showCreateNoteDialog} onOpenChange={setShowCreateNoteDialog}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <PenSquare size={20} /> New Session Note for {client.full_name}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateNoteSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Note Type</Label>
                  <Select value={newNote.template_type} onValueChange={(v) => setNewNote({ ...newNote, template_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="SOAP">SOAP Note</SelectItem>
                      <SelectItem value="DAP">DAP Note</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Link to Appointment</Label>
                  <Select value={newNote.appointment_id || 'none'} onValueChange={(v) => setNewNote({ ...newNote, appointment_id: v === 'none' ? '' : v })}>
                    <SelectTrigger><SelectValue placeholder="Select appointment..." /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No appointment</SelectItem>
                      {profileData.appointments
                        .filter(a => a.status !== 'cancelled')
                        .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
                        .slice(0, 10)
                        .map(appt => (
                          <SelectItem key={appt.id} value={appt.id}>
                            {formatDate(appt.start_time)} - {formatTime(appt.start_time)} ({appt.status})
                          </SelectItem>
                        ))
                      }
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {newNote.template_type === 'SOAP' ? (
                <>
                  <div>
                    <Label className="text-blue-700">Subjective *</Label>
                    <Textarea
                      value={newNote.subjective}
                      onChange={(e) => setNewNote({ ...newNote, subjective: e.target.value })}
                      placeholder="Client's reported symptoms, concerns, experiences..."
                      rows={3}
                      required
                    />
                  </div>
                  <div>
                    <Label className="text-green-700">Objective</Label>
                    <Textarea
                      value={newNote.objective}
                      onChange={(e) => setNewNote({ ...newNote, objective: e.target.value })}
                      placeholder="Observable behaviors, mental status, appearance..."
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label className="text-yellow-700">Assessment *</Label>
                    <Textarea
                      value={newNote.assessment}
                      onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })}
                      placeholder="Clinical impressions, progress, interpretations..."
                      rows={3}
                      required
                    />
                  </div>
                  <div>
                    <Label className="text-purple-700">Plan *</Label>
                    <Textarea
                      value={newNote.plan}
                      onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })}
                      placeholder="Treatment plan, interventions, homework, next steps..."
                      rows={3}
                      required
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <Label className="text-teal-700">Data *</Label>
                    <Textarea
                      value={newNote.data}
                      onChange={(e) => setNewNote({ ...newNote, data: e.target.value })}
                      placeholder="Observations and information gathered..."
                      rows={3}
                      required
                    />
                  </div>
                  <div>
                    <Label className="text-yellow-700">Assessment *</Label>
                    <Textarea
                      value={newNote.assessment}
                      onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })}
                      placeholder="Clinical impressions and interpretations..."
                      rows={3}
                      required
                    />
                  </div>
                  <div>
                    <Label className="text-purple-700">Plan *</Label>
                    <Textarea
                      value={newNote.plan}
                      onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })}
                      placeholder="Treatment plan and next steps..."
                      rows={3}
                      required
                    />
                  </div>
                </>
              )}

              <div className="flex gap-2 pt-2">
                <Button type="submit">Create Session Note</Button>
                <Button type="button" variant="outline" onClick={() => setShowCreateNoteDialog(false)}>Cancel</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Book Appointment Dialog */}
        <Dialog open={showBookAppointmentDialog} onOpenChange={setShowBookAppointmentDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <CalendarPlus size={20} /> Book Appointment for {client.full_name}
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
                          onClick={() => handleSlotSelect(slot)}
                        >
                          {formatTime(slot.start)}
                        </Button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm text-center py-4">No available slots for this date</p>
                  )}
                </div>
              )}

              {selectedSlot && (
                <div className="p-3 bg-primary/10 rounded-lg text-sm">
                  <p className="font-medium text-primary">Selected: {formatTime(selectedSlot.start)} - {formatTime(selectedSlot.end)}</p>
                </div>
              )}

              <div>
                <Label>Notes (optional)</Label>
                <Textarea
                  value={appointmentNotes}
                  onChange={(e) => setAppointmentNotes(e.target.value)}
                  placeholder="Session purpose, reminders..."
                  rows={2}
                  className="mt-1"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button 
                  onClick={handleCreateAppointment} 
                  disabled={!selectedSlot}
                  className="flex-1"
                >
                  Book Appointment
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowBookAppointmentDialog(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </DialogContent>
    </Dialog>
  );
};

export default ClientProfileView;
