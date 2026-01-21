import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { toast } from 'sonner';
import { formatDate, formatTime, formatCurrency } from '../utils/formatUtils';
import { 
  ArrowLeft, Phone, Mail, User, Calendar, FileText, ClipboardList, 
  BookOpen, DollarSign, MessageSquare, Edit, Plus, CheckCircle2,
  AlertCircle, Clock, CalendarPlus, PenSquare, ChevronRight, Loader2
} from 'lucide-react';

// Import sub-components
import CaseHistoryForm from './CaseHistoryForm';
import TherapyConsent from './TherapyConsent';
import AssessmentTrendChart from './AssessmentTrendChart';

const ClientProfilePage = ({ clientIdProp, isReadOnly = false, isAssistant = false }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  
  // Extract clientId from URL or prop
  const clientId = clientIdProp || location.pathname.split('/').pop();
  
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data states
  const [sessions, setSessions] = useState([]);
  const [sessionNotes, setSessionNotes] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [payments, setPayments] = useState([]);
  const [homework, setHomework] = useState([]);
  const [caseHistory, setCaseHistory] = useState(null);
  const [consent, setConsent] = useState(null);
  
  // Dialog states
  const [showCaseHistory, setShowCaseHistory] = useState(false);
  const [showConsent, setShowConsent] = useState(false);
  const [showBookAppointment, setShowBookAppointment] = useState(false);
  
  // Book Appointment states
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [appointmentNotes, setAppointmentNotes] = useState('');
  const [loadingSlots, setLoadingSlots] = useState(false);
  
  // Fetch client data
  const fetchClientData = useCallback(async () => {
    if (!clientId) return;
    
    try {
      setLoading(true);
      const [clientRes, sessionsRes, notesRes, appointmentsRes, assessmentsRes, paymentsRes] = await Promise.all([
        axios.get(`${API}/clients/${clientId}`),
        axios.get(`${API}/sessions?client_id=${clientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/session-notes?client_id=${clientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/appointments?client_id=${clientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/assessments/client/${clientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/payments?client_id=${clientId}`).catch(() => ({ data: [] }))
      ]);
      
      setClient(clientRes.data);
      setSessions(sessionsRes.data || []);
      setSessionNotes(notesRes.data || []);
      setAppointments(appointmentsRes.data || []);
      setAssessments(assessmentsRes.data || []);
      setPayments(paymentsRes.data || []);
      
      // Fetch case history and consent
      try {
        const caseRes = await axios.get(`${API}/case-history/${clientId}`);
        setCaseHistory(caseRes.data);
      } catch (e) {
        setCaseHistory(null);
      }
      
      try {
        const consentRes = await axios.get(`${API}/therapy-consent/${clientId}`);
        setConsent(consentRes.data);
      } catch (e) {
        setConsent(null);
      }
      
      // Fetch homework
      try {
        const hwRes = await axios.get(`${API}/homework?client_id=${clientId}`);
        setHomework(hwRes.data || []);
      } catch (e) {
        setHomework([]);
      }
      
    } catch (error) {
      toast.error('Failed to load client data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [clientId]);
  
  useEffect(() => {
    fetchClientData();
  }, [fetchClientData]);
  
  // ========== Book Appointment Functions ==========
  const handleOpenBookAppointment = () => {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setAppointmentNotes('');
    setShowBookAppointment(true);
    fetchAvailableSlots(dateStr);
  };
  
  const fetchAvailableSlots = async (date) => {
    if (!client?.therapist_id) {
      toast.error('Therapist not assigned to client');
      return;
    }
    setLoadingSlots(true);
    try {
      const response = await axios.get(`${API}/available-slots/${client.therapist_id}?date=${date}`);
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
        client_id: clientId,
        start_time: selectedSlot.start,
        end_time: selectedSlot.end,
        notes: appointmentNotes,
      });
      toast.success('Appointment booked successfully');
      setShowBookAppointment(false);
      setSelectedSlot(null);
      setAppointmentNotes('');
      fetchClientData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to book appointment');
    }
  };
  
  // Define all tabs - filter based on isAssistant
  const allTabs = [
    { id: 'overview', label: 'Overview', icon: User, clinicalOnly: false },
    { id: 'case-history', label: 'Case History', icon: FileText, clinicalOnly: true },
    { id: 'sessions', label: 'Sessions', icon: Calendar, clinicalOnly: false },
    { id: 'notes', label: 'Session Notes', icon: PenSquare, clinicalOnly: true },
    { id: 'assessments', label: 'Assessments', icon: ClipboardList, clinicalOnly: true },
    { id: 'homework', label: 'Homework', icon: BookOpen, clinicalOnly: true },
    { id: 'payments', label: 'Payments', icon: DollarSign, clinicalOnly: false },
  ];
  
  // For Assistant: show only non-clinical tabs (Sessions, Payments, + limited Overview)
  const tabs = isAssistant 
    ? allTabs.filter(tab => !tab.clinicalOnly)
    : allTabs;
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (!client) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-muted-foreground">Client not found</p>
        <Button onClick={() => navigate(-1)}>
          <ArrowLeft size={16} className="mr-2" /> Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary to-primary/80 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Back Button */}
          <Button 
            variant="ghost" 
            className="text-white/80 hover:text-white hover:bg-white/10 mb-4 -ml-2"
            onClick={() => navigate(isAssistant ? '/assistant' : '/therapist')}
            data-testid="back-to-clients"
          >
            <ArrowLeft size={18} className="mr-2" /> Back to {isAssistant ? 'Dashboard' : 'Clients'}
          </Button>
          
          {/* Client Info */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-2xl font-bold">
              {client.full_name?.charAt(0) || 'C'}
            </div>
            <div className="flex-1">
              <h1 className="text-2xl sm:text-3xl font-serif">{client.full_name}</h1>
              <p className="text-white/70 text-sm">Client ID: {client.client_id}</p>
              <div className="flex flex-wrap gap-3 mt-2 text-sm text-white/80">
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
            </div>
            
            {/* Status Badges */}
            <div className="flex flex-wrap gap-2">
              {consent?.is_signed && (
                <Badge className="bg-green-500/20 text-green-100 border-green-400/30">
                  <CheckCircle2 size={12} className="mr-1" /> Consent Signed
                </Badge>
              )}
              {caseHistory?.is_complete && (
                <Badge className="bg-blue-500/20 text-blue-100 border-blue-400/30">
                  <FileText size={12} className="mr-1" /> Case History Complete
                </Badge>
              )}
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="flex flex-wrap gap-2 mt-4">
            <Button 
              size="sm" 
              variant="secondary"
              className="bg-white/20 hover:bg-white/30 text-white border-0"
              onClick={handleOpenBookAppointment}
              disabled={isReadOnly}
            >
              <CalendarPlus size={14} className="mr-1" /> Book Appointment
            </Button>
            {!isAssistant && (
              <Button 
                size="sm" 
                variant="secondary"
                className="bg-white/20 hover:bg-white/30 text-white border-0"
                onClick={() => navigate('/therapist', { state: { view: 'notes', clientId } })}
                disabled={isReadOnly}
              >
                <PenSquare size={14} className="mr-1" /> Start Session
              </Button>
            )}
          </div>
        </div>
        
        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex overflow-x-auto scrollbar-hide -mb-px">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                    activeTab === tab.id 
                      ? 'border-white text-white' 
                      : 'border-transparent text-white/60 hover:text-white/80'
                  }`}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon size={16} />
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
      
      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Quick Info */}
            <div className="space-y-6">
              {/* Client Details Card */}
              <Card className="p-5">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <User size={18} /> Client Details
                </h3>
                <div className="space-y-3 text-sm">
                  {client.date_of_birth && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Date of Birth</span>
                      <span>{formatDate(client.date_of_birth)}</span>
                    </div>
                  )}
                  {client.gender && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Gender</span>
                      <span className="capitalize">{client.gender}</span>
                    </div>
                  )}
                  {client.address && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Address</span>
                      <span className="text-right max-w-[200px]">{client.address}</span>
                    </div>
                  )}
                  {client.emergency_contact && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Emergency Contact</span>
                      <span>{client.emergency_contact}</span>
                    </div>
                  )}
                </div>
              </Card>
              
              {/* Consent Status Card - Therapist Only */}
              {!isAssistant && (
                <Card className="p-5">
                  <h3 className="font-semibold mb-4">Therapy Consent</h3>
                  {consent?.is_signed ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle2 size={18} />
                      <span>Signed on {formatDate(consent.signature_date)}</span>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-amber-600">
                        <AlertCircle size={18} />
                        <span>Consent not signed</span>
                      </div>
                      <Button size="sm" onClick={() => setShowConsent(true)} disabled={isReadOnly}>
                        View Consent Form
                      </Button>
                    </div>
                  )}
                </Card>
              )}
            </div>
            
            {/* Middle Column - Recent Activity */}
            <div className="space-y-6">
              {/* Upcoming Appointments */}
              <Card className="p-5">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Calendar size={18} /> Upcoming Appointments
                </h3>
                {appointments.filter(a => new Date(a.start_time) > new Date() && a.status !== 'cancelled').length === 0 ? (
                  <p className="text-muted-foreground text-sm">No upcoming appointments</p>
                ) : (
                  <div className="space-y-3">
                    {appointments
                      .filter(a => new Date(a.start_time) > new Date() && a.status !== 'cancelled')
                      .slice(0, 3)
                      .map(appt => (
                        <div key={appt.id} className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                          <div>
                            <p className="font-medium">{formatDate(appt.start_time)}</p>
                            <p className="text-sm text-muted-foreground">{formatTime(appt.start_time)}</p>
                          </div>
                          <Badge variant="outline">{appt.status}</Badge>
                        </div>
                      ))}
                  </div>
                )}
              </Card>
              
              {/* Recent Session Notes - Therapist Only */}
              {!isAssistant && (
                <Card className="p-5">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <PenSquare size={18} /> Recent Notes
                  </h3>
                  {sessionNotes.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No session notes yet</p>
                  ) : (
                    <div className="space-y-3">
                      {sessionNotes.slice(0, 3).map(note => (
                        <div key={note.id} className="p-3 bg-muted/50 rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <p className="font-medium text-sm">{formatDate(note.session_date)}</p>
                            <Badge variant="outline" className="text-xs">{note.note_type || 'SOAP'}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {note.subjective || note.content || 'No content'}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              )}
              
              {/* Recent Payments - Assistant View */}
              {isAssistant && (
                <Card className="p-5">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <DollarSign size={18} /> Recent Payments
                  </h3>
                  {payments.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No payments recorded</p>
                  ) : (
                    <div className="space-y-3">
                      {payments.slice(0, 3).map(payment => (
                        <div key={payment.id} className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                          <div>
                            <p className="font-medium">{formatCurrency(payment.amount)}</p>
                            <p className="text-sm text-muted-foreground">{formatDate(payment.payment_date || payment.created_at)}</p>
                          </div>
                          <Badge variant="outline" className="capitalize">{payment.payment_method || 'cash'}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              )}
            </div>
            
            {/* Right Column - Stats & Case History */}
            <div className="space-y-6">
              {/* Stats - Show different stats for Assistant */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="p-4 text-center">
                  <p className="text-2xl font-bold text-primary">{sessions.length}</p>
                  <p className="text-sm text-muted-foreground">Total Sessions</p>
                </Card>
                {isAssistant ? (
                  <>
                    <Card className="p-4 text-center">
                      <p className="text-2xl font-bold text-primary">{appointments.filter(a => new Date(a.start_time) > new Date() && a.status !== 'cancelled').length}</p>
                      <p className="text-sm text-muted-foreground">Upcoming</p>
                    </Card>
                    <Card className="p-4 text-center">
                      <p className="text-2xl font-bold text-primary">{payments.length}</p>
                      <p className="text-sm text-muted-foreground">Payments</p>
                    </Card>
                  </>
                ) : (
                  <>
                    <Card className="p-4 text-center">
                      <p className="text-2xl font-bold text-primary">{assessments.length}</p>
                      <p className="text-sm text-muted-foreground">Assessments</p>
                    </Card>
                    <Card className="p-4 text-center">
                      <p className="text-2xl font-bold text-primary">{homework.length}</p>
                      <p className="text-sm text-muted-foreground">Homework</p>
                    </Card>
                  </>
                )}
                <Card className="p-4 text-center">
                  <p className="text-2xl font-bold text-primary">
                    {formatCurrency(payments.reduce((sum, p) => sum + (p.amount || 0), 0))}
                  </p>
                  <p className="text-sm text-muted-foreground">Total Paid</p>
                </Card>
              </div>
              
              {/* Case History Quick View - Therapist Only */}
              {!isAssistant && (
                <Card className="p-5">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-semibold flex items-center gap-2">
                      <FileText size={18} /> Case History
                    </h3>
                    <Button size="sm" variant="outline" onClick={() => setShowCaseHistory(true)}>
                      {caseHistory?.is_complete ? 'View' : 'Edit'}
                    </Button>
                  </div>
                  {caseHistory?.is_complete ? (
                    <div className="text-sm text-green-600 flex items-center gap-2">
                      <CheckCircle2 size={16} />
                      Case history completed
                    </div>
                  ) : (
                    <div className="text-sm text-amber-600 flex items-center gap-2">
                      <AlertCircle size={16} />
                      Case history incomplete
                    </div>
                  )}
                </Card>
              )}
            </div>
          </div>
        )}
        
        {/* Case History Tab */}
        {activeTab === 'case-history' && (
          <div className="max-w-4xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Case History</h2>
              <Button onClick={() => setShowCaseHistory(true)} disabled={isReadOnly}>
                <Edit size={16} className="mr-2" /> 
                {caseHistory?.is_complete ? 'View / Edit' : 'Complete Case History'}
              </Button>
            </div>
            
            {caseHistory ? (
              <div className="space-y-6">
                {/* Basic Identification */}
                {caseHistory.basic_identification && Object.keys(caseHistory.basic_identification).length > 0 && (
                  <Card className="p-5">
                    <h3 className="font-semibold mb-4">Basic Identification</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                      {Object.entries(caseHistory.basic_identification).map(([key, value]) => value && (
                        <div key={key}>
                          <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}: </span>
                          <span>{value}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
                
                {/* Presenting Complaints */}
                {caseHistory.presenting_complaints && Object.keys(caseHistory.presenting_complaints).length > 0 && (
                  <Card className="p-5">
                    <h3 className="font-semibold mb-4">Presenting Complaints</h3>
                    <div className="space-y-3 text-sm">
                      {caseHistory.presenting_complaints.main_problems && (
                        <div>
                          <span className="text-muted-foreground">Main Problems: </span>
                          <p className="mt-1">{caseHistory.presenting_complaints.main_problems}</p>
                        </div>
                      )}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {caseHistory.presenting_complaints.duration && (
                          <div>
                            <span className="text-muted-foreground">Duration: </span>
                            {caseHistory.presenting_complaints.duration}
                          </div>
                        )}
                        {caseHistory.presenting_complaints.severity && (
                          <div>
                            <span className="text-muted-foreground">Severity: </span>
                            {caseHistory.presenting_complaints.severity}
                          </div>
                        )}
                        {caseHistory.presenting_complaints.frequency && (
                          <div>
                            <span className="text-muted-foreground">Frequency: </span>
                            {caseHistory.presenting_complaints.frequency}
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                )}
                
                {/* Other sections summary */}
                {['history_of_present_illness', 'past_psychiatric_history', 'medical_history', 'family_history', 'personal_developmental_history', 'mental_status_examination', 'provisional_formulation', 'initial_therapy_plan'].map(section => {
                  const sectionData = caseHistory[section];
                  if (!sectionData || Object.keys(sectionData).length === 0) return null;
                  
                  return (
                    <Card key={section} className="p-5">
                      <h3 className="font-semibold mb-4 capitalize">{section.replace(/_/g, ' ')}</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                        {Object.entries(sectionData).slice(0, 6).map(([key, value]) => value && (
                          <div key={key}>
                            <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}: </span>
                            <span>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <Card className="p-8 text-center">
                <FileText size={48} className="mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">No case history recorded yet</p>
                <Button onClick={() => setShowCaseHistory(true)} disabled={isReadOnly}>
                  Start Case History
                </Button>
              </Card>
            )}
          </div>
        )}
        
        {/* Sessions Tab */}
        {activeTab === 'sessions' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Sessions & Appointments</h2>
              <Button onClick={() => setShowBookAppointment(true)} disabled={isReadOnly}>
                <Plus size={16} className="mr-2" /> Book Appointment
              </Button>
            </div>
            
            {appointments.length === 0 ? (
              <Card className="p-8 text-center">
                <Calendar size={48} className="mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">No appointments scheduled</p>
                <Button onClick={() => setShowBookAppointment(true)} disabled={isReadOnly}>
                  Book First Appointment
                </Button>
              </Card>
            ) : (
              <div className="space-y-4">
                {appointments.map(appt => (
                  <Card key={appt.id} className="p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <Calendar size={16} className="text-muted-foreground" />
                          <span className="font-medium">{formatDate(appt.start_time)}</span>
                          <span className="text-muted-foreground">at {formatTime(appt.start_time)}</span>
                        </div>
                        {appt.notes && (
                          <p className="text-sm text-muted-foreground">{appt.notes}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={appt.status === 'completed' ? 'default' : 'outline'}>
                          {appt.status}
                        </Badge>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Session Notes Tab */}
        {activeTab === 'notes' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Session Notes</h2>
              {!isAssistant && (
                <Button 
                  onClick={() => navigate('/therapist', { state: { view: 'notes', clientId } })}
                  disabled={isReadOnly}
                >
                  <Plus size={16} className="mr-2" /> New Note
                </Button>
              )}
            </div>
            
            {sessionNotes.length === 0 ? (
              <Card className="p-8 text-center">
                <PenSquare size={48} className="mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">No session notes yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {sessionNotes.map(note => (
                  <Card key={note.id} className="p-5">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <p className="font-semibold">{formatDate(note.session_date)}</p>
                        <p className="text-sm text-muted-foreground">Session #{note.session_number || 'N/A'}</p>
                      </div>
                      <Badge>{note.note_type || 'SOAP'}</Badge>
                    </div>
                    
                    {note.note_type === 'SOAP' || !note.note_type ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        {note.subjective && (
                          <div>
                            <p className="font-medium text-muted-foreground mb-1">Subjective</p>
                            <p>{note.subjective}</p>
                          </div>
                        )}
                        {note.objective && (
                          <div>
                            <p className="font-medium text-muted-foreground mb-1">Objective</p>
                            <p>{note.objective}</p>
                          </div>
                        )}
                        {note.assessment && (
                          <div>
                            <p className="font-medium text-muted-foreground mb-1">Assessment</p>
                            <p>{note.assessment}</p>
                          </div>
                        )}
                        {note.plan && (
                          <div>
                            <p className="font-medium text-muted-foreground mb-1">Plan</p>
                            <p>{note.plan}</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm">{note.content}</p>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Assessments Tab */}
        {activeTab === 'assessments' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Assessments</h2>
            </div>
            
            {assessments.length === 0 ? (
              <Card className="p-8 text-center">
                <ClipboardList size={48} className="mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No assessments completed yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {/* Trend Chart */}
                <AssessmentTrendChart assessments={assessments} />
                
                {/* Assessment List */}
                {assessments.map(assessment => (
                  <Card key={assessment.id} className="p-5">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold">{assessment.assessment_type || assessment.type}</p>
                        <p className="text-sm text-muted-foreground">{formatDate(assessment.completed_at || assessment.created_at)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-primary">{assessment.total_score || assessment.score}</p>
                        <p className="text-sm text-muted-foreground">Score</p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Homework Tab */}
        {activeTab === 'homework' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Homework & Assignments</h2>
            </div>
            
            {homework.length === 0 ? (
              <Card className="p-8 text-center">
                <BookOpen size={48} className="mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No homework assigned yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {homework.map(hw => (
                  <Card key={hw.id} className="p-5">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold">{hw.title}</p>
                        <p className="text-sm text-muted-foreground mt-1">{hw.description}</p>
                        <p className="text-xs text-muted-foreground mt-2">
                          Assigned: {formatDate(hw.assigned_date || hw.created_at)}
                        </p>
                      </div>
                      <Badge variant={hw.status === 'completed' ? 'default' : 'outline'}>
                        {hw.status || 'pending'}
                      </Badge>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Payments Tab */}
        {activeTab === 'payments' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Payment History</h2>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Total Collected</p>
                <p className="text-xl font-bold text-primary">
                  {formatCurrency(payments.reduce((sum, p) => sum + (p.amount || 0), 0))}
                </p>
              </div>
            </div>
            
            {payments.length === 0 ? (
              <Card className="p-8 text-center">
                <DollarSign size={48} className="mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No payments recorded yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {payments.map(payment => (
                  <Card key={payment.id} className="p-5">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-semibold">{formatCurrency(payment.amount)}</p>
                        <p className="text-sm text-muted-foreground">{formatDate(payment.payment_date || payment.created_at)}</p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline" className="capitalize">{payment.payment_method || 'cash'}</Badge>
                        {payment.receipt_number && (
                          <p className="text-xs text-muted-foreground mt-1">#{payment.receipt_number}</p>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Case History Modal */}
      {showCaseHistory && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-4xl bg-background rounded-lg shadow-xl overflow-hidden" style={{ height: '90vh' }}>
            <CaseHistoryForm
              clientId={clientId}
              clientName={client.full_name}
              isReadOnly={isReadOnly}
              onComplete={() => {
                setShowCaseHistory(false);
                fetchClientData();
              }}
              onClose={() => setShowCaseHistory(false)}
            />
          </div>
        </div>
      )}
      
      {/* Consent Dialog */}
      <Dialog open={showConsent} onOpenChange={setShowConsent}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Therapy Consent</DialogTitle>
          </DialogHeader>
          <TherapyConsent
            clientId={clientId}
            clientName={client.full_name}
            isReadOnly={isReadOnly}
            onComplete={() => {
              setShowConsent(false);
              fetchClientData();
            }}
          />
        </DialogContent>
      </Dialog>
      
      {/* Book Appointment Dialog */}
      <Dialog open={showBookAppointment} onOpenChange={setShowBookAppointment}>
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
                disabled={!selectedSlot || isReadOnly}
                className="flex-1"
                data-testid="confirm-book-appointment"
              >
                Book Appointment
              </Button>
              <Button type="button" variant="outline" onClick={() => setShowBookAppointment(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ClientProfilePage;
