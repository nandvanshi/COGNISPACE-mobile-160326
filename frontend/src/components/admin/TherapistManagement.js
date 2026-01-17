import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Ban, CheckCircle, Key } from 'lucide-react';

const TherapistManagement = () => {
  const [therapists, setTherapists] = useState([]);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [selectedTherapist, setSelectedTherapist] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTherapists();
  }, []);

  const fetchTherapists = async () => {
    try {
      const response = await axios.get(`${API}/api/admin/therapists`);
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
      await axios.post(`${API}/api/admin/therapists/${therapistId}/suspend`);
      toast.success('Therapist suspended');
      fetchTherapists();
    } catch (error) {
      toast.error('Failed to suspend therapist');
    }
  };

  const handleActivate = async (therapistId) => {
    try {
      await axios.post(`${API}/api/admin/therapists/${therapistId}/activate`);
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
        `${API}/api/admin/therapists/${selectedTherapist.id}/reset-password?new_password=${newPassword}`
      );
      toast.success(`Password reset! New password: ${newPassword}`);
      setShowPasswordDialog(false);
    } catch (error) {
      toast.error('Failed to reset password');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading therapists...</div>;
  }

  return (
    <div data-testid="therapist-management">
      <div className="mb-8">
        <h2 className="text-4xl font-serif text-primary mb-2">Therapist Management</h2>
        <p className="text-muted-foreground">Manage therapist accounts and subscriptions</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {therapists.map((therapist) => (
          <Card
            key={therapist.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
            data-testid={`therapist-${therapist.id}`}
          >
            <div className="flex justify-between items-start">
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
                <p className="text-sm text-muted-foreground">
                  Credentials: {therapist.credentials}
                </p>
                {therapist.specialization && (
                  <p className="text-sm text-muted-foreground">
                    Specialization: {therapist.specialization}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
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
                <Button
                  onClick={() => handleResetPassword(therapist)}
                  variant="outline"
                  size="sm"
                  data-testid={`reset-password-${therapist.id}`}
                >
                  <Key size={16} className="mr-2" />
                  Reset Password
                </Button>
              </div>
            </div>
          </Card>
        ))}

        {therapists.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No therapists found</p>
          </div>
        )}
      </div>

      {/* Reset Password Dialog */}
      {showPasswordDialog && selectedTherapist && (
        <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
          <DialogContent data-testid="password-reset-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">
                Reset Password
              </DialogTitle>
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
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setNewPassword(generatePassword())}
                    data-testid="regenerate-button"
                  >
                    Regenerate
                  </Button>
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={confirmPasswordReset}
                  className="flex-1"
                  data-testid="confirm-reset-button"
                >
                  Reset Password
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowPasswordDialog(false)}
                  data-testid="cancel-reset-button"
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

export default TherapistManagement;
