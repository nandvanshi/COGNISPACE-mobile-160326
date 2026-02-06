import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { toast } from 'sonner';
import { Ban, CheckCircle, Key, Plus, Edit, Users, Eye, Calendar, CreditCard, RefreshCw, Search, X, MapPin, Loader2, Building2, Trash2 } from 'lucide-react';
import { formatDate, formatCurrency } from '../../utils/formatUtils';

// Available specializations
const SPECIALIZATION_OPTIONS = [
  "Clinical Psychology", "Counseling Psychology", "Child & Adolescent Therapy",
  "Marriage & Family Therapy", "CBT", "DBT", "Trauma & PTSD", "Anxiety Disorders",
  "Depression", "Addiction & Substance Abuse", "Eating Disorders", "OCD",
  "Grief Counseling", "Stress Management", "Anger Management", "Career Counseling",
  "Relationship Issues", "Mindfulness", "Neuropsychology", "Art Therapy"
];

const TherapistManagement = ({ onViewClients }) => {
  const [therapists, setTherapists] = useState([]);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showClientsDialog, setShowClientsDialog] = useState(false);
  const [showSubscriptionDialog, setShowSubscriptionDialog] = useState(false);
  const [selectedTherapist, setSelectedTherapist] = useState(null);
  const [therapistDetail, setTherapistDetail] = useState(null);
  const [therapistClients, setTherapistClients] = useState([]);
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [extendDays, setExtendDays] = useState(30);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSpecDropdown, setShowSpecDropdown] = useState(false);
  const [newTherapist, setNewTherapist] = useState({
    mobile: '',
    email: '',
    full_name: '',
    password: '',
    qualifications: '',
    specializations: [],
    years_of_experience: '',
    clinic_name: '',
    fee_slots: [{ amount: '', duration_minutes: 50 }],
    address_line_1: '',
    address_line_2: '',
    pincode: '',
    city: '',
    state: '',
    district: ''
  });
  const [editData, setEditData] = useState({
    full_name: '',
    email: '',
    qualifications: '',
    specializations: [],
    years_of_experience: '',
    profile_photo: '',
    clinic_name: '',
    address_line_1: '',
    address_line_2: '',
    pincode: '',
    city: '',
    state: '',
    district: '',
    google_maps_link: ''
  });
  const [showEditSpecDropdown, setShowEditSpecDropdown] = useState(false);
  const [pincodeLoading, setPincodeLoading] = useState(false);

  useEffect(() => {
    fetchTherapists();
    fetchSubscriptionPlans();
  }, []);

  const fetchTherapists = async () => {
    try {
      const response = await axios.get(`${API}/admin/therapists`);
      setTherapists(response.data);
    } catch (error) {
      toast.error('Failed to load therapists');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscriptionPlans = async () => {
    try {
      const response = await axios.get(`${API}/admin/subscription-plans`);
      setSubscriptionPlans(response.data);
    } catch (error) {
      console.error('Failed to load subscription plans');
    }
  };

  const handleSuspend = async (therapistId) => {
    if (!window.confirm('Are you sure you want to suspend this therapist?')) return;
    try {
      await axios.post(`${API}/admin/therapists/${therapistId}/suspend`);
      toast.success('Therapist suspended');
      fetchTherapists();
    } catch (error) {
      toast.error('Failed to suspend therapist');
    }
  };

  const handleActivate = async (therapistId) => {
    try {
      await axios.post(`${API}/admin/therapists/${therapistId}/activate`);
      toast.success('Therapist activated');
      fetchTherapists();
    } catch (error) {
      toast.error('Failed to activate therapist');
    }
  };

  const handleDeleteTherapist = async (therapist) => {
    const confirmMessage = `⚠️ WARNING: This will permanently delete therapist "${therapist.full_name}" and ALL associated data:\n\n` +
      `• Profile & Settings\n` +
      `• All Appointments\n` +
      `• All Session Notes\n` +
      `• All Assessments & Reports\n` +
      `• All Payments\n` +
      `• All Client Associations\n\n` +
      `Mobile: ${therapist.mobile}\n` +
      `Email: ${therapist.email || 'N/A'}\n\n` +
      `This action CANNOT be undone. The mobile/email can be used for new registration after deletion.\n\n` +
      `Type "DELETE" to confirm:`;
    
    const userInput = window.prompt(confirmMessage);
    if (userInput !== 'DELETE') {
      if (userInput !== null) {
        toast.error('Deletion cancelled - you must type DELETE to confirm');
      }
      return;
    }
    
    try {
      const res = await axios.delete(`${API}/admin/therapists/${therapist.id}`);
      toast.success(res.data.message || 'Therapist deleted successfully');
      fetchTherapists();
      setShowDetailDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete therapist');
    }
  };

  const handleResetPassword = (therapist) => {
    setSelectedTherapist(therapist);
    setNewPassword(generatePassword());
    setShowPasswordDialog(true);
  };

  const generatePassword = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
    let password = '';
    for (let i = 0; i < 10; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
  };

  const confirmPasswordReset = async () => {
    try {
      await axios.post(`${API}/admin/therapists/${selectedTherapist.id}/reset-password?new_password=${newPassword}`);
      toast.success(`Password reset! New password: ${newPassword}`);
      setShowPasswordDialog(false);
    } catch (error) {
      toast.error('Failed to reset password');
    }
  };

  const handleCreateTherapist = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!newTherapist.specializations || newTherapist.specializations.length === 0) {
      toast.error('Please select at least 1 specialization');
      return;
    }
    
    const validFeeSlots = newTherapist.fee_slots.filter(slot => slot.amount && slot.duration_minutes);
    if (validFeeSlots.length === 0) {
      toast.error('Please add at least one consultation fee');
      return;
    }
    
    try {
      const payload = {
        ...newTherapist,
        years_of_experience: newTherapist.years_of_experience ? parseInt(newTherapist.years_of_experience) : null,
        fee_slots: validFeeSlots.map(slot => ({
          amount: parseFloat(slot.amount),
          duration_minutes: parseInt(slot.duration_minutes)
        }))
      };
      await axios.post(`${API}/admin/therapists/create`, payload);
      toast.success('Therapist created with 30-day trial subscription');
      setShowCreateDialog(false);
      setShowSpecDropdown(false);
      setNewTherapist({
        mobile: '', email: '', full_name: '', password: '',
        qualifications: '', specializations: [], years_of_experience: '',
        clinic_name: '', fee_slots: [{ amount: '', duration_minutes: 50 }],
        address_line_1: '', address_line_2: '', pincode: '', city: '', state: '', district: ''
      });
      fetchTherapists();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create therapist');
    }
  };

  const handleEditClick = async (therapist) => {
    try {
      // Fetch full therapist details to get all profile data
      const response = await axios.get(`${API}/admin/therapists/${therapist.id}`);
      const fullData = response.data;
      
      setSelectedTherapist(therapist);
      setEditData({
        full_name: fullData.full_name || '',
        email: fullData.email || '',
        qualifications: fullData.qualifications || '',
        specializations: fullData.specializations || [],
        years_of_experience: fullData.years_of_experience || '',
        profile_photo: fullData.profile_photo || '',
        clinic_name: fullData.clinic_name || '',
        address_line_1: fullData.address_line_1 || '',
        address_line_2: fullData.address_line_2 || '',
        pincode: fullData.pincode || '',
        city: fullData.city || '',
        state: fullData.state || '',
        district: fullData.district || '',
        google_maps_link: fullData.google_maps_link || ''
      });
      setShowEditDialog(true);
    } catch (error) {
      toast.error('Failed to load therapist details for editing');
    }
  };

  const handleUpdateTherapist = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        full_name: editData.full_name,
        email: editData.email,
        qualifications: editData.qualifications,
        specializations: editData.specializations,
        years_of_experience: editData.years_of_experience ? parseInt(editData.years_of_experience) : null,
        profile_photo: editData.profile_photo,
        clinic_name: editData.clinic_name,
        address_line_1: editData.address_line_1,
        address_line_2: editData.address_line_2,
        pincode: editData.pincode,
        city: editData.city,
        state: editData.state,
        district: editData.district
      };
      await axios.put(`${API}/admin/therapists/${selectedTherapist.id}`, payload);
      toast.success('Therapist updated successfully');
      setShowEditDialog(false);
      setShowEditSpecDropdown(false);
      fetchTherapists();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update therapist');
    }
  };
  
  // Edit specialization handlers
  const toggleEditSpecialization = (spec) => {
    setEditData(prev => {
      const current = prev.specializations || [];
      if (current.includes(spec)) {
        return { ...prev, specializations: current.filter(s => s !== spec) };
      } else if (current.length < 5) {
        return { ...prev, specializations: [...current, spec] };
      } else {
        toast.error('Maximum 5 specializations allowed');
        return prev;
      }
    });
  };

  const removeEditSpecialization = (spec) => {
    setEditData(prev => ({
      ...prev,
      specializations: (prev.specializations || []).filter(s => s !== spec)
    }));
  };

  const handleViewDetail = async (therapist) => {
    try {
      const response = await axios.get(`${API}/admin/therapists/${therapist.id}`);
      setTherapistDetail(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      toast.error('Failed to load therapist details');
    }
  };

  const handleViewClients = async (therapist) => {
    try {
      const response = await axios.get(`${API}/admin/therapists/${therapist.id}/clients`);
      setTherapistClients(response.data);
      setSelectedTherapist(therapist);
      setShowClientsDialog(true);
    } catch (error) {
      toast.error('Failed to load clients');
    }
  };

  const handleManageSubscription = (therapist) => {
    setSelectedTherapist(therapist);
    setSelectedPlanId('');
    setExtendDays(30);
    setShowSubscriptionDialog(true);
  };

  const handleAssignTrial = async () => {
    try {
      await axios.post(`${API}/admin/therapists/${selectedTherapist.id}/assign-trial`);
      toast.success('30-day trial subscription assigned');
      setShowSubscriptionDialog(false);
      fetchTherapists();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign trial');
    }
  };

  const handleAssignPlan = async () => {
    if (!selectedPlanId) {
      toast.error('Please select a subscription plan');
      return;
    }
    try {
      await axios.post(`${API}/admin/therapists/${selectedTherapist.id}/assign-subscription`, {
        plan_id: selectedPlanId
      });
      toast.success('Subscription plan assigned successfully');
      setShowSubscriptionDialog(false);
      fetchTherapists();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign subscription');
    }
  };

  const handleExtendSubscription = async () => {
    try {
      await axios.post(`${API}/admin/therapists/${selectedTherapist.id}/extend-subscription`, {
        additional_days: extendDays
      });
      toast.success(`Subscription extended by ${extendDays} days`);
      setShowSubscriptionDialog(false);
      fetchTherapists();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to extend subscription');
    }
  };

  const handleMigrateSubscriptions = async () => {
    if (!window.confirm('This will assign a 30-day trial to all therapists without subscriptions. Continue?')) return;
    try {
      const response = await axios.post(`${API}/admin/migrate-subscriptions`);
      toast.success(response.data.message);
      fetchTherapists();
    } catch (error) {
      toast.error('Failed to migrate subscriptions');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString();
  };

  const getRemainingDays = (endDateStr) => {
    if (!endDateStr) return null;
    const endDate = new Date(endDateStr);
    const today = new Date();
    const diffTime = endDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  // Pincode lookup function
  const lookupPincode = async (pincode, isEdit = false) => {
    if (!pincode || pincode.length !== 6) return;
    
    setPincodeLoading(true);
    try {
      const response = await axios.get(`${API}/therapist/pincode/${pincode}`);
      if (isEdit) {
        setEditData(prev => ({
          ...prev,
          city: response.data.city,
          state: response.data.state,
          district: response.data.district
        }));
      } else {
        setNewTherapist(prev => ({
          ...prev,
          city: response.data.city,
          state: response.data.state,
          district: response.data.district
        }));
      }
      toast.success('Address auto-filled from pincode');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Pincode not found');
    } finally {
      setPincodeLoading(false);
    }
  };

  const handlePincodeChange = (value, isEdit = false) => {
    const cleanValue = value.replace(/\D/g, '').slice(0, 6);
    if (isEdit) {
      setEditData(prev => ({ ...prev, pincode: cleanValue }));
    } else {
      setNewTherapist(prev => ({ ...prev, pincode: cleanValue }));
    }
    
    // Auto-lookup when 6 digits entered
    if (cleanValue.length === 6) {
      lookupPincode(cleanValue, isEdit);
    }
  };

  // Specialization handlers
  const toggleSpecialization = (spec) => {
    setNewTherapist(prev => {
      const current = prev.specializations || [];
      if (current.includes(spec)) {
        return { ...prev, specializations: current.filter(s => s !== spec) };
      } else if (current.length < 5) {
        return { ...prev, specializations: [...current, spec] };
      } else {
        toast.error('Maximum 5 specializations allowed');
        return prev;
      }
    });
  };

  const removeSpecialization = (spec) => {
    setNewTherapist(prev => ({
      ...prev,
      specializations: (prev.specializations || []).filter(s => s !== spec)
    }));
  };

  // Fee slot handlers
  const addFeeSlot = () => {
    if (newTherapist.fee_slots.length >= 5) {
      toast.error('Maximum 5 fee options allowed');
      return;
    }
    setNewTherapist(prev => ({
      ...prev,
      fee_slots: [...prev.fee_slots, { amount: '', duration_minutes: 30 }]
    }));
  };

  const updateFeeSlot = (index, field, value) => {
    setNewTherapist(prev => {
      const newSlots = [...prev.fee_slots];
      newSlots[index] = { ...newSlots[index], [field]: value };
      return { ...prev, fee_slots: newSlots };
    });
  };

  const removeFeeSlot = (index) => {
    if (newTherapist.fee_slots.length <= 1) {
      toast.error('At least one fee option required');
      return;
    }
    setNewTherapist(prev => ({
      ...prev,
      fee_slots: prev.fee_slots.filter((_, i) => i !== index)
    }));
  };

  const getSubscriptionBadge = (therapist) => {
    if (!therapist.subscription_status) {
      return <span className="px-2 py-1 bg-error/10 text-error text-xs rounded-full">No Subscription</span>;
    }
    const colors = {
      trial: 'bg-info/10 text-info',
      active: 'bg-success/10 text-success',
      expired: 'bg-error/10 text-error',
      cancelled: 'bg-warning/10 text-warning'
    };
    return (
      <span className={`px-2 py-1 ${colors[therapist.subscription_status] || 'bg-muted text-muted-foreground'} text-xs rounded-full`}>
        {therapist.subscription_status} {therapist.subscription_plan ? `(${therapist.subscription_plan})` : ''}
      </span>
    );
  };

  // Filter therapists based on search query (name, email, mobile)
  const filteredTherapists = useMemo(() => {
    if (!searchQuery.trim()) return therapists;
    const query = searchQuery.toLowerCase().trim();
    return therapists.filter((therapist) => {
      const fullName = (therapist.full_name || '').toLowerCase();
      const email = (therapist.email || '').toLowerCase();
      const mobile = (therapist.mobile || '').toLowerCase();
      const credentials = (therapist.credentials || '').toLowerCase();
      return fullName.includes(query) || email.includes(query) || mobile.includes(query) || credentials.includes(query);
    });
  }, [therapists, searchQuery]);

  if (loading) {
    return <div className="text-center py-12">Loading therapists...</div>;
  }

  return (
    <div data-testid="therapist-management">
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Therapist Management</h2>
          <p className="text-muted-foreground">Manage therapist accounts and subscriptions</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleMigrateSubscriptions}
            variant="outline"
            data-testid="migrate-subscriptions-button"
          >
            <RefreshCw size={16} className="mr-2" />
            Fix Missing Subscriptions
          </Button>
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="add-therapist-button"
          >
            <Plus size={20} className="mr-2" />
            Add Therapist
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search by name, email, mobile, or credentials..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-10"
            data-testid="therapist-search-input"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              data-testid="clear-search-button"
            >
              <X size={16} />
            </button>
          )}
        </div>
        {searchQuery && (
          <p className="text-sm text-muted-foreground mt-2" data-testid="search-results-count">
            Showing {filteredTherapists.length} of {therapists.length} therapist{therapists.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filteredTherapists.map((therapist) => {
          const remainingDays = getRemainingDays(therapist.subscription_end_date);
          return (
            <Card
              key={therapist.id}
              className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
              data-testid={`therapist-${therapist.id}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex gap-4">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                    {therapist.profile_photo ? (
                      <img src={therapist.profile_photo} alt={therapist.full_name} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-2xl font-bold text-primary">{therapist.full_name?.charAt(0)}</span>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h4 className="text-lg font-medium text-foreground">{therapist.full_name}</h4>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        therapist.status === 'approved' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                      }`}>
                        {therapist.status}
                      </span>
                      {getSubscriptionBadge(therapist)}
                    </div>
                    <p className="text-sm text-muted-foreground">Mobile: {therapist.mobile}</p>
                    <p className="text-sm text-muted-foreground">Email: {therapist.email || 'N/A'}</p>
                    <p className="text-sm text-muted-foreground">Credentials: {therapist.credentials}</p>
                    {therapist.subscription_end_date && (
                      <p className="text-sm mt-2">
                        <Calendar size={14} className="inline mr-1" />
                        Expires: {formatDate(therapist.subscription_end_date)}
                        {remainingDays !== null && (
                          <span className={`ml-2 font-medium ${remainingDays <= 7 ? 'text-error' : remainingDays <= 30 ? 'text-warning' : 'text-success'}`}>
                            ({remainingDays > 0 ? `${remainingDays} days left` : 'Expired'})
                          </span>
                        )}
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex flex-col gap-2">
                  <div className="flex gap-2">
                    <Button onClick={() => handleViewDetail(therapist)} variant="outline" size="sm">
                      <Eye size={16} className="mr-1" /> View
                    </Button>
                    <Button onClick={() => handleEditClick(therapist)} variant="outline" size="sm">
                      <Edit size={16} className="mr-1" /> Edit
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => handleManageSubscription(therapist)} variant="outline" size="sm" data-testid={`subscription-${therapist.id}`}>
                      <CreditCard size={16} className="mr-1" /> Subscription
                    </Button>
                    <Button onClick={() => handleViewClients(therapist)} variant="outline" size="sm">
                      <Users size={16} className="mr-1" /> Clients
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => handleResetPassword(therapist)} variant="outline" size="sm">
                      <Key size={16} className="mr-1" /> Reset PW
                    </Button>
                    {therapist.status === 'approved' ? (
                      <Button onClick={() => handleSuspend(therapist.id)} variant="destructive" size="sm">
                        <Ban size={16} className="mr-1" /> Suspend
                      </Button>
                    ) : (
                      <Button onClick={() => handleActivate(therapist.id)} className="bg-success hover:bg-success/80" size="sm">
                        <CheckCircle size={16} className="mr-1" /> Activate
                      </Button>
                    )}
                    <Button 
                      onClick={() => handleDeleteTherapist(therapist)} 
                      variant="ghost" 
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      data-testid={`delete-therapist-${therapist.id}`}
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}

        {filteredTherapists.length === 0 && (
          <div className="text-center py-12">
            {searchQuery ? (
              <div>
                <p className="text-muted-foreground mb-2">No therapists found matching "{searchQuery}"</p>
                <Button variant="outline" onClick={() => setSearchQuery('')} data-testid="clear-search-empty">
                  Clear Search
                </Button>
              </div>
            ) : (
              <p className="text-muted-foreground">No therapists found</p>
            )}
          </div>
        )}
      </div>

      {/* Subscription Management Dialog */}
      {showSubscriptionDialog && selectedTherapist && (
        <Dialog open={showSubscriptionDialog} onOpenChange={setShowSubscriptionDialog}>
          <DialogContent className="max-w-lg" data-testid="subscription-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Manage Subscription</DialogTitle>
            </DialogHeader>
            <div className="space-y-6">
              <div className="p-4 bg-surface rounded-lg">
                <p className="font-medium">{selectedTherapist.full_name}</p>
                <p className="text-sm text-muted-foreground">
                  Current: {selectedTherapist.subscription_status || 'None'} 
                  {selectedTherapist.subscription_plan && ` (${selectedTherapist.subscription_plan})`}
                </p>
                {selectedTherapist.subscription_end_date && (
                  <p className="text-sm text-muted-foreground">
                    Expires: {formatDate(selectedTherapist.subscription_end_date)}
                  </p>
                )}
              </div>

              {/* Assign Trial */}
              <div className="p-4 border border-info/30 rounded-lg bg-info/5">
                <h4 className="font-medium mb-2">Assign Free Trial (30 days)</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  Assign a new 30-day trial subscription. Use this for new therapists or to reset their trial.
                </p>
                <Button onClick={handleAssignTrial} className="w-full" data-testid="assign-trial-button">
                  Assign 30-Day Trial
                </Button>
              </div>

              {/* Assign Plan */}
              {subscriptionPlans.length > 0 && (
                <div className="p-4 border border-primary/30 rounded-lg bg-primary/5">
                  <h4 className="font-medium mb-2">Assign Subscription Plan</h4>
                  <div className="space-y-3">
                    <Select value={selectedPlanId} onValueChange={setSelectedPlanId}>
                      <SelectTrigger data-testid="select-plan-trigger">
                        <SelectValue placeholder="Select a plan" />
                      </SelectTrigger>
                      <SelectContent>
                        {subscriptionPlans.map((plan) => (
                          <SelectItem key={plan.id} value={plan.id}>
                            {plan.name} - ${plan.price} ({plan.duration_days} days)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button onClick={handleAssignPlan} className="w-full" variant="outline" data-testid="assign-plan-button">
                      Assign Selected Plan
                    </Button>
                  </div>
                </div>
              )}

              {/* Extend Subscription */}
              <div className="p-4 border border-success/30 rounded-lg bg-success/5">
                <h4 className="font-medium mb-2">Extend Current Subscription</h4>
                <p className="text-sm text-muted-foreground mb-3">
                  Add extra days to the current subscription end date.
                </p>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    value={extendDays}
                    onChange={(e) => setExtendDays(parseInt(e.target.value) || 0)}
                    className="w-24"
                    min={1}
                    data-testid="extend-days-input"
                  />
                  <span className="flex items-center text-sm text-muted-foreground">days</span>
                  <Button onClick={handleExtendSubscription} variant="outline" className="flex-1" data-testid="extend-subscription-button">
                    Extend Subscription
                  </Button>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Create Therapist Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl" data-testid="create-therapist-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Add New Therapist</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTherapist} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
            <p className="text-sm text-info bg-info/10 p-3 rounded-lg">
              New therapists automatically receive a 30-day trial subscription.
            </p>
            
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Full Name *</Label>
                <Input value={newTherapist.full_name} onChange={(e) => setNewTherapist({ ...newTherapist, full_name: e.target.value })} required className="mt-1" />
              </div>
              <div>
                <Label>Mobile (10 digits) *</Label>
                <Input value={newTherapist.mobile} onChange={(e) => setNewTherapist({ ...newTherapist, mobile: e.target.value })} required maxLength={10} className="mt-1" />
              </div>
            </div>
            <div>
              <Label>Email *</Label>
              <Input type="email" value={newTherapist.email} onChange={(e) => setNewTherapist({ ...newTherapist, email: e.target.value })} required className="mt-1" />
            </div>
            <div>
              <Label>Password *</Label>
              <div className="flex gap-2 mt-1">
                <Input value={newTherapist.password} onChange={(e) => setNewTherapist({ ...newTherapist, password: e.target.value })} required />
                <Button type="button" variant="outline" onClick={() => setNewTherapist({ ...newTherapist, password: generatePassword() })}>Generate</Button>
              </div>
            </div>
            <div>
              <Label>Qualifications *</Label>
              <Input value={newTherapist.qualifications} onChange={(e) => setNewTherapist({ ...newTherapist, qualifications: e.target.value })} required className="mt-1" placeholder="M.Phil Clinical Psychology, RCI Licensed" />
              <p className="text-xs text-muted-foreground mt-1">Degrees, certifications, licenses</p>
            </div>
            <div>
              <Label>Years of Experience</Label>
              <Input type="number" value={newTherapist.years_of_experience} onChange={(e) => setNewTherapist({ ...newTherapist, years_of_experience: e.target.value })} className="mt-1" />
            </div>

            {/* Specializations Multi-Select */}
            <div className="border-t pt-4">
              <Label>Specializations * <span className="text-muted-foreground font-normal">(Select 1-5)</span></Label>
              <div className="flex flex-wrap gap-2 mt-2 mb-3 min-h-[32px]">
                {(newTherapist.specializations || []).map((spec, idx) => (
                  <Badge key={idx} variant="secondary" className="px-3 py-1 bg-primary/10 text-primary">
                    {spec}
                    <button type="button" onClick={() => removeSpecialization(spec)} className="ml-2 hover:text-destructive">
                      <X size={12} />
                    </button>
                  </Badge>
                ))}
                {(!newTherapist.specializations || newTherapist.specializations.length === 0) && (
                  <span className="text-sm text-muted-foreground">No specializations selected</span>
                )}
              </div>
              <div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="w-full justify-between"
                  onClick={() => setShowSpecDropdown(!showSpecDropdown)}
                >
                  <span>Select ({(newTherapist.specializations || []).length}/5)</span>
                  <Plus size={14} />
                </Button>
                {showSpecDropdown && (
                  <>
                    <div 
                      className="fixed inset-0 z-[9998]" 
                      onClick={() => setShowSpecDropdown(false)}
                    />
                    <div 
                      className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[9999] w-[380px] bg-white border-2 border-primary/20 rounded-xl shadow-2xl"
                    >
                      <div className="p-3 border-b bg-primary/5 rounded-t-xl flex justify-between items-center">
                        <span className="font-medium text-primary text-sm">Select Specializations (max 5)</span>
                        <button type="button" onClick={() => setShowSpecDropdown(false)} className="text-gray-500 hover:text-gray-700">
                          <X size={16} />
                        </button>
                      </div>
                      <div className="overflow-y-auto" style={{ maxHeight: '300px' }}>
                        {SPECIALIZATION_OPTIONS.map((spec, idx) => (
                          <button
                            key={idx}
                            type="button"
                            className={`w-full text-left px-4 py-2.5 text-sm hover:bg-primary/5 flex items-center justify-between border-b border-gray-100 last:border-0 ${
                              (newTherapist.specializations || []).includes(spec) ? 'bg-primary/10 text-primary font-medium' : ''
                            }`}
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSpecialization(spec);
                            }}
                          >
                            <span>{spec}</span>
                            {(newTherapist.specializations || []).includes(spec) && <CheckCircle size={16} className="flex-shrink-0" />}
                          </button>
                        ))}
                      </div>
                      <div className="p-2 border-t bg-gray-50 rounded-b-xl">
                        <Button 
                          type="button" 
                          size="sm" 
                          onClick={() => setShowSpecDropdown(false)}
                          className="w-full"
                        >
                          Done ({(newTherapist.specializations || []).length} selected)
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Clinic Info */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <Building2 size={16} className="text-primary" />
                <span className="font-medium text-sm">Clinic Information</span>
              </div>
              <div>
                <Label>Clinic Name</Label>
                <Input value={newTherapist.clinic_name} onChange={(e) => setNewTherapist({ ...newTherapist, clinic_name: e.target.value })} className="mt-1" placeholder="Mind Wellness Clinic" />
              </div>
            </div>

            {/* Consultation Fees */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CreditCard size={16} className="text-primary" />
                  <span className="font-medium text-sm">Consultation Fees</span>
                </div>
                {newTherapist.fee_slots.length < 5 && (
                  <Button type="button" variant="outline" size="sm" onClick={addFeeSlot}>
                    <Plus size={14} className="mr-1" /> Add
                  </Button>
                )}
              </div>
              <div className="space-y-2">
                {newTherapist.fee_slots.map((slot, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 bg-surface rounded-lg">
                    <div className="flex-1 grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs">Amount (₹)</Label>
                        <Input
                          type="number"
                          min="0"
                          value={slot.amount}
                          onChange={(e) => updateFeeSlot(index, 'amount', e.target.value)}
                          placeholder="1500"
                          className="mt-1"
                        />
                      </div>
                      <div>
                        <Label className="text-xs">Duration</Label>
                        <select
                          value={slot.duration_minutes}
                          onChange={(e) => updateFeeSlot(index, 'duration_minutes', e.target.value)}
                          className="w-full h-9 mt-1 px-3 rounded-md border border-input bg-background text-sm"
                        >
                          <option value="15">15 min</option>
                          <option value="20">20 min</option>
                          <option value="30">30 min</option>
                          <option value="40">40 min</option>
                          <option value="45">45 min</option>
                          <option value="50">50 min</option>
                          <option value="60">60 min</option>
                          <option value="90">90 min</option>
                        </select>
                      </div>
                    </div>
                    <div className="text-right min-w-[80px]">
                      <p className="font-medium text-primary">{slot.amount ? `₹${slot.amount}` : '—'}</p>
                      <p className="text-xs text-muted-foreground">{slot.duration_minutes} min</p>
                    </div>
                    {newTherapist.fee_slots.length > 1 && (
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeFeeSlot(index)} className="text-destructive">
                        <Trash2 size={14} />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Address Section */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center gap-2 mb-3">
                <MapPin size={16} className="text-primary" />
                <span className="font-medium text-sm">Clinic Address</span>
                <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">Indian Format</span>
              </div>
              <div className="space-y-3">
                <div>
                  <Label>Address Line 1</Label>
                  <Input value={newTherapist.address_line_1} onChange={(e) => setNewTherapist({ ...newTherapist, address_line_1: e.target.value })} className="mt-1" placeholder="Building/House No., Street" />
                </div>
                <div>
                  <Label>Address Line 2</Label>
                  <Input value={newTherapist.address_line_2} onChange={(e) => setNewTherapist({ ...newTherapist, address_line_2: e.target.value })} className="mt-1" placeholder="Locality, Area, Landmark" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>PIN Code</Label>
                    <div className="relative mt-1">
                      <Input 
                        value={newTherapist.pincode} 
                        onChange={(e) => handlePincodeChange(e.target.value, false)} 
                        maxLength={6} 
                        placeholder="110001"
                        className="pr-8"
                      />
                      {pincodeLoading && (
                        <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-primary" />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">6-digit PIN auto-fills city/state</p>
                  </div>
                  <div>
                    <Label>City</Label>
                    <Input value={newTherapist.city} onChange={(e) => setNewTherapist({ ...newTherapist, city: e.target.value })} className="mt-1" placeholder="Auto-filled" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>District</Label>
                    <Input value={newTherapist.district} onChange={(e) => setNewTherapist({ ...newTherapist, district: e.target.value })} className="mt-1" placeholder="Auto-filled" />
                  </div>
                  <div>
                    <Label>State</Label>
                    <Input value={newTherapist.state} onChange={(e) => setNewTherapist({ ...newTherapist, state: e.target.value })} className="mt-1" placeholder="Auto-filled" />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1">Create Therapist</Button>
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Therapist Dialog */}
      {showEditDialog && selectedTherapist && (
        <Dialog open={showEditDialog} onOpenChange={(open) => { setShowEditDialog(open); if (!open) setShowEditSpecDropdown(false); }}>
          <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="edit-therapist-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Edit Therapist</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleUpdateTherapist} className="space-y-4">
              {/* Profile Photo Section */}
              <div className="flex items-center gap-4 p-4 bg-surface rounded-lg">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                  {editData.profile_photo ? (
                    <img src={editData.profile_photo} alt={editData.full_name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-xl font-bold text-primary">{editData.full_name?.charAt(0)}</span>
                  )}
                </div>
                <div className="flex-1">
                  <Label>Profile Photo URL</Label>
                  <Input value={editData.profile_photo} onChange={(e) => setEditData({ ...editData, profile_photo: e.target.value })} placeholder="https://example.com/photo.jpg" className="mt-1" />
                </div>
              </div>
              
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Full Name *</Label>
                  <Input value={editData.full_name} onChange={(e) => setEditData({ ...editData, full_name: e.target.value })} required className="mt-1" />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input type="email" value={editData.email} onChange={(e) => setEditData({ ...editData, email: e.target.value })} className="mt-1" />
                </div>
              </div>
              
              <div>
                <Label>Qualifications</Label>
                <Input value={editData.qualifications} onChange={(e) => setEditData({ ...editData, qualifications: e.target.value })} className="mt-1" placeholder="M.Phil Clinical Psychology, RCI Licensed" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Years of Experience</Label>
                  <Input type="number" value={editData.years_of_experience} onChange={(e) => setEditData({ ...editData, years_of_experience: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label>Clinic Name</Label>
                  <Input value={editData.clinic_name} onChange={(e) => setEditData({ ...editData, clinic_name: e.target.value })} className="mt-1" />
                </div>
              </div>
              
              {/* Specializations Multi-Select */}
              <div className="border-t pt-4">
                <Label>Specializations <span className="text-muted-foreground font-normal">(Select 1-5)</span></Label>
                <div className="flex flex-wrap gap-2 mt-2 mb-3 min-h-[32px]">
                  {(editData.specializations || []).map((spec, idx) => (
                    <Badge key={idx} variant="secondary" className="px-3 py-1 bg-primary/10 text-primary">
                      {spec}
                      <button type="button" onClick={() => removeEditSpecialization(spec)} className="ml-2 hover:text-destructive">
                        <X size={12} />
                      </button>
                    </Badge>
                  ))}
                  {(!editData.specializations || editData.specializations.length === 0) && (
                    <span className="text-sm text-muted-foreground">No specializations selected</span>
                  )}
                </div>
                <div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="w-full justify-between"
                    onClick={() => setShowEditSpecDropdown(!showEditSpecDropdown)}
                  >
                    <span>Select ({(editData.specializations || []).length}/5)</span>
                    <Plus size={14} />
                  </Button>
                  {showEditSpecDropdown && (
                    <>
                      <div 
                        className="fixed inset-0 z-[9998]" 
                        onClick={() => setShowEditSpecDropdown(false)}
                      />
                      <div 
                        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[9999] w-[380px] bg-white border-2 border-primary/20 rounded-xl shadow-2xl"
                      >
                        <div className="p-3 border-b bg-primary/5 rounded-t-xl flex justify-between items-center">
                          <span className="font-medium text-primary text-sm">Select Specializations (max 5)</span>
                          <button type="button" onClick={() => setShowEditSpecDropdown(false)} className="text-gray-500 hover:text-gray-700">
                            <X size={16} />
                          </button>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: '300px' }}>
                          {SPECIALIZATION_OPTIONS.map((spec, idx) => (
                            <button
                              key={idx}
                              type="button"
                              className={`w-full text-left px-4 py-2.5 text-sm hover:bg-primary/5 flex items-center justify-between border-b border-gray-100 last:border-0 ${
                                (editData.specializations || []).includes(spec) ? 'bg-primary/10 text-primary font-medium' : ''
                              }`}
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleEditSpecialization(spec);
                              }}
                            >
                              <span>{spec}</span>
                              {(editData.specializations || []).includes(spec) && <CheckCircle size={16} className="flex-shrink-0" />}
                            </button>
                          ))}
                        </div>
                        <div className="p-2 border-t bg-gray-50 rounded-b-xl">
                          <Button 
                            type="button" 
                            size="sm" 
                            onClick={() => setShowEditSpecDropdown(false)}
                            className="w-full"
                          >
                            Done ({(editData.specializations || []).length} selected)
                          </Button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
              
              {/* Address Section */}
              <div className="border-t pt-4">
                <div className="flex items-center gap-2 mb-3">
                  <MapPin size={16} className="text-primary" />
                  <span className="font-medium text-sm">Clinic Address</span>
                </div>
                <div className="space-y-3">
                  <div>
                    <Label>Address Line 1</Label>
                    <Input value={editData.address_line_1} onChange={(e) => setEditData({ ...editData, address_line_1: e.target.value })} className="mt-1" placeholder="Building/House No., Street" />
                  </div>
                  <div>
                    <Label>Address Line 2</Label>
                    <Input value={editData.address_line_2} onChange={(e) => setEditData({ ...editData, address_line_2: e.target.value })} className="mt-1" placeholder="Locality, Area, Landmark" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>PIN Code</Label>
                      <div className="relative mt-1">
                        <Input 
                          value={editData.pincode} 
                          onChange={(e) => handlePincodeChange(e.target.value, true)} 
                          maxLength={6} 
                          placeholder="110001"
                          className="pr-8"
                        />
                        {pincodeLoading && (
                          <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-primary" />
                        )}
                      </div>
                    </div>
                    <div>
                      <Label>City</Label>
                      <Input value={editData.city} onChange={(e) => setEditData({ ...editData, city: e.target.value })} className="mt-1" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>District</Label>
                      <Input value={editData.district} onChange={(e) => setEditData({ ...editData, district: e.target.value })} className="mt-1" />
                    </div>
                    <div>
                      <Label>State</Label>
                      <Input value={editData.state} onChange={(e) => setEditData({ ...editData, state: e.target.value })} className="mt-1" />
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3 pt-2">
                <Button type="submit" className="flex-1">Update Therapist</Button>
                <Button type="button" variant="outline" onClick={() => { setShowEditDialog(false); setShowEditSpecDropdown(false); }}>Cancel</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {/* Therapist Detail Dialog */}
      {showDetailDialog && therapistDetail && (
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="therapist-detail-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Therapist Profile</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {/* Header with photo and name */}
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                  {therapistDetail.profile_photo ? (
                    <img src={therapistDetail.profile_photo} alt={therapistDetail.full_name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-3xl font-bold text-primary">{therapistDetail.full_name?.charAt(0)}</span>
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-semibold">{therapistDetail.full_name}</h3>
                  <p className="text-muted-foreground">{therapistDetail.qualifications || therapistDetail.credentials || 'N/A'}</p>
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                    therapistDetail.status === 'approved' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                  }`}>
                    {therapistDetail.status}
                  </span>
                </div>
              </div>
              
              {/* Basic Info */}
              <div className="p-4 bg-surface rounded-lg">
                <h4 className="font-semibold mb-3 text-sm text-primary">Basic Information</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><strong>Mobile:</strong> {therapistDetail.mobile}</div>
                  <div><strong>Email:</strong> {therapistDetail.email || 'N/A'}</div>
                  <div><strong>Experience:</strong> {therapistDetail.years_of_experience ? `${therapistDetail.years_of_experience} years` : 'N/A'}</div>
                  <div><strong>Clients:</strong> {therapistDetail.client_count || 0}</div>
                </div>
              </div>
              
              {/* Specializations */}
              {therapistDetail.specializations && therapistDetail.specializations.length > 0 && (
                <div className="p-4 bg-primary/5 rounded-lg">
                  <h4 className="font-semibold mb-2 text-sm text-primary">Specializations</h4>
                  <div className="flex flex-wrap gap-2">
                    {therapistDetail.specializations.map((spec, idx) => (
                      <Badge key={idx} variant="secondary" className="bg-primary/10 text-primary">
                        {spec}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Clinic Info */}
              {(therapistDetail.clinic_name || therapistDetail.address_line_1) && (
                <div className="p-4 bg-surface rounded-lg">
                  <h4 className="font-semibold mb-3 text-sm text-primary flex items-center gap-2">
                    <Building2 size={14} /> Clinic Information
                  </h4>
                  {therapistDetail.clinic_name && (
                    <p className="font-medium mb-2">{therapistDetail.clinic_name}</p>
                  )}
                  {therapistDetail.address_line_1 && (
                    <div className="text-sm text-muted-foreground space-y-1">
                      <p>{therapistDetail.address_line_1}</p>
                      {therapistDetail.address_line_2 && <p>{therapistDetail.address_line_2}</p>}
                      <p>
                        {[therapistDetail.city, therapistDetail.district, therapistDetail.state].filter(Boolean).join(', ')}
                        {therapistDetail.pincode && ` - ${therapistDetail.pincode}`}
                      </p>
                    </div>
                  )}
                  {therapistDetail.google_maps_link && (
                    <a 
                      href={therapistDetail.google_maps_link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-sm text-primary hover:underline mt-2 inline-block"
                    >
                      View on Google Maps →
                    </a>
                  )}
                </div>
              )}
              
              {/* Fee Slots */}
              {therapistDetail.fee_slots && therapistDetail.fee_slots.length > 0 && (
                <div className="p-4 bg-surface rounded-lg">
                  <h4 className="font-semibold mb-3 text-sm text-primary flex items-center gap-2">
                    <CreditCard size={14} /> Consultation Fees
                  </h4>
                  <div className="flex flex-wrap gap-3">
                    {therapistDetail.fee_slots.map((slot, idx) => (
                      <div key={idx} className="px-3 py-2 bg-white border rounded-lg text-sm">
                        <span className="font-medium text-primary">₹{slot.amount}</span>
                        <span className="text-muted-foreground ml-1">/ {slot.duration_minutes} min</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Subscription Details */}
              <div className="p-4 bg-info/10 rounded-lg">
                <h4 className="font-semibold mb-2 text-sm text-primary">Subscription Details</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><strong>Plan:</strong> {therapistDetail.subscription_plan || 'None'}</div>
                  <div><strong>Status:</strong> {therapistDetail.subscription_status || 'None'}</div>
                  <div className="col-span-2">
                    <strong>Valid Until:</strong> {therapistDetail.subscription_end_date ? formatDate(therapistDetail.subscription_end_date) : 'N/A'}
                    {therapistDetail.subscription_end_date && (
                      <span className={`ml-2 font-medium ${getRemainingDays(therapistDetail.subscription_end_date) <= 7 ? 'text-error' : 'text-success'}`}>
                        ({getRemainingDays(therapistDetail.subscription_end_date)} days remaining)
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button onClick={() => { setShowDetailDialog(false); handleViewClients(therapistDetail); }} className="flex-1">
                  <Users size={16} className="mr-2" /> View Clients
                </Button>
                <Button 
                  onClick={() => { setShowDetailDialog(false); handleEditClick(therapistDetail); }} 
                  variant="outline"
                  className="flex-1"
                >
                  <Edit size={16} className="mr-2" /> Edit Profile
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Therapist Clients Dialog */}
      {showClientsDialog && selectedTherapist && (
        <Dialog open={showClientsDialog} onOpenChange={setShowClientsDialog}>
          <DialogContent className="max-w-2xl" data-testid="therapist-clients-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">
                Clients of {selectedTherapist.full_name}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {therapistClients.length === 0 ? (
                <p className="text-center text-muted-foreground py-4">No clients assigned</p>
              ) : (
                therapistClients.map((client) => (
                  <Card key={client.id} className="p-4 bg-surface">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="font-medium">{client.full_name}</h4>
                        <p className="text-sm text-muted-foreground">
                          {client.client_id} | {client.mobile} | {client.email || 'No email'}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Reset Password Dialog */}
      {showPasswordDialog && selectedTherapist && (
        <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
          <DialogContent data-testid="password-reset-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Reset Password</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-foreground">
                Resetting password for: <strong>{selectedTherapist.full_name}</strong>
              </p>
              <div>
                <Label>New Password</Label>
                <div className="flex gap-2 mt-1">
                  <Input value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                  <Button type="button" variant="outline" onClick={() => setNewPassword(generatePassword())}>Regenerate</Button>
                </div>
              </div>
              <div className="flex gap-3">
                <Button onClick={confirmPasswordReset} className="flex-1">Reset Password</Button>
                <Button variant="outline" onClick={() => setShowPasswordDialog(false)}>Cancel</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default TherapistManagement;
