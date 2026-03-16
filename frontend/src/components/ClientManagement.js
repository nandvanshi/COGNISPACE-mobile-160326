import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { VoiceTextarea as Textarea } from './VoiceTextarea';
import { toast } from 'sonner';
import { UserPlus, Search, Key, Camera, Edit, User, Phone, Mail, MapPin, AlertCircle, Eye } from 'lucide-react';

const ClientManagement = ({ isReadOnly = false, isAssistant = false, initialClientId = null, initialFilter = null, filterData = null, onClearContext = () => {} }) => {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [filteredClients, setFilteredClients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState(initialFilter);
  const [selectedClient, setSelectedClient] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [newClient, setNewClient] = useState({
    mobile: '',
    full_name: '',
    password: '',
    email: '',
    age: '',
    guardian_name: '',
    address: '',
    referred_by: '',
    intake_summary: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClients();
  }, []);

  // Handle initial client ID - open profile view when provided
  useEffect(() => {
    if (initialClientId && clients.length > 0) {
      const client = clients.find(c => c.id === initialClientId);
      if (client) {
        handleViewProfile(client);
        onClearContext(); // Clear context after handling
      }
    }
  }, [initialClientId, clients]);

  // Update activeFilter when initialFilter prop changes
  useEffect(() => {
    setActiveFilter(initialFilter);
  }, [initialFilter]);

  useEffect(() => {
    let result = clients;
    
    // Apply inactive filter if active
    if (activeFilter === 'inactive' && filterData && filterData.length > 0) {
      result = clients.filter(c => filterData.includes(c.id));
    }
    
    // Apply search query
    if (searchQuery) {
      result = result.filter(
        (c) =>
          c.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (c.mobile && c.mobile.includes(searchQuery)) ||
          (c.email && c.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
          (c.client_id && c.client_id.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }
    
    setFilteredClients(result);
  }, [searchQuery, clients, activeFilter, filterData]);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
      setFilteredClients(response.data);
    } catch (error) {
      toast.error('Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectClient = async (client) => {
    try {
      const response = await axios.get(`${API}/clients/${client.id}`);
      setSelectedClient(response.data);
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
    
    // Validate mobile if changed
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
      
      // Remove undefined values
      Object.keys(updateData).forEach(key => updateData[key] === undefined && delete updateData[key]);
      
      await axios.put(`${API}/clients/${selectedClient.id}`, updateData);
      toast.success('Client profile updated successfully');
      setShowEditDialog(false);
      setSelectedClient(null);
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update client');
    }
  };

  const handleAddClient = async (e) => {
    e.preventDefault();
    
    if (!/^\d{10}$/.test(newClient.mobile)) {
      toast.error('Mobile number must be exactly 10 digits');
      return;
    }
    
    try {
      const clientData = {
        ...newClient,
        age: newClient.age ? parseInt(newClient.age) : null,
        email: newClient.email || null,
      };
      await axios.post(`${API}/clients`, clientData);
      toast.success('Client added successfully');
      setShowAddDialog(false);
      setNewClient({
        mobile: '',
        full_name: '',
        password: '',
        email: '',
        age: '',
        guardian_name: '',
        address: '',
        referred_by: '',
        intake_summary: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
      });
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add client');
    }
  };

  const handleResetPassword = (client) => {
    setSelectedClient(client);
    setNewPassword(generatePassword());
    setShowPasswordDialog(true);
  };

  const handleViewProfile = (client) => {
    // Navigate to full-page client profile - different route for assistant
    if (isAssistant) {
      navigate(`/assistant/clients/${client.id}`);
    } else {
      navigate(`/therapist/clients/${client.id}`);
    }
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
      await axios.post(`${API}/clients/${selectedClient.id}/reset-password`, {
        new_password: newPassword
      });
      toast.success(`Password reset! New password: ${newPassword}`);
      setShowPasswordDialog(false);
      setSelectedClient(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading clients...</div>;
  }

  const clearFilter = () => {
    setActiveFilter(null);
    onClearContext();
  };

  return (
    <div data-testid="client-management">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Client Management</h2>
          <p className="text-muted-foreground">Manage your client profiles</p>
        </div>
        <Button
          onClick={() => setShowAddDialog(true)}
          className="bg-primary hover:bg-primary-700 rounded-full"
          data-testid="add-client-button"
          disabled={isReadOnly}
          title={isReadOnly ? 'Subscription expired - Read-only mode' : ''}
        >
          <UserPlus size={20} className="mr-2" />
          Add Client
        </Button>
      </div>

      {/* Active Filter Banner */}
      {activeFilter === 'inactive' && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between" data-testid="inactive-filter-banner">
          <div className="flex items-center gap-2 text-amber-800">
            <AlertCircle size={18} />
            <span className="text-sm font-medium">Showing inactive clients (no sessions in 30+ days)</span>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={clearFilter}
            className="text-amber-700 hover:text-amber-900 hover:bg-amber-100"
            data-testid="clear-filter-btn"
          >
            Show All Clients
          </Button>
        </div>
      )}

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
          <Input
            placeholder="Search clients by name, mobile, email, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            data-testid="client-search-input"
          />
        </div>
      </div>

      {/* Clients Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredClients.map((client) => (
          <Card
            key={client.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
            data-testid={`client-card-${client.id}`}
          >
            <div className="flex items-start gap-4">
              {/* Avatar */}
              <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden flex-shrink-0">
                {client.profile_photo ? (
                  <img src={client.profile_photo} alt={client.full_name} className="w-full h-full object-cover" />
                ) : (
                  <span className="text-xl font-bold text-primary">{client.full_name?.charAt(0)}</span>
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-lg font-medium text-foreground truncate">{client.full_name}</h4>
                </div>
                {client.client_id && (
                  <span className="inline-block px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full mb-2">
                    {client.client_id}
                  </span>
                )}
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
                </div>
              </div>
            </div>
            
            <div className="flex gap-2 mt-4 pt-4 border-t border-border/40">
              <Button
                onClick={() => handleViewProfile(client)}
                variant="default"
                size="sm"
                className="flex-1"
                data-testid={`view-profile-${client.id}`}
              >
                <Eye size={16} className="mr-1" />
                View Profile
              </Button>
              <Button
                onClick={() => handleSelectClient(client)}
                variant="outline"
                size="sm"
                className="flex-1"
                disabled={isReadOnly}
                data-testid={`edit-client-${client.id}`}
              >
                <Edit size={16} className="mr-1" />
                Edit
              </Button>
              <Button
                onClick={() => handleResetPassword(client)}
                variant="outline"
                size="sm"
                disabled={isReadOnly}
                data-testid={`reset-pw-${client.id}`}
              >
                <Key size={16} />
              </Button>
            </div>
          </Card>
        ))}

        {filteredClients.length === 0 && (
          <div className="col-span-full text-center py-12">
            <p className="text-muted-foreground">No clients found</p>
          </div>
        )}
      </div>

      {/* Add Client Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="add-client-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Add New Client</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddClient} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Full Name *</Label>
                <Input
                  value={newClient.full_name}
                  onChange={(e) => setNewClient({ ...newClient, full_name: e.target.value })}
                  required
                  className="mt-1"
                  data-testid="new-client-name"
                />
              </div>
              <div>
                <Label>Mobile (10 digits) *</Label>
                <Input
                  value={newClient.mobile}
                  onChange={(e) => setNewClient({ ...newClient, mobile: e.target.value })}
                  required
                  maxLength={10}
                  className="mt-1"
                  data-testid="new-client-mobile"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Email</Label>
                <Input
                  type="email"
                  value={newClient.email}
                  onChange={(e) => setNewClient({ ...newClient, email: e.target.value })}
                  className="mt-1"
                  data-testid="new-client-email"
                />
              </div>
              <div>
                <Label>Password *</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    value={newClient.password}
                    onChange={(e) => setNewClient({ ...newClient, password: e.target.value })}
                    required
                    data-testid="new-client-password"
                  />
                  <Button type="button" variant="outline" onClick={() => setNewClient({ ...newClient, password: generatePassword() })}>
                    Generate
                  </Button>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Age</Label>
                <Input
                  type="number"
                  value={newClient.age}
                  onChange={(e) => setNewClient({ ...newClient, age: e.target.value })}
                  className="mt-1"
                  data-testid="new-client-age"
                />
              </div>
              <div>
                <Label>Guardian Name</Label>
                <Input
                  value={newClient.guardian_name}
                  onChange={(e) => setNewClient({ ...newClient, guardian_name: e.target.value })}
                  className="mt-1"
                  data-testid="new-client-guardian"
                />
              </div>
            </div>
            <div>
              <Label>Address</Label>
              <Textarea
                value={newClient.address}
                onChange={(e) => setNewClient({ ...newClient, address: e.target.value })}
                className="mt-1"
                data-testid="new-client-address"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Referred By</Label>
                <Input
                  value={newClient.referred_by}
                  onChange={(e) => setNewClient({ ...newClient, referred_by: e.target.value })}
                  className="mt-1"
                  data-testid="new-client-referred"
                />
              </div>
            </div>
            <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <AlertCircle size={16} /> Emergency Contact
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Contact Name</Label>
                  <Input
                    value={newClient.emergency_contact_name}
                    onChange={(e) => setNewClient({ ...newClient, emergency_contact_name: e.target.value })}
                    className="mt-1"
                    data-testid="new-client-emergency-name"
                  />
                </div>
                <div>
                  <Label>Contact Phone</Label>
                  <Input
                    value={newClient.emergency_contact_phone}
                    onChange={(e) => setNewClient({ ...newClient, emergency_contact_phone: e.target.value })}
                    className="mt-1"
                    data-testid="new-client-emergency-phone"
                  />
                </div>
              </div>
            </div>
            <div>
              <Label>Intake Summary</Label>
              <Textarea
                value={newClient.intake_summary}
                onChange={(e) => setNewClient({ ...newClient, intake_summary: e.target.value })}
                className="mt-1"
                rows={3}
                data-testid="new-client-intake"
              />
            </div>
            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="submit-add-client">Add Client</Button>
              <Button type="button" variant="outline" onClick={() => setShowAddDialog(false)}>Cancel</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Client Dialog */}
      {showEditDialog && selectedClient && (
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="edit-client-dialog">
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
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center overflow-hidden">
                  {editForm.profile_photo ? (
                    <img src={editForm.profile_photo} alt={editForm.full_name} className="w-full h-full object-cover" />
                  ) : (
                    <span className="text-2xl font-bold text-primary">{editForm.full_name?.charAt(0)}</span>
                  )}
                </div>
                <div className="flex-1">
                  <Label>Profile Photo URL</Label>
                  <Input
                    value={editForm.profile_photo}
                    onChange={(e) => setEditForm({ ...editForm, profile_photo: e.target.value })}
                    placeholder="https://example.com/photo.jpg"
                    className="mt-1"
                    data-testid="edit-client-photo"
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
                    data-testid="edit-client-name"
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
                    data-testid="edit-client-mobile"
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
                    data-testid="edit-client-email"
                  />
                </div>
                <div>
                  <Label>Age</Label>
                  <Input
                    type="number"
                    value={editForm.age}
                    onChange={(e) => setEditForm({ ...editForm, age: e.target.value })}
                    className="mt-1"
                    data-testid="edit-client-age"
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
                    data-testid="edit-client-guardian"
                  />
                </div>
                <div>
                  <Label>Referred By</Label>
                  <Input
                    value={editForm.referred_by}
                    onChange={(e) => setEditForm({ ...editForm, referred_by: e.target.value })}
                    className="mt-1"
                    data-testid="edit-client-referred"
                  />
                </div>
              </div>
              <div>
                <Label>Address</Label>
                <Textarea
                  value={editForm.address}
                  onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                  className="mt-1"
                  data-testid="edit-client-address"
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
                      data-testid="edit-client-emergency-name"
                    />
                  </div>
                  <div>
                    <Label>Contact Phone</Label>
                    <Input
                      value={editForm.emergency_contact_phone}
                      onChange={(e) => setEditForm({ ...editForm, emergency_contact_phone: e.target.value })}
                      className="mt-1"
                      data-testid="edit-client-emergency-phone"
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
                  data-testid="edit-client-intake"
                />
              </div>
              
              <div className="flex gap-3">
                <Button type="submit" className="flex-1" data-testid="submit-edit-client">Save Changes</Button>
                <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {/* Reset Password Dialog */}
      {showPasswordDialog && selectedClient && (
        <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
          <DialogContent data-testid="reset-password-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Reset Client Password</DialogTitle>
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
                    data-testid="new-password-input"
                  />
                  <Button type="button" variant="outline" onClick={() => setNewPassword(generatePassword())}>
                    Regenerate
                  </Button>
                </div>
              </div>
              <div className="flex gap-3">
                <Button onClick={confirmPasswordReset} className="flex-1" data-testid="confirm-reset-btn">
                  Reset Password
                </Button>
                <Button variant="outline" onClick={() => setShowPasswordDialog(false)}>
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
