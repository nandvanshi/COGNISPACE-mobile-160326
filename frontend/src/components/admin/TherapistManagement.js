import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Ban, CheckCircle, Key, Plus, Edit, Users, Eye, Camera, Calendar } from 'lucide-react';

const TherapistManagement = ({ onViewClients }) => {
  const [therapists, setTherapists] = useState([]);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showClientsDialog, setShowClientsDialog] = useState(false);
  const [selectedTherapist, setSelectedTherapist] = useState(null);
  const [therapistDetail, setTherapistDetail] = useState(null);
  const [therapistClients, setTherapistClients] = useState([]);
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [newTherapist, setNewTherapist] = useState({
    mobile: '',
    email: '',
    full_name: '',
    password: '',
    credentials: '',
    specialization: '',
    years_of_experience: ''
  });
  const [editData, setEditData] = useState({
    full_name: '',
    email: '',
    credentials: '',
    specialization: '',
    years_of_experience: ''
  });

  useEffect(() => {
    fetchTherapists();
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
      await axios.post(
        `${API}/admin/therapists/${selectedTherapist.id}/reset-password?new_password=${newPassword}`
      );
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
      toast.success('Therapist created successfully');
      setShowCreateDialog(false);
      setNewTherapist({
        mobile: '',
        email: '',
        full_name: '',
        password: '',
        credentials: '',
        specialization: '',
        years_of_experience: ''
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
      years_of_experience: therapist.years_of_experience || ''
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

  if (loading) {
    return <div className="text-center py-12">Loading therapists...</div>;
  }

  return (
    <div data-testid="therapist-management">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Therapist Management</h2>
          <p className="text-muted-foreground">Manage therapist accounts and subscriptions</p>
        </div>
        <Button
          onClick={() => setShowCreateDialog(true)}
          className="bg-primary hover:bg-primary-700 rounded-full"
          data-testid="add-therapist-button"
        >
          <Plus size={20} className="mr-2" />
          Add Therapist
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {therapists.map((therapist) => {
          const remainingDays = getRemainingDays(therapist.subscription_end_date);
          return (
            <Card
              key={therapist.id}
              className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
              data-testid={`therapist-${therapist.id}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex gap-4">
                  {/* Profile Photo */}
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                    {therapist.profile_photo ? (
                      <img src={therapist.profile_photo} alt={therapist.full_name} className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-2xl font-bold text-primary">{therapist.full_name?.charAt(0)}</span>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-lg font-medium text-foreground">{therapist.full_name}</h4>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          therapist.status === 'approved'
                            ? 'bg-success/10 text-success'
                            : 'bg-error/10 text-error'
                        }`}
                      >
                        {therapist.status}
                      </span>
                      {therapist.subscription_status && (
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            therapist.subscription_status === 'active' || therapist.subscription_status === 'trial'
                              ? 'bg-info/10 text-info'
                              : 'bg-warning/10 text-warning'
                          }`}
                        >
                          {therapist.subscription_status}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">Mobile: {therapist.mobile}</p>
                    <p className="text-sm text-muted-foreground">Email: {therapist.email || 'N/A'}</p>
                    <p className="text-sm text-muted-foreground">Credentials: {therapist.credentials}</p>
                    {therapist.specialization && (
                      <p className="text-sm text-muted-foreground">Specialization: {therapist.specialization}</p>
                    )}
                    {therapist.subscription_end_date && (
                      <p className="text-sm mt-2">
                        <Calendar size={14} className="inline mr-1" />
                        Subscription expires: {formatDate(therapist.subscription_end_date)}
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
                    <Button
                      onClick={() => handleViewDetail(therapist)}
                      variant="outline"
                      size="sm"
                      data-testid={`view-${therapist.id}`}
                    >
                      <Eye size={16} className="mr-1" />
                      View
                    </Button>
                    <Button
                      onClick={() => handleEditClick(therapist)}
                      variant="outline"
                      size="sm"
                      data-testid={`edit-${therapist.id}`}
                    >
                      <Edit size={16} className="mr-1" />
                      Edit
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleViewClients(therapist)}
                      variant="outline"
                      size="sm"
                      data-testid={`clients-${therapist.id}`}
                    >
                      <Users size={16} className="mr-1" />
                      Clients
                    </Button>
                    <Button
                      onClick={() => handleResetPassword(therapist)}
                      variant="outline"
                      size="sm"
                      data-testid={`reset-password-${therapist.id}`}
                    >
                      <Key size={16} className="mr-1" />
                      Reset PW
                    </Button>
                  </div>
                  {therapist.status === 'approved' ? (
                    <Button
                      onClick={() => handleSuspend(therapist.id)}
                      variant="destructive"
                      size="sm"
                      data-testid={`suspend-${therapist.id}`}
                    >
                      <Ban size={16} className="mr-2" />
                      Suspend
                    </Button>
                  ) : (
                    <Button
                      onClick={() => handleActivate(therapist.id)}
                      className="bg-success hover:bg-success/80"
                      size="sm"
                      data-testid={`activate-${therapist.id}`}
                    >
                      <CheckCircle size={16} className="mr-2" />
                      Activate
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          );
        })}

        {therapists.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No therapists found</p>
          </div>
        )}
      </div>

      {/* Create Therapist Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-lg" data-testid="create-therapist-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Add New Therapist</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTherapist} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Full Name *</Label>
                <Input
                  value={newTherapist.full_name}
                  onChange={(e) => setNewTherapist({ ...newTherapist, full_name: e.target.value })}
                  required
                  className="mt-1"
                  data-testid="new-therapist-name"
                />
              </div>
              <div>
                <Label>Mobile (10 digits) *</Label>
                <Input
                  value={newTherapist.mobile}
                  onChange={(e) => setNewTherapist({ ...newTherapist, mobile: e.target.value })}
                  required
                  maxLength={10}
                  className="mt-1"
                  data-testid="new-therapist-mobile"
                />
              </div>
            </div>
            <div>
              <Label>Email *</Label>
              <Input
                type="email"
                value={newTherapist.email}
                onChange={(e) => setNewTherapist({ ...newTherapist, email: e.target.value })}
                required
                className="mt-1"
                data-testid="new-therapist-email"
              />
            </div>
            <div>
              <Label>Password *</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  value={newTherapist.password}
                  onChange={(e) => setNewTherapist({ ...newTherapist, password: e.target.value })}
                  required
                  data-testid="new-therapist-password"
                />
                <Button type="button" variant="outline" onClick={() => setNewTherapist({ ...newTherapist, password: generatePassword() })}>
                  Generate
                </Button>
              </div>
            </div>
            <div>
              <Label>Credentials/License *</Label>
              <Input
                value={newTherapist.credentials}
                onChange={(e) => setNewTherapist({ ...newTherapist, credentials: e.target.value })}
                required
                className="mt-1"
                placeholder="e.g., Licensed Clinical Psychologist, #12345"
                data-testid="new-therapist-credentials"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Specialization</Label>
                <Input
                  value={newTherapist.specialization}
                  onChange={(e) => setNewTherapist({ ...newTherapist, specialization: e.target.value })}
                  className="mt-1"
                  data-testid="new-therapist-specialization"
                />
              </div>
              <div>
                <Label>Years of Experience</Label>
                <Input
                  type="number"
                  value={newTherapist.years_of_experience}
                  onChange={(e) => setNewTherapist({ ...newTherapist, years_of_experience: e.target.value })}
                  className="mt-1"
                  data-testid="new-therapist-experience"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="submit-create-therapist">Create Therapist</Button>
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
              <div>
                <Label>Full Name</Label>
                <Input
                  value={editData.full_name}
                  onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                  className="mt-1"
                  data-testid="edit-therapist-name"
                />
              </div>
              <div>
                <Label>Email</Label>
                <Input
                  type="email"
                  value={editData.email}
                  onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                  className="mt-1"
                  data-testid="edit-therapist-email"
                />
              </div>
              <div>
                <Label>Credentials</Label>
                <Input
                  value={editData.credentials}
                  onChange={(e) => setEditData({ ...editData, credentials: e.target.value })}
                  className="mt-1"
                  data-testid="edit-therapist-credentials"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Specialization</Label>
                  <Input
                    value={editData.specialization}
                    onChange={(e) => setEditData({ ...editData, specialization: e.target.value })}
                    className="mt-1"
                    data-testid="edit-therapist-specialization"
                  />
                </div>
                <div>
                  <Label>Years of Experience</Label>
                  <Input
                    type="number"
                    value={editData.years_of_experience}
                    onChange={(e) => setEditData({ ...editData, years_of_experience: e.target.value })}
                    className="mt-1"
                    data-testid="edit-therapist-experience"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <Button type="submit" className="flex-1" data-testid="submit-edit-therapist">Update Therapist</Button>
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
                  <div><strong>Plan:</strong> {therapistDetail.subscription_plan || 'N/A'}</div>
                  <div><strong>Status:</strong> {therapistDetail.subscription_status || 'N/A'}</div>
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
                        {client.age && <p className="text-sm text-muted-foreground">Age: {client.age}</p>}
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
                  <Input
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    data-testid="new-password-input"
                  />
                  <Button type="button" variant="outline" onClick={() => setNewPassword(generatePassword())} data-testid="regenerate-button">
                    Regenerate
                  </Button>
                </div>
              </div>
              <div className="flex gap-3">
                <Button onClick={confirmPasswordReset} className="flex-1" data-testid="confirm-reset-button">Reset Password</Button>
                <Button variant="outline" onClick={() => setShowPasswordDialog(false)} data-testid="cancel-reset-button">Cancel</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default TherapistManagement;
