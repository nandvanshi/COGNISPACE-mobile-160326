import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Textarea } from '../ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { toast } from 'sonner';
import { Key, Search, Eye, User, Phone, Mail, Edit, AlertCircle, UserX, Link2, Users } from 'lucide-react';

const ClientManagement = ({ onViewTherapist }) => {
  const [clients, setClients] = useState([]);
  const [filteredClients, setFilteredClients] = useState([]);
  const [orphanedClients, setOrphanedClients] = useState([]);
  const [therapists, setTherapists] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [clientDetail, setClientDetail] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [editForm, setEditForm] = useState({});
  const [selectedTherapistId, setSelectedTherapistId] = useState('');
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    fetchClients();
    fetchOrphanedClients();
    fetchTherapists();
  }, []);

  useEffect(() => {
    if (searchQuery) {
      setFilteredClients(
        clients.filter(
          (c) =>
            c.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (c.mobile && c.mobile.includes(searchQuery)) ||
            (c.email && c.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (c.client_id && c.client_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (c.therapist_name && c.therapist_name.toLowerCase().includes(searchQuery.toLowerCase()))
        )
      );
    } else {
      setFilteredClients(clients);
    }
  }, [searchQuery, clients]);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/admin/clients`);
      setClients(response.data);
      setFilteredClients(response.data);
    } catch (error) {
      toast.error('Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrphanedClients = async () => {
    try {
      const response = await axios.get(`${API}/admin/clients/orphaned/list`);
      setOrphanedClients(response.data.clients || []);
    } catch (error) {
      console.error('Failed to load orphaned clients');
    }
  };

  const fetchTherapists = async () => {
    try {
      const response = await axios.get(`${API}/admin/therapists`);
      setTherapists(response.data.filter(t => t.status === 'approved'));
    } catch (error) {
      console.error('Failed to load therapists');
    }
  };

  const handleLinkClient = (client) => {
    setSelectedClient(client);
    setSelectedTherapistId('');
    setShowLinkDialog(true);
  };

  const confirmLinkClient = async () => {
    if (!selectedTherapistId) {
      toast.error('Please select a therapist');
      return;
    }
    try {
      await axios.post(`${API}/admin/clients/${selectedClient.id}/link-therapist?therapist_id=${selectedTherapistId}`);
      toast.success('Client linked to therapist successfully');
      setShowLinkDialog(false);
      fetchClients();
      fetchOrphanedClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to link client');
    }
  };

  const handleViewDetail = async (client) => {
    try {
      const response = await axios.get(`${API}/admin/clients/${client.id}`);
      setClientDetail(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      toast.error('Failed to load client details');
    }
  };

  const handleEditClient = async (client) => {
    try {
      const response = await axios.get(`${API}/admin/clients/${client.id}`);
      setSelectedClient(client);
      setEditForm({
        full_name: response.data.full_name || '',
        mobile: response.data.mobile || '',
        email: response.data.email || '',
        age: response.data.age || '',
        guardian_name: response.data.guardian_name || '',
        address: response.data.address || '',
        referred_by: response.data.referred_by || '',
        intake_summary: response.data.intake_summary || '',
        emergency_contact_name: response.data.emergency_contact_name || '',
        emergency_contact_phone: response.data.emergency_contact_phone || '',
        profile_photo: response.data.profile_photo || '',
      });
      setShowEditDialog(true);
    } catch (error) {
      toast.error('Failed to load client details');
    }
  };

  const handleUpdateClient = async (e) => {
    e.preventDefault();
    
    if (editForm.mobile && !/^\d{10}$/.test(editForm.mobile)) {
      toast.error('Mobile number must be exactly 10 digits');
      return;
    }
    
    try {
      const updateData = {
        full_name: editForm.full_name || undefined,
        mobile: editForm.mobile || undefined,
        email: editForm.email || undefined,
        age: editForm.age ? parseInt(editForm.age) : undefined,
        guardian_name: editForm.guardian_name || undefined,
        address: editForm.address || undefined,
        referred_by: editForm.referred_by || undefined,
        intake_summary: editForm.intake_summary || undefined,
        emergency_contact_name: editForm.emergency_contact_name || undefined,
        emergency_contact_phone: editForm.emergency_contact_phone || undefined,
        profile_photo: editForm.profile_photo || undefined,
      };
      
      Object.keys(updateData).forEach(key => updateData[key] === undefined && delete updateData[key]);
      
      await axios.put(`${API}/admin/clients/${selectedClient.id}`, updateData);
      toast.success('Client updated successfully');
      setShowEditDialog(false);
      setSelectedClient(null);
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update client');
    }
  };

  const handleResetPassword = (client) => {
    setSelectedClient(client);
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
      await axios.post(`${API}/admin/clients/${selectedClient.id}/reset-password`, {
        new_password: newPassword
      });
      toast.success(`Password reset! New password: ${newPassword}`);
      setShowPasswordDialog(false);
      setSelectedClient(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  const handleNavigateToTherapist = (therapistId, therapistName) => {
    if (onViewTherapist && therapistId) {
      onViewTherapist(therapistId, therapistName);
      setShowDetailDialog(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading clients...</div>;
  }

  return (
    <div data-testid="client-management-admin">
      <div className="mb-8">
        <h2 className="text-4xl font-serif text-primary mb-2">Client Management</h2>
        <p className="text-muted-foreground">View and manage client accounts</p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList>
          <TabsTrigger value="all" className="gap-2">
            <Users size={16} /> All Clients ({clients.length})
          </TabsTrigger>
          <TabsTrigger value="orphaned" className="gap-2">
            <UserX size={16} /> Orphaned ({orphanedClients.length})
          </TabsTrigger>
        </TabsList>

        {/* All Clients Tab */}
        <TabsContent value="all">
          {/* Search */}
          <div className="mb-6">
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                size={20}
              />
              <Input
                placeholder="Search clients by name, mobile, email, ID, or therapist..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                data-testid="admin-client-search-input"
              />
            </div>
          </div>

          {/* Clients Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredClients.map((client) => (
              <Card
                key={client.id}
                className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
                data-testid={`admin-client-${client.id}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3">
                    {/* Avatar */}
                    <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden flex-shrink-0">
                      {client.profile_photo ? (
                        <img src={client.profile_photo} alt={client.full_name} className="w-full h-full object-cover" />
                      ) : (
                        <span className="text-lg font-bold text-primary">{client.full_name?.charAt(0)}</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-lg font-medium text-foreground">{client.full_name}</h4>
                        {client.client_id && (
                          <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">
                            {client.client_id}
                          </span>
                        )}
                      </div>
                      <div className="space-y-1 text-sm text-muted-foreground">
                        <p className="flex items-center gap-2">
                          <Phone size={14} /> {client.mobile || 'N/A'}
                        </p>
                        <p className="flex items-center gap-2">
                          <Mail size={14} /> {client.email || 'N/A'}
                    </p>
                    {client.age && (
                      <p className="flex items-center gap-2">
                        <User size={14} /> Age: {client.age}
                      </p>
                    )}
                    {client.therapist_name && (
                      <p className="mt-2">
                        <span className="px-2 py-1 bg-info/10 text-info text-xs rounded-full">
                          Therapist: {client.therapist_name}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <Button
                  onClick={() => handleViewDetail(client)}
                  variant="outline"
                  size="sm"
                  data-testid={`admin-view-client-${client.id}`}
                >
                  <Eye size={16} className="mr-1" />
                  View
                </Button>
                <Button
                  onClick={() => handleEditClient(client)}
                  variant="outline"
                  size="sm"
                  data-testid={`admin-edit-client-${client.id}`}
                >
                  <Edit size={16} className="mr-1" />
                  Edit
                </Button>
                <Button
                  onClick={() => handleResetPassword(client)}
                  variant="outline"
                  size="sm"
                  data-testid={`admin-reset-password-${client.id}`}
                >
                  <Key size={16} className="mr-1" />
                  Reset PW
                </Button>
              </div>
            </div>
          </Card>
        ))}

        {filteredClients.length === 0 && (
          <div className="col-span-2 text-center py-12">
            <p className="text-muted-foreground">No clients found</p>
          </div>
        )}
      </div>
        </TabsContent>

        {/* Orphaned Clients Tab */}
        <TabsContent value="orphaned">
          {orphanedClients.length === 0 ? (
            <div className="text-center py-12 bg-surface rounded-xl">
              <UserX size={48} className="mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">No Orphaned Clients</h3>
              <p className="text-muted-foreground">All clients are linked to active therapists.</p>
            </div>
          ) : (
            <>
              <div className="mb-4 p-4 bg-warning/10 border border-warning/20 rounded-xl">
                <p className="text-sm text-warning-foreground">
                  <strong>Note:</strong> These clients were unlinked when their therapist was deleted. 
                  You can link them to a new therapist.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {orphanedClients.map((client) => (
                  <Card
                    key={client.id}
                    className="p-6 bg-white/70 backdrop-blur-xl border border-amber-200 rounded-xl"
                    data-testid={`orphaned-client-${client.id}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-start gap-3">
                        <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
                          <UserX size={24} className="text-amber-600" />
                        </div>
                        <div>
                          <h4 className="text-lg font-medium">{client.full_name}</h4>
                          <p className="text-sm text-muted-foreground flex items-center gap-1">
                            <Phone size={14} /> {client.mobile || 'N/A'}
                          </p>
                          <p className="text-xs text-amber-600 mt-1">{client.reason}</p>
                        </div>
                      </div>
                      <Button
                        onClick={() => handleLinkClient(client)}
                        size="sm"
                        className="gap-1"
                        data-testid={`link-client-${client.id}`}
                      >
                        <Link2 size={16} /> Link
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>

      <div className="mt-8 p-6 bg-info/10 border border-info/20 rounded-xl">
        <p className="text-sm text-info">
          <strong>Privacy Note:</strong> Session notes, assessments, and messages are NOT accessible
          to admin for client privacy protection.
        </p>
      </div>

      {/* Client Detail Dialog */}
      {showDetailDialog && clientDetail && (
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-lg" data-testid="admin-client-detail-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Client Profile</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                  {clientDetail.profile_photo ? (
                    <img src={clientDetail.profile_photo} alt={clientDetail.full_name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-2xl font-bold text-primary">{clientDetail.full_name?.charAt(0)}</span>
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-semibold">{clientDetail.full_name}</h3>
                  {clientDetail.client_id && (
                    <p className="text-sm text-muted-foreground">ID: {clientDetail.client_id}</p>
                  )}
                </div>
              </div>

              {/* Contact Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Phone size={16} className="text-muted-foreground" />
                  <span>{clientDetail.mobile || 'N/A'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Mail size={16} className="text-muted-foreground" />
                  <span>{clientDetail.email || 'N/A'}</span>
                </div>
              </div>

              {/* Personal Info */}
              <div className="p-4 bg-surface rounded-lg space-y-2">
                <h4 className="font-semibold mb-2">Personal Information</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><strong>Age:</strong> {clientDetail.age || 'N/A'}</div>
                  <div><strong>Guardian:</strong> {clientDetail.guardian_name || 'N/A'}</div>
                  <div className="col-span-2"><strong>Address:</strong> {clientDetail.address || 'N/A'}</div>
                  <div><strong>Referred By:</strong> {clientDetail.referred_by || 'N/A'}</div>
                </div>
              </div>

              {/* Emergency Contact */}
              {(clientDetail.emergency_contact_name || clientDetail.emergency_contact_phone) && (
                <div className="p-4 bg-warning/10 rounded-lg">
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <AlertCircle size={16} /> Emergency Contact
                  </h4>
                  <div className="text-sm">
                    <p><strong>Name:</strong> {clientDetail.emergency_contact_name || 'N/A'}</p>
                    <p><strong>Phone:</strong> {clientDetail.emergency_contact_phone || 'N/A'}</p>
                  </div>
                </div>
              )}

              {/* Intake Summary */}
              {clientDetail.intake_summary && (
                <div className="p-4 bg-surface rounded-lg">
                  <h4 className="font-semibold mb-2">Intake Summary</h4>
                  <p className="text-sm text-muted-foreground">{clientDetail.intake_summary}</p>
                </div>
              )}

              {/* Assigned Therapist */}
              <div className="p-4 bg-info/10 rounded-lg">
                <h4 className="font-semibold mb-2">Assigned Therapist</h4>
                {clientDetail.therapist_name ? (
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{clientDetail.therapist_name}</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleNavigateToTherapist(clientDetail.therapist_id, clientDetail.therapist_name)}
                      data-testid="admin-view-therapist-button"
                    >
                      View Therapist Profile
                    </Button>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No therapist assigned</p>
                )}
              </div>

              {/* Created Date */}
              <p className="text-xs text-muted-foreground">
                Registered: {new Date(clientDetail.created_at).toLocaleDateString()}
              </p>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Edit Client Dialog */}
      {showEditDialog && selectedClient && (
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="admin-edit-client-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Edit Client Profile</DialogTitle>
            </DialogHeader>
            
            {/* Client ID (Immutable) */}
            <div className="p-3 bg-muted rounded-lg mb-4">
              <p className="text-sm text-muted-foreground">
                <strong>Client ID:</strong> {selectedClient.client_id || 'N/A'} 
                <span className="ml-2 text-xs">(immutable)</span>
              </p>
            </div>
            
            <form onSubmit={handleUpdateClient} className="space-y-4">
              {/* Profile Photo */}
              <div className="flex items-center gap-4 p-4 bg-surface rounded-lg">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                  {editForm.profile_photo ? (
                    <img src={editForm.profile_photo} alt={editForm.full_name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-xl font-bold text-primary">{editForm.full_name?.charAt(0)}</span>
                  )}
                </div>
                <div className="flex-1">
                  <Label>Profile Photo URL</Label>
                  <Input
                    value={editForm.profile_photo}
                    onChange={(e) => setEditForm({ ...editForm, profile_photo: e.target.value })}
                    placeholder="https://example.com/photo.jpg"
                    className="mt-1"
                    data-testid="admin-edit-client-photo"
                  />
                </div>
              </div>
              
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Full Name *</Label>
                  <Input
                    value={editForm.full_name}
                    onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                    required
                    className="mt-1"
                    data-testid="admin-edit-client-name"
                  />
                </div>
                <div>
                  <Label>Mobile (10 digits) *</Label>
                  <Input
                    value={editForm.mobile}
                    onChange={(e) => setEditForm({ ...editForm, mobile: e.target.value })}
                    required
                    maxLength={10}
                    className="mt-1"
                    data-testid="admin-edit-client-mobile"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    className="mt-1"
                    data-testid="admin-edit-client-email"
                  />
                </div>
                <div>
                  <Label>Age</Label>
                  <Input
                    type="number"
                    value={editForm.age}
                    onChange={(e) => setEditForm({ ...editForm, age: e.target.value })}
                    className="mt-1"
                    data-testid="admin-edit-client-age"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Guardian Name</Label>
                  <Input
                    value={editForm.guardian_name}
                    onChange={(e) => setEditForm({ ...editForm, guardian_name: e.target.value })}
                    className="mt-1"
                    data-testid="admin-edit-client-guardian"
                  />
                </div>
                <div>
                  <Label>Referred By</Label>
                  <Input
                    value={editForm.referred_by}
                    onChange={(e) => setEditForm({ ...editForm, referred_by: e.target.value })}
                    className="mt-1"
                    data-testid="admin-edit-client-referred"
                  />
                </div>
              </div>
              <div>
                <Label>Address</Label>
                <Textarea
                  value={editForm.address}
                  onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                  className="mt-1"
                  data-testid="admin-edit-client-address"
                />
              </div>
              
              {/* Emergency Contact */}
              <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <AlertCircle size={16} /> Emergency Contact
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Contact Name</Label>
                    <Input
                      value={editForm.emergency_contact_name}
                      onChange={(e) => setEditForm({ ...editForm, emergency_contact_name: e.target.value })}
                      className="mt-1"
                      data-testid="admin-edit-client-emergency-name"
                    />
                  </div>
                  <div>
                    <Label>Contact Phone</Label>
                    <Input
                      value={editForm.emergency_contact_phone}
                      onChange={(e) => setEditForm({ ...editForm, emergency_contact_phone: e.target.value })}
                      className="mt-1"
                      data-testid="admin-edit-client-emergency-phone"
                    />
                  </div>
                </div>
              </div>
              
              <div>
                <Label>Intake Summary</Label>
                <Textarea
                  value={editForm.intake_summary}
                  onChange={(e) => setEditForm({ ...editForm, intake_summary: e.target.value })}
                  className="mt-1"
                  rows={3}
                  data-testid="admin-edit-client-intake"
                />
              </div>
              
              <div className="flex gap-3">
                <Button type="submit" className="flex-1" data-testid="admin-submit-edit-client">Save Changes</Button>
                <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {/* Reset Password Dialog */}
      {showPasswordDialog && selectedClient && (
        <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
          <DialogContent data-testid="admin-client-password-reset-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">
                Reset Client Password
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-foreground">
                Resetting password for: <strong>{selectedClient.full_name}</strong>
              </p>
              <div>
                <Label>New Password</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    data-testid="admin-new-client-password-input"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setNewPassword(generatePassword())}
                    data-testid="admin-regenerate-client-password-button"
                  >
                    Regenerate
                  </Button>
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={confirmPasswordReset}
                  className="flex-1"
                  data-testid="admin-confirm-client-reset-button"
                >
                  Reset Password
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowPasswordDialog(false)}
                  data-testid="admin-cancel-client-reset-button"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Link Client to Therapist Dialog */}
      {showLinkDialog && selectedClient && (
        <Dialog open={showLinkDialog} onOpenChange={setShowLinkDialog}>
          <DialogContent className="max-w-md" data-testid="link-client-dialog">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Link2 size={20} /> Link Client to Therapist
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="p-4 bg-surface rounded-lg">
                <p className="font-medium">{selectedClient.full_name}</p>
                <p className="text-sm text-muted-foreground">{selectedClient.mobile}</p>
              </div>
              
              <div>
                <Label htmlFor="therapist-select">Select Therapist</Label>
                <select
                  id="therapist-select"
                  value={selectedTherapistId}
                  onChange={(e) => setSelectedTherapistId(e.target.value)}
                  className="w-full mt-2 h-10 px-3 rounded-lg border border-border bg-white"
                  data-testid="select-therapist-dropdown"
                >
                  <option value="">-- Select a therapist --</option>
                  {therapists.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.full_name} ({t.mobile})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={confirmLinkClient}
                  className="flex-1"
                  disabled={!selectedTherapistId}
                  data-testid="confirm-link-btn"
                >
                  Link Client
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowLinkDialog(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default ClientManagement;
