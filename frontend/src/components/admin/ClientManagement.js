import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Key, Search, Eye, User, Phone, Mail, MapPin, AlertCircle } from 'lucide-react';

const ClientManagement = ({ onViewTherapist }) => {
  const [clients, setClients] = useState([]);
  const [filteredClients, setFilteredClients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [clientDetail, setClientDetail] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClients();
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

  const handleViewDetail = async (client) => {
    try {
      const response = await axios.get(`${API}/admin/clients/${client.id}`);
      setClientDetail(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      toast.error('Failed to load client details');
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
      await axios.post(
        `${API}/admin/clients/${selectedClient.id}/reset-password?new_password=${newPassword}`
      );
      toast.success(`Password reset! New password: ${newPassword}`);
      setShowPasswordDialog(false);
    } catch (error) {
      toast.error('Failed to reset password');
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
            data-testid="client-search-input"
          />
        </div>
      </div>

      {/* Clients Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredClients.map((client) => (
          <Card
            key={client.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
            data-testid={`client-${client.id}`}
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="text-lg font-medium text-foreground">{client.full_name}</h4>
                  {client.client_id && (
                    <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">
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
                    <p className="flex items-center gap-2 mt-2">
                      <span className="px-2 py-1 bg-info/10 text-info text-xs rounded-full">
                        Therapist: {client.therapist_name}
                      </span>
                    </p>
                  )}
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <Button
                  onClick={() => handleViewDetail(client)}
                  variant="outline"
                  size="sm"
                  data-testid={`view-client-${client.id}`}
                >
                  <Eye size={16} className="mr-1" />
                  View
                </Button>
                <Button
                  onClick={() => handleResetPassword(client)}
                  variant="outline"
                  size="sm"
                  data-testid={`reset-password-${client.id}`}
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

      <div className="mt-8 p-6 bg-info/10 border border-info/20 rounded-xl">
        <p className="text-sm text-info">
          <strong>Privacy Note:</strong> Session notes, assessments, and messages are NOT accessible
          to admin for client privacy protection.
        </p>
      </div>

      {/* Client Detail Dialog */}
      {showDetailDialog && clientDetail && (
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-lg" data-testid="client-detail-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">Client Profile</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-2xl font-bold text-primary">{clientDetail.full_name?.charAt(0)}</span>
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
                      data-testid="view-therapist-button"
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

      {/* Reset Password Dialog */}
      {showPasswordDialog && selectedClient && (
        <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
          <DialogContent data-testid="client-password-reset-dialog">
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
                    data-testid="new-client-password-input"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setNewPassword(generatePassword())}
                    data-testid="regenerate-client-password-button"
                  >
                    Regenerate
                  </Button>
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={confirmPasswordReset}
                  className="flex-1"
                  data-testid="confirm-client-reset-button"
                >
                  Reset Password
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowPasswordDialog(false)}
                  data-testid="cancel-client-reset-button"
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
