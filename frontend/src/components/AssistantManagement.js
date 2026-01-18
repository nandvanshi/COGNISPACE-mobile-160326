import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { UserPlus, User, Mail, MoreVertical, Trash2, Ban, CheckCircle, Key } from 'lucide-react';

const AssistantManagement = ({ isReadOnly = false }) => {
  const [assistants, setAssistants] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [selectedAssistant, setSelectedAssistant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: ''
  });
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    fetchAssistants();
  }, []);

  const fetchAssistants = async () => {
    try {
      const response = await axios.get(`${API}/assistants`);
      setAssistants(response.data);
    } catch (error) {
      toast.error('Failed to load assistants');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAssistant = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/assistants`, formData);
      toast.success('Assistant created successfully');
      setShowCreateDialog(false);
      setFormData({ email: '', password: '', full_name: '' });
      fetchAssistants();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create assistant');
    }
  };

  const handleSuspend = async (assistant) => {
    try {
      await axios.put(`${API}/assistants/${assistant.id}/suspend`);
      toast.success(`${assistant.full_name} has been suspended`);
      fetchAssistants();
    } catch (error) {
      toast.error('Failed to suspend assistant');
    }
  };

  const handleActivate = async (assistant) => {
    try {
      await axios.put(`${API}/assistants/${assistant.id}/activate`);
      toast.success(`${assistant.full_name} has been activated`);
      fetchAssistants();
    } catch (error) {
      toast.error('Failed to activate assistant');
    }
  };

  const handleDelete = async (assistant) => {
    if (!window.confirm(`Are you sure you want to delete ${assistant.full_name}? This action cannot be undone.`)) {
      return;
    }
    try {
      await axios.delete(`${API}/assistants/${assistant.id}`);
      toast.success(`${assistant.full_name} has been deleted`);
      fetchAssistants();
    } catch (error) {
      toast.error('Failed to delete assistant');
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!selectedAssistant || !newPassword) return;
    try {
      await axios.put(`${API}/assistants/${selectedAssistant.id}/reset-password?new_password=${encodeURIComponent(newPassword)}`);
      toast.success('Password reset successfully');
      setShowPasswordDialog(false);
      setNewPassword('');
      setSelectedAssistant(null);
    } catch (error) {
      toast.error('Failed to reset password');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading assistants...</div>;
  }

  return (
    <div data-testid="assistant-management">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Assistants</h2>
          <p className="text-muted-foreground">Manage your practice assistants</p>
        </div>
        {!isReadOnly && (
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="add-assistant-button"
          >
            <UserPlus size={20} className="mr-2" />
            Add Assistant
          </Button>
        )}
      </div>

      {/* Info Card */}
      <Card className="p-4 mb-6 bg-info/10 border-info/20">
        <p className="text-sm text-info">
          Assistants can manage appointments, clients (non-clinical data), and calendar blocking. 
          They cannot access session notes, assessments, protocols, or change your availability settings.
        </p>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl">
          <p className="text-3xl font-serif text-primary">{assistants.length}</p>
          <p className="text-muted-foreground">Total Assistants</p>
        </Card>
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl">
          <p className="text-3xl font-serif text-success">{assistants.filter(a => a.status === 'active').length}</p>
          <p className="text-muted-foreground">Active</p>
        </Card>
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl">
          <p className="text-3xl font-serif text-warning">{assistants.filter(a => a.status === 'suspended').length}</p>
          <p className="text-muted-foreground">Suspended</p>
        </Card>
      </div>

      {/* Assistants List */}
      {assistants.length === 0 ? (
        <Card className="p-8 text-center bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl">
          <User size={48} className="mx-auto text-muted-foreground/30 mb-4" />
          <p className="text-muted-foreground">No assistants yet. Add one to help manage your practice.</p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {assistants.map((assistant) => (
            <Card 
              key={assistant.id} 
              className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
              data-testid={`assistant-${assistant.id}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    assistant.status === 'active' ? 'bg-success/10' : 'bg-warning/10'
                  }`}>
                    <User size={24} className={assistant.status === 'active' ? 'text-success' : 'text-warning'} />
                  </div>
                  <div>
                    <p className="font-semibold text-lg">{assistant.full_name}</p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Mail size={14} />
                      <span>{assistant.email}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    assistant.status === 'active' 
                      ? 'bg-success/10 text-success' 
                      : 'bg-warning/10 text-warning'
                  }`}>
                    {assistant.status}
                  </span>
                  
                  {!isReadOnly && (
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          setSelectedAssistant(assistant);
                          setShowPasswordDialog(true);
                        }}
                        title="Reset Password"
                      >
                        <Key size={16} />
                      </Button>
                      
                      {assistant.status === 'active' ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleSuspend(assistant)}
                          title="Suspend"
                        >
                          <Ban size={16} className="text-warning" />
                        </Button>
                      ) : (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleActivate(assistant)}
                          title="Activate"
                        >
                          <CheckCircle size={16} className="text-success" />
                        </Button>
                      )}
                      
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(assistant)}
                        title="Delete"
                      >
                        <Trash2 size={16} className="text-error" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent data-testid="create-assistant-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Add New Assistant</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateAssistant} className="space-y-4">
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                placeholder="Jane Doe"
                required
                data-testid="assistant-name-input"
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="assistant@example.com"
                required
                data-testid="assistant-email-input"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Minimum 8 characters"
                required
                minLength={8}
                data-testid="assistant-password-input"
              />
            </div>
            <div className="flex gap-3 pt-4">
              <Button type="submit" className="flex-1" data-testid="create-assistant-submit">
                Create Assistant
              </Button>
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent data-testid="reset-password-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Reset Password</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleResetPassword} className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Reset password for <strong>{selectedAssistant?.full_name}</strong>
            </p>
            <div>
              <Label htmlFor="new_password">New Password</Label>
              <Input
                id="new_password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                required
                minLength={8}
                data-testid="new-password-input"
              />
            </div>
            <div className="flex gap-3 pt-4">
              <Button type="submit" className="flex-1" data-testid="reset-password-submit">
                Reset Password
              </Button>
              <Button type="button" variant="outline" onClick={() => {
                setShowPasswordDialog(false);
                setNewPassword('');
                setSelectedAssistant(null);
              }}>
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AssistantManagement;
