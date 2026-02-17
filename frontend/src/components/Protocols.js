import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Plus, BookOpen, Sparkles, Trash2 } from 'lucide-react';

const Protocols = ({ isReadOnly = false }) => {
  const [protocols, setProtocols] = useState([]);
  const [clients, setClients] = useState([]);
  const [templates, setTemplates] = useState({});
  const [showDialog, setShowDialog] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [selectedProtocol, setSelectedProtocol] = useState(null);
  const [newProtocol, setNewProtocol] = useState({
    client_id: '',
    template: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [protocolsRes, clientsRes, templatesRes] = await Promise.all([
        axios.get(`${API}/protocols`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/protocols/templates`),
      ]);
      setProtocols(protocolsRes.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      setClients(clientsRes.data);
      setTemplates(templatesRes.data);
    } catch (error) {
      toast.error('Failed to load protocols');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProtocol = async (e) => {
    e.preventDefault();

    if (!newProtocol.client_id || !newProtocol.template) {
      toast.error('Please select a client and template');
      return;
    }

    const templateData = templates[newProtocol.template];
    if (!templateData) {
      toast.error('Invalid template');
      return;
    }

    try {
      await axios.post(`${API}/protocols`, {
        client_id: newProtocol.client_id,
        modality: templateData.modality,
        condition: templateData.condition,
        sessions: templateData.sessions,
      });
      toast.success('Protocol created');
      setShowDialog(false);
      setNewProtocol({ client_id: '', template: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to create protocol');
    }
  };

  const handleDeleteProtocol = async (protocolId) => {
    if (!window.confirm('Are you sure you want to delete this protocol?')) return;
    
    try {
      await axios.delete(`${API}/protocols/${protocolId}`);
      toast.success('Protocol deleted');
      setSelectedProtocol(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to delete protocol');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading protocols...</div>;
  }

  return (
    <div data-testid="protocols">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Treatment Protocols</h2>
          <p className="text-muted-foreground">Build and customize evidence-based treatment plans</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => setShowTemplates(true)}
            variant="outline"
            data-testid="view-templates-button"
          >
            <Sparkles size={20} className="mr-2" />
            Templates
          </Button>
          <Button
            onClick={() => setShowDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="create-protocol-button"
          >
            <Plus size={20} className="mr-2" />
            New Protocol
          </Button>
        </div>
      </div>

      {/* Protocols List */}
      <div className="space-y-4">
        {protocols.map((protocol) => (
          <Card
            key={protocol.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setSelectedProtocol(protocol)}
            data-testid={`protocol-${protocol.id}`}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="font-medium text-lg text-foreground">{protocol.client_name}</p>
                <p className="text-sm text-muted-foreground">
                  {protocol.modality} for {protocol.condition}
                </p>
              </div>
              <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-secondary/10 text-secondary">
                {protocol.sessions?.length || 0} Sessions
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {protocol.sessions?.slice(0, 4).map((session) => (
                <div key={session.session_number || session.number} className="p-2 bg-surface rounded-lg text-center">
                  <p className="text-xs text-muted-foreground">Session {session.session_number || session.number}</p>
                  <p className="text-xs font-medium truncate">{session.title || session.focus}</p>
                </div>
              ))}
            </div>
          </Card>
        ))}

        {protocols.length === 0 && (
          <div className="text-center py-12">
            <BookOpen size={48} className="mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No protocols created yet</p>
            <p className="text-sm text-muted-foreground mt-1">Create a protocol from our templates above</p>
          </div>
        )}
      </div>

      {/* Create Protocol Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="protocol-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Create Treatment Protocol</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateProtocol} className="space-y-4">
            <div>
              <Label htmlFor="protocol-client">Client</Label>
              <select
                id="protocol-client"
                data-testid="protocol-client-select"
                value={newProtocol.client_id}
                onChange={(e) => setNewProtocol({ ...newProtocol, client_id: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
                required
              >
                <option value="">Select a client</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="protocol-template">Protocol Template</Label>
              <select
                id="protocol-template"
                data-testid="protocol-template-select"
                value={newProtocol.template}
                onChange={(e) => setNewProtocol({ ...newProtocol, template: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
                required
              >
                <option value="">Select a template</option>
                {Object.entries(templates).map(([key, value]) => (
                  <option key={key} value={key}>
                    {value.name || key} - {value.modality} for {value.condition}
                  </option>
                ))}
              </select>
            </div>
            {newProtocol.template && templates[newProtocol.template] && (
              <div className="p-4 bg-surface rounded-lg">
                <p className="font-medium text-foreground mb-1">
                  {templates[newProtocol.template].name}
                </p>
                <p className="text-sm text-muted-foreground mb-3">
                  {templates[newProtocol.template].description}
                </p>
                <p className="text-sm font-medium text-foreground mb-2">
                  {templates[newProtocol.template].sessions.length} sessions planned:
                </p>
                <ul className="text-xs text-muted-foreground space-y-1 max-h-40 overflow-y-auto">
                  {templates[newProtocol.template].sessions.map((s) => (
                    <li key={s.session_number}>
                      Session {s.session_number}: {s.title}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="save-protocol-button">
                Create Protocol
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                data-testid="cancel-protocol-button"
              >
                Cancel
              </Button>
            </div>
          </form>
          <div className="mt-4 p-4 bg-info/10 border border-info/20 rounded-lg">
            <p className="text-sm text-info">
              <strong>Editable Template:</strong> You can customize this protocol after creation to fit your
              client's specific needs.
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Protocol Dialog */}
      {selectedProtocol && (
        <Dialog open={!!selectedProtocol} onOpenChange={() => setSelectedProtocol(null)}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="view-protocol-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">
                {selectedProtocol.modality} Protocol - {selectedProtocol.client_name}
              </DialogTitle>
              <p className="text-sm text-muted-foreground">For {selectedProtocol.condition}</p>
            </DialogHeader>
            <div className="space-y-4">
              {selectedProtocol.sessions?.length > 0 ? (
                selectedProtocol.sessions.map((session) => (
                  <Card key={session.session_number || session.number} className="p-4 bg-surface">
                    <h4 className="font-medium text-primary mb-2">
                      Session {session.session_number || session.number}: {session.title || session.focus}
                    </h4>
                    {session.goals && session.goals.length > 0 && (
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {session.goals.map((goal, idx) => (
                          <li key={idx}>• {goal}</li>
                        ))}
                      </ul>
                    )}
                    {session.activities && session.activities.length > 0 && (
                      <ul className="text-sm text-muted-foreground space-y-1">
                        {session.activities.map((activity, idx) => (
                          <li key={idx}>• {activity}</li>
                        ))}
                      </ul>
                    )}
                  </Card>
                ))
              ) : (
                <p className="text-center text-muted-foreground py-8">No sessions in this protocol</p>
              )}
            </div>
            <div className="flex gap-3 mt-4">
              <Button onClick={() => setSelectedProtocol(null)} className="flex-1" data-testid="close-protocol-button">
                Close
              </Button>
              {!isReadOnly && (
                <Button 
                  variant="destructive" 
                  onClick={() => handleDeleteProtocol(selectedProtocol.id)}
                  data-testid="delete-protocol-button"
                >
                  <Trash2 size={16} className="mr-2" /> Delete Protocol
                </Button>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Template Library Dialog */}
      <Dialog open={showTemplates} onOpenChange={setShowTemplates}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="templates-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Protocol Templates Library</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {Object.entries(templates).map(([key, value]) => (
              <Card key={key} className="p-4 bg-surface" data-testid={`template-${key}`}>
                <h4 className="font-medium text-lg text-primary mb-1">{value.name || key}</h4>
                <p className="text-sm text-muted-foreground mb-2">{value.description}</p>
                <p className="text-sm text-foreground mb-2">
                  <strong>{value.modality}</strong> approach for <strong>{value.condition}</strong>
                </p>
                <p className="text-xs text-muted-foreground mb-2">{value.sessions?.length || 0} sessions</p>
                <div className="mt-3 space-y-1">
                  {value.sessions?.slice(0, 4).map((s) => (
                    <p key={s.session_number} className="text-xs text-muted-foreground">
                      • Session {s.session_number}: {s.title}
                    </p>
                  ))}
                  {value.sessions?.length > 4 && (
                    <p className="text-xs text-muted-foreground">... and {value.sessions.length - 4} more</p>
                  )}
                </div>
              </Card>
            ))}
            {Object.keys(templates).length === 0 && (
              <p className="text-center text-muted-foreground py-8">No templates available</p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Clinical Notice */}
      <div className="mt-8 p-6 bg-info/10 border border-info/20 rounded-xl">
        <p className="text-sm text-info">
          <strong>Evidence-Based Templates:</strong> Protocols are based on evidence-based practices but
          should be customized to each client's unique needs and clinical presentation.
        </p>
      </div>
    </div>
  );
};

export default Protocols;
