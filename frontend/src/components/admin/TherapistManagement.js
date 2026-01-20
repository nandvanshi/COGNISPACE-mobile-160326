import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { toast } from 'sonner';
import { Ban, CheckCircle, Key, Plus, Edit, Users, Eye, Calendar, CreditCard, RefreshCw, Search, X } from 'lucide-react';

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
  const [newTherapist, setNewTherapist] = useState({
    mobile: '',
    email: '',
    full_name: '',
    password: '',
    credentials: '',
    specialization: '',
    years_of_experience: '',
    clinic_name: '',
    consultation_fee: '',
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
    credentials: '',
    specialization: '',
    years_of_experience: '',
    profile_photo: '',
    clinic_name: '',
    consultation_fee: '',
    address_line_1: '',
    address_line_2: '',
    pincode: '',
    city: '',
    state: '',
    district: ''
  });
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
    try {
      const payload = {
        ...newTherapist,
        years_of_experience: newTherapist.years_of_experience ? parseInt(newTherapist.years_of_experience) : null
      };
      await axios.post(`${API}/admin/therapists/create`, payload);
      toast.success('Therapist created with 30-day trial subscription');
      setShowCreateDialog(false);
      setNewTherapist({
        mobile: '', email: '', full_name: '', password: '',
        credentials: '', specialization: '', years_of_experience: ''
      });
      fetchTherapists();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create therapist');
    }
  };

  const handleEditClick = (therapist) => {
    setSelectedTherapist(therapist);
    setEditData({
      full_name: therapist.full_name || '',
      email: therapist.email || '',
      credentials: therapist.credentials || '',
      specialization: therapist.specialization || '',
      years_of_experience: therapist.years_of_experience || '',
      profile_photo: therapist.profile_photo || ''
    });
    setShowEditDialog(true);
  };

  const handleUpdateTherapist = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...editData,
        years_of_experience: editData.years_of_experience ? parseInt(editData.years_of_experience) : null
      };
      await axios.put(`${API}/admin/therapists/${selectedTherapist.id}`, payload);
      toast.success('Therapist updated successfully');
      setShowEditDialog(false);
      fetchTherapists();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update therapist');
    }
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
        <DialogContent className="max-w-lg" data-testid="create-therapist-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Add New Therapist</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTherapist} className="space-y-4">
            <p className="text-sm text-info bg-info/10 p-3 rounded-lg">
              New therapists automatically receive a 30-day trial subscription.
            </p>
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
              <Label>Credentials/License *</Label>
              <Input value={newTherapist.credentials} onChange={(e) => setNewTherapist({ ...newTherapist, credentials: e.target.value })} required className="mt-1" placeholder="e.g., Licensed Clinical Psychologist" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Specialization</Label>
                <Input value={newTherapist.specialization} onChange={(e) => setNewTherapist({ ...newTherapist, specialization: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label>Years of Experience</Label>
                <Input type="number" value={newTherapist.years_of_experience} onChange={(e) => setNewTherapist({ ...newTherapist, years_of_experience: e.target.value })} className="mt-1" />
              </div>
            </div>
            <div className="flex gap-3">
              <Button type="submit" className="flex-1">Create Therapist</Button>
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Therapist Dialog */}
      {showEditDialog && selectedTherapist && (
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className="max-w-lg" data-testid="edit-therapist-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Edit Therapist</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleUpdateTherapist} className="space-y-4">
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
              <div>
                <Label>Full Name</Label>
                <Input value={editData.full_name} onChange={(e) => setEditData({ ...editData, full_name: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label>Email</Label>
                <Input type="email" value={editData.email} onChange={(e) => setEditData({ ...editData, email: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label>Credentials</Label>
                <Input value={editData.credentials} onChange={(e) => setEditData({ ...editData, credentials: e.target.value })} className="mt-1" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Specialization</Label>
                  <Input value={editData.specialization} onChange={(e) => setEditData({ ...editData, specialization: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label>Years of Experience</Label>
                  <Input type="number" value={editData.years_of_experience} onChange={(e) => setEditData({ ...editData, years_of_experience: e.target.value })} className="mt-1" />
                </div>
              </div>
              <div className="flex gap-3">
                <Button type="submit" className="flex-1">Update Therapist</Button>
                <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {/* Therapist Detail Dialog */}
      {showDetailDialog && therapistDetail && (
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-lg" data-testid="therapist-detail-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Therapist Profile</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
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
                  <p className="text-muted-foreground">{therapistDetail.credentials}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>Mobile:</strong> {therapistDetail.mobile}</div>
                <div><strong>Email:</strong> {therapistDetail.email || 'N/A'}</div>
                <div><strong>Specialization:</strong> {therapistDetail.specialization || 'N/A'}</div>
                <div><strong>Experience:</strong> {therapistDetail.years_of_experience ? `${therapistDetail.years_of_experience} years` : 'N/A'}</div>
                <div><strong>Status:</strong> {therapistDetail.status}</div>
                <div><strong>Clients:</strong> {therapistDetail.client_count}</div>
              </div>
              
              <div className="p-4 bg-info/10 rounded-lg">
                <h4 className="font-semibold mb-2">Subscription Details</h4>
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
              
              <Button onClick={() => { setShowDetailDialog(false); handleViewClients(therapistDetail); }} className="w-full">
                <Users size={16} className="mr-2" /> View Assigned Clients
              </Button>
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
