import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { UserPlus, Search } from 'lucide-react';

const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [filteredClients, setFilteredClients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [editForm, setEditForm] = useState({});
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
            c.email.toLowerCase().includes(searchQuery.toLowerCase())
        )
      );
    } else {
      setFilteredClients(clients);
    }
  }, [searchQuery, clients]);

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
      setEditForm(response.data);
    } catch (error) {
      toast.error('Failed to load client details');
    }
  };

  const handleUpdateClient = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/clients/${selectedClient.id}`, {
        intake_summary: editForm.intake_summary,
        emergency_contact_name: editForm.emergency_contact_name,
        emergency_contact_phone: editForm.emergency_contact_phone,
      });
      toast.success('Client profile updated');
      fetchClients();
      setSelectedClient(null);
    } catch (error) {
      toast.error('Failed to update client');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading clients...</div>;
  }

  return (
    <div data-testid="client-management">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Client Management</h2>
          <p className="text-muted-foreground">Manage your client profiles</p>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
          <Input
            placeholder="Search clients by name or email..."
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
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => handleSelectClient(client)}
            data-testid={`client-card-${client.id}`}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium text-lg">
                {client.full_name.charAt(0)}
              </div>
              <div>
                <p className="font-medium text-foreground">{client.full_name}</p>
                <p className="text-sm text-muted-foreground">{client.email}</p>
              </div>
            </div>
            {client.intake_summary && (
              <p className="text-sm text-muted-foreground line-clamp-2">{client.intake_summary}</p>
            )}
          </Card>
        ))}
      </div>

      {filteredClients.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No clients found</p>
        </div>
      )}

      {/* Edit Client Dialog */}
      {selectedClient && (
        <Dialog open={!!selectedClient} onOpenChange={() => setSelectedClient(null)}>
          <DialogContent className="max-w-2xl" data-testid="client-edit-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">
                {selectedClient.full_name}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleUpdateClient} className="space-y-4">
              <div>
                <Label>Email</Label>
                <Input value={selectedClient.email} disabled className="mt-1" />
              </div>
              <div>
                <Label htmlFor="intake-summary">Intake Summary</Label>
                <Textarea
                  id="intake-summary"
                  data-testid="intake-summary-input"
                  value={editForm.intake_summary || ''}
                  onChange={(e) => setEditForm({ ...editForm, intake_summary: e.target.value })}
                  rows={4}
                  className="mt-1"
                  placeholder="Client's presenting concerns, history, goals..."
                />
              </div>
              <div>
                <Label htmlFor="emergency-contact-name">Emergency Contact Name</Label>
                <Input
                  id="emergency-contact-name"
                  data-testid="emergency-contact-name-input"
                  value={editForm.emergency_contact_name || ''}
                  onChange={(e) =>
                    setEditForm({ ...editForm, emergency_contact_name: e.target.value })
                  }
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="emergency-contact-phone">Emergency Contact Phone</Label>
                <Input
                  id="emergency-contact-phone"
                  data-testid="emergency-contact-phone-input"
                  value={editForm.emergency_contact_phone || ''}
                  onChange={(e) =>
                    setEditForm({ ...editForm, emergency_contact_phone: e.target.value })
                  }
                  className="mt-1"
                />
              </div>
              <div className="flex gap-3">
                <Button type="submit" className="flex-1" data-testid="save-client-button">
                  Save Changes
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedClient(null)}
                  data-testid="cancel-edit-button"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default ClientManagement;
