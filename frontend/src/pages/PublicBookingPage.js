import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Calendar } from '../components/ui/calendar';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  CalendarDays, Clock, User, Mail, Phone, CheckCircle2, 
  AlertCircle, ArrowLeft, ArrowRight, Loader2, MapPin,
  Award, Briefcase
} from 'lucide-react';
import { format, addDays, isSameDay, parseISO, startOfDay } from 'date-fns';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PublicBookingPage = () => {
  const { therapistId } = useParams();
  const navigate = useNavigate();
  
  // Step management
  const [step, setStep] = useState(1); // 1: Select Slot, 2: Enter Details, 3: Confirmation
  
  // Therapist data
  const [therapist, setTherapist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Slot selection
  const [selectedDate, setSelectedDate] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  
  // Client details form
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    mobile: '',
    gender: '',
    date_of_birth: '',
    notes: ''
  });
  
  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [bookingResult, setBookingResult] = useState(null);

  // Fetch therapist profile
  useEffect(() => {
    const fetchTherapist = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/public/therapist/${therapistId}`);
        setTherapist(res.data);
        setError(null);
      } catch (err) {
        if (err.response?.status === 403) {
          setError('Public booking is not available for this therapist');
        } else if (err.response?.status === 404) {
          setError('Therapist not found');
        } else {
          setError('Failed to load therapist information');
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchTherapist();
  }, [therapistId]);

  // Fetch available slots when date changes
  useEffect(() => {
    if (!selectedDate || !therapist) return;
    
    const fetchSlots = async () => {
      setLoadingSlots(true);
      try {
        const dateStr = format(selectedDate, 'yyyy-MM-dd');
        const res = await axios.get(`${BACKEND_URL}/api/public/therapist/${therapistId}/slots?date=${dateStr}`);
        setAvailableSlots(res.data.slots || []);
      } catch (err) {
        toast.error('Failed to load available slots');
        setAvailableSlots([]);
      } finally {
        setLoadingSlots(false);
      }
    };
    
    fetchSlots();
  }, [selectedDate, therapistId, therapist]);

  // Group slots by date
  const slotsByDate = useMemo(() => {
    const grouped = {};
    availableSlots.forEach(slot => {
      const date = slot.start.split('T')[0];
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(slot);
    });
    return grouped;
  }, [availableSlots]);

  // Get slots for selected date
  const slotsForSelectedDate = useMemo(() => {
    if (!selectedDate) return [];
    const dateStr = format(selectedDate, 'yyyy-MM-dd');
    return availableSlots.filter(slot => slot.start.startsWith(dateStr));
  }, [selectedDate, availableSlots]);

  const handleDateSelect = (date) => {
    setSelectedDate(date);
    setSelectedSlot(null);
  };

  const handleSlotSelect = (slot) => {
    setSelectedSlot(slot);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    // Validate form
    if (!formData.full_name.trim()) {
      toast.error('Please enter your name');
      return;
    }
    if (!formData.email.trim() || !/\S+@\S+\.\S+/.test(formData.email)) {
      toast.error('Please enter a valid email');
      return;
    }
    if (!formData.mobile.trim() || formData.mobile.length < 10) {
      toast.error('Please enter a valid mobile number');
      return;
    }
    
    setSubmitting(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/public/book`, {
        therapist_id: therapistId,
        slot_start: selectedSlot.start,
        slot_end: selectedSlot.end,
        full_name: formData.full_name.trim(),
        email: formData.email.trim(),
        mobile: formData.mobile.trim(),
        gender: formData.gender || null,
        date_of_birth: formData.date_of_birth || null,
        notes: formData.notes.trim() || null
      });
      
      setBookingResult(res.data);
      setBookingSuccess(true);
      setStep(3);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit booking');
    } finally {
      setSubmitting(false);
    }
  };

  // Calculate available dates (next 30 days)
  const availableDates = useMemo(() => {
    const dates = [];
    for (let i = 0; i < 30; i++) {
      dates.push(addDays(new Date(), i));
    }
    return dates;
  }, []);

  // Format time from ISO string
  const formatSlotTime = (isoString) => {
    try {
      const date = parseISO(isoString);
      return format(date, 'h:mm a');
    } catch {
      return isoString;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary/5 to-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-10 w-10 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-primary/5 to-background flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-8 text-center">
          <AlertCircle className="h-16 w-16 text-destructive mx-auto mb-4" />
          <h1 className="text-xl font-semibold mb-2">Booking Unavailable</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Button onClick={() => navigate('/')} variant="outline">
            Go to Homepage
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary/5 to-background" data-testid="public-booking-page">
      {/* Header */}
      <header className="bg-white border-b border-border sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <img src="/logo-symbol.png" alt="COGNISPACE" className="h-8 w-auto" />
            <span className="font-serif text-xl text-primary">COGNISPACE</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 lg:py-10">
        {/* Step Indicator */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center gap-2">
            {[1, 2, 3].map((s) => (
              <React.Fragment key={s}>
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                    step >= s ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'
                  }`}
                >
                  {step > s ? <CheckCircle2 size={16} /> : s}
                </div>
                {s < 3 && (
                  <div className={`w-12 h-1 rounded ${step > s ? 'bg-primary' : 'bg-muted'}`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Therapist Info Card */}
        <Card className="p-5 lg:p-6 mb-6" data-testid="therapist-info-card">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary">
              <User size={28} />
            </div>
            <div className="flex-1">
              <h1 className="text-xl lg:text-2xl font-semibold text-foreground">{therapist?.name}</h1>
              {therapist?.clinic_name && (
                <p className="text-muted-foreground flex items-center gap-1 mt-1">
                  <MapPin size={14} />
                  {therapist.clinic_name}
                </p>
              )}
              <div className="flex flex-wrap gap-2 mt-2">
                {therapist?.qualifications && (
                  <Badge variant="secondary" className="gap-1">
                    <Award size={12} />
                    {therapist.qualifications}
                  </Badge>
                )}
                {therapist?.session_duration && (
                  <Badge variant="outline" className="gap-1">
                    <Clock size={12} />
                    {therapist.session_duration} min session
                  </Badge>
                )}
              </div>
              {therapist?.specializations?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {therapist.specializations.map((spec, idx) => (
                    <span key={idx} className="text-xs bg-muted px-2 py-1 rounded">{spec}</span>
                  ))}
                </div>
              )}
            </div>
            {therapist?.consultation_fee > 0 && (
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Consultation Fee</p>
                <p className="text-xl font-bold text-primary">₹{therapist.consultation_fee}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Step 1: Select Slot */}
        {step === 1 && (
          <Card className="p-5 lg:p-6" data-testid="step-1-select-slot">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CalendarDays className="text-primary" size={20} />
              Select Date & Time
            </h2>
            
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Calendar */}
              <div>
                <Label className="mb-2 block">Select a date</Label>
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={handleDateSelect}
                  disabled={(date) => date < startOfDay(new Date())}
                  className="rounded-md border"
                />
              </div>
              
              {/* Time Slots */}
              <div>
                <Label className="mb-2 block">
                  {selectedDate 
                    ? `Available times on ${format(selectedDate, 'MMM d, yyyy')}`
                    : 'Select a date to see available times'
                  }
                </Label>
                
                {loadingSlots ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : selectedDate ? (
                  slotsForSelectedDate.length > 0 ? (
                    <div className="grid grid-cols-3 gap-2 max-h-[300px] overflow-y-auto">
                      {slotsForSelectedDate.map((slot, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSlotSelect(slot)}
                          className={`p-3 rounded-lg border-2 text-sm font-medium transition-all ${
                            selectedSlot?.start === slot.start
                              ? 'border-primary bg-primary text-white'
                              : 'border-border hover:border-primary/50'
                          }`}
                          data-testid={`time-slot-${idx}`}
                        >
                          {slot.display || formatSlotTime(slot.start)}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      <Clock size={40} className="mx-auto mb-2 opacity-50" />
                      <p>No available slots for this date</p>
                      <p className="text-sm">Please select another date</p>
                    </div>
                  )
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <CalendarDays size={40} className="mx-auto mb-2 opacity-50" />
                    <p>Select a date from the calendar</p>
                  </div>
                )}
              </div>
            </div>
            
            {/* Selected slot summary */}
            {selectedSlot && (
              <div className="mt-6 p-4 bg-primary/5 rounded-lg border border-primary/20">
                <p className="text-sm text-muted-foreground">Selected appointment</p>
                <p className="font-semibold text-primary">
                  {selectedDate && format(selectedDate, 'EEEE, MMMM d, yyyy')} at {formatSlotTime(selectedSlot.start)}
                </p>
              </div>
            )}
            
            <div className="mt-6 flex justify-end">
              <Button 
                onClick={() => setStep(2)} 
                disabled={!selectedSlot}
                className="gap-2"
                data-testid="continue-to-details"
              >
                Continue
                <ArrowRight size={16} />
              </Button>
            </div>
          </Card>
        )}

        {/* Step 2: Enter Details */}
        {step === 2 && (
          <Card className="p-5 lg:p-6" data-testid="step-2-details">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <User className="text-primary" size={20} />
              Your Details
            </h2>
            
            {/* Appointment Summary */}
            <div className="mb-6 p-4 bg-muted/50 rounded-lg">
              <p className="text-sm text-muted-foreground">Your appointment</p>
              <p className="font-semibold">
                {selectedDate && format(selectedDate, 'EEEE, MMMM d, yyyy')} at {formatSlotTime(selectedSlot?.start)}
              </p>
              <button 
                onClick={() => setStep(1)} 
                className="text-sm text-primary hover:underline mt-1"
              >
                Change time
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  placeholder="Enter your full name"
                  className="mt-1"
                  data-testid="input-full-name"
                />
              </div>
              
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="your@email.com"
                    className="mt-1"
                    data-testid="input-email"
                  />
                </div>
                <div>
                  <Label htmlFor="mobile">Mobile Number *</Label>
                  <Input
                    id="mobile"
                    name="mobile"
                    type="tel"
                    value={formData.mobile}
                    onChange={handleInputChange}
                    placeholder="10-digit mobile number"
                    className="mt-1"
                    data-testid="input-mobile"
                  />
                </div>
              </div>
              
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="gender">Gender</Label>
                  <Select 
                    value={formData.gender} 
                    onValueChange={(val) => setFormData(prev => ({ ...prev, gender: val }))}
                  >
                    <SelectTrigger className="mt-1" data-testid="select-gender">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">Male</SelectItem>
                      <SelectItem value="female">Female</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                      <SelectItem value="prefer_not_to_say">Prefer not to say</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="date_of_birth">Date of Birth</Label>
                  <Input
                    id="date_of_birth"
                    name="date_of_birth"
                    type="date"
                    value={formData.date_of_birth}
                    onChange={handleInputChange}
                    className="mt-1"
                    data-testid="input-dob"
                  />
                </div>
              </div>
              
              <div>
                <Label htmlFor="notes">Additional Notes (Optional)</Label>
                <Textarea
                  id="notes"
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  placeholder="Any specific concerns or information for the therapist..."
                  className="mt-1"
                  rows={3}
                  data-testid="input-notes"
                />
              </div>
            </div>
            
            <div className="mt-6 flex justify-between">
              <Button variant="outline" onClick={() => setStep(1)} className="gap-2">
                <ArrowLeft size={16} />
                Back
              </Button>
              <Button 
                onClick={handleSubmit} 
                disabled={submitting}
                className="gap-2"
                data-testid="submit-booking"
              >
                {submitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Confirm Booking
                    <CheckCircle2 size={16} />
                  </>
                )}
              </Button>
            </div>
          </Card>
        )}

        {/* Step 3: Confirmation */}
        {step === 3 && bookingSuccess && (
          <Card className="p-6 lg:p-8 text-center" data-testid="step-3-confirmation">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="h-10 w-10 text-green-600" />
            </div>
            
            <h2 className="text-2xl font-semibold text-foreground mb-2">Booking Request Submitted!</h2>
            <p className="text-muted-foreground mb-6">
              Your appointment request has been sent to {therapist?.name}. You will receive a confirmation once approved.
            </p>
            
            <div className="bg-muted/50 rounded-lg p-4 mb-6 text-left max-w-sm mx-auto">
              <h3 className="font-medium mb-3">Appointment Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Date</span>
                  <span className="font-medium">{selectedDate && format(selectedDate, 'MMM d, yyyy')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Time</span>
                  <span className="font-medium">{formatSlotTime(selectedSlot?.start)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Therapist</span>
                  <span className="font-medium">{therapist?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Status</span>
                  <Badge className="bg-amber-100 text-amber-700 border-amber-200">Pending Approval</Badge>
                </div>
              </div>
            </div>
            
            {bookingResult?.is_new_client && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left max-w-sm mx-auto">
                <h3 className="font-medium text-blue-800 mb-2">Account Created!</h3>
                <p className="text-sm text-blue-700">
                  A new account has been created for you. Check your email for login credentials.
                </p>
              </div>
            )}
            
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button variant="outline" onClick={() => navigate('/login')}>
                Go to Login
              </Button>
              <Button onClick={() => {
                setStep(1);
                setSelectedSlot(null);
                setFormData({ full_name: '', email: '', mobile: '', gender: '', date_of_birth: '', notes: '' });
                setBookingSuccess(false);
              }}>
                Book Another Appointment
              </Button>
            </div>
          </Card>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-border mt-12 py-6">
        <div className="max-w-4xl mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} COGNISPACE. All rights reserved.</p>
          <div className="flex justify-center gap-4 mt-2">
            <a href="/privacy-policy" className="hover:text-primary">Privacy Policy</a>
            <a href="/terms-conditions" className="hover:text-primary">Terms & Conditions</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PublicBookingPage;
