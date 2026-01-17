import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Key, Search } from 'lucide-react';

const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [filteredClients, setFilteredClients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
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
            c.mobile.includes(searchQuery) ||
            (c.email && c.email.toLowerCase().includes(searchQuery.toLowerCase()))
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
        `${API}/api/admin/clients/${selectedClient.id}/reset-password?new_password=${newPassword}`
      );
      toast.success(`Password reset! New password: ${newPassword}`);
      setShowPasswordDialog(false);
    } catch (error) {
      toast.error('Failed to reset password');
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
            placeholder="Search clients by name, mobile, or email..."
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
                <h4 className="text-lg font-medium text-foreground">{client.full_name}</h4>
                <p className="text-sm text-muted-foreground mt-1">Mobile: {client.mobile}</p>
                <p className="text-sm text-muted-foreground">Email: {client.email || 'N/A'}</p>
                {client.client_id && (
                  <p className="text-xs text-muted-foreground mt-2">ID: {client.client_id}</p>
                )}
              </div>
              <Button
                onClick={() => handleResetPassword(client)}
                variant="outline"
                size="sm"
                data-testid={`reset-password-${client.id}`}
              >
                <Key size={16} className="mr-2" />
                Reset Password
              </Button>
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
