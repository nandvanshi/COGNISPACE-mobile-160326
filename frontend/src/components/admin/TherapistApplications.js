import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Check, X, Eye, Building2, MapPin, CreditCard, Calendar, Mail, Phone, User } from 'lucide-react';

const TherapistApplications = () => {
  const [applications, setApplications] = useState([]);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedApp, setSelectedApp] = useState(null);
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      const response = await axios.get(`${API}/admin/therapist-applications`);
      setApplications(response.data);
    } catch (error) {
      toast.error('Failed to load applications');
    } finally {
      setLoading(false);
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

  const handleApprove = (app) => {
    setSelectedApp(app);
    // Only generate password if application doesn't have one
    if (!app.has_password) {
      setGeneratedPassword(generatePassword());
    } else {
      setGeneratedPassword('');
    }
    setShowApproveDialog(true);
  };

  const handleViewDetail = (app) => {
    setSelectedApp(app);
    setShowDetailDialog(true);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const confirmApproval = async () => {
    try {
      // Only send password if application doesn't have one
      const url = selectedApp.has_password 
        ? `${API}/admin/therapist-applications/${selectedApp.id}/approve`
        : `${API}/admin/therapist-applications/${selectedApp.id}/approve?password=${generatedPassword}`;
      
      await axios.post(url);
      
      if (selectedApp.has_password) {
        toast.success(`Therapist approved! They can login with their registered password.`);
      } else {
        toast.success(`Therapist approved! Password: ${generatedPassword}`);
      }
      setShowApproveDialog(false);
      fetchApplications();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve application');
    }
  };

  const handleReject = async (appId) => {
    if (!window.confirm('Are you sure you want to reject this application?')) return;

    try {
      await axios.post(`${API}/admin/therapist-applications/${appId}/reject`);
      toast.success('Application rejected');
      fetchApplications();
    } catch (error) {
      toast.error('Failed to reject application');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading applications...</div>;
  }

  const pendingApps = applications.filter((a) => a.status === 'pending_approval');
  const processedApps = applications.filter((a) => a.status !== 'pending_approval');

  return (
    <div data-testid="therapist-applications">
      <div className="mb-8">
        <h2 className="text-4xl font-serif text-primary mb-2">Therapist Applications</h2>
        <p className="text-muted-foreground">Review and approve new therapist applications</p>
      </div>

      {/* Pending Applications */}
      <div className="mb-8">
        <h3 className="text-2xl font-serif text-primary mb-4">Pending ({pendingApps.length})</h3>
        {pendingApps.length === 0 ? (
          <p className="text-muted-foreground">No pending applications</p>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {pendingApps.map((app) => (
              <Card
                key={app.id}
                className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
                data-testid={`application-${app.id}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="text-lg font-medium text-foreground">{app.full_name}</h4>
                    <p className="text-sm text-muted-foreground mt-1">Mobile: {app.mobile}</p>
                    <p className="text-sm text-muted-foreground">Email: {app.email}</p>
                    <p className="text-sm text-foreground mt-2">
                      <strong>Credentials:</strong> {app.credentials}
                    </p>
                    {app.specialization && (
                      <p className="text-sm text-muted-foreground mt-1">
                        <strong>Specialization:</strong> {app.specialization}
                      </p>
                    )}
                    {app.years_of_experience && (
                      <p className="text-sm text-muted-foreground">
                        <strong>Experience:</strong> {app.years_of_experience} years
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleApprove(app)}
                      className="bg-success hover:bg-success/80"
                      data-testid={`approve-${app.id}`}
                    >
                      <Check size={20} className="mr-2" />
                      Approve
                    </Button>
                    <Button
                      onClick={() => handleReject(app.id)}
                      variant="destructive"
                      data-testid={`reject-${app.id}`}
                    >
                      <X size={20} className="mr-2" />
                      Reject
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Processed Applications */}
      {processedApps.length > 0 && (
        <div>
          <h3 className="text-2xl font-serif text-primary mb-4">Processed ({processedApps.length})</h3>
          <div className="grid grid-cols-1 gap-4">
            {processedApps.map((app) => (
              <Card
                key={app.id}
                className="p-6 bg-surface opacity-60"
                data-testid={`processed-${app.id}`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-lg font-medium text-foreground">{app.full_name}</h4>
                    <p className="text-sm text-muted-foreground">Mobile: {app.mobile}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      app.status === 'approved'
                        ? 'bg-success/10 text-success'
                        : 'bg-error/10 text-error'
                    }`}
                  >
                    {app.status}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Approve Dialog */}
      {showApproveDialog && selectedApp && (
        <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
          <DialogContent data-testid="approve-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">
                Approve Therapist
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-foreground">
                Approving: <strong>{selectedApp.full_name}</strong>
              </p>
              
              {/* Show password field only if application doesn't have password */}
              {!selectedApp.has_password ? (
                <div>
                  <Label>Generated Password</Label>
                  <div className="flex gap-2 mt-1">
                    <Input
                      value={generatedPassword}
                      onChange={(e) => setGeneratedPassword(e.target.value)}
                      data-testid="generated-password-input"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setGeneratedPassword(generatePassword())}
                      data-testid="regenerate-password-button"
                    >
                      Regenerate
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Share this password with the therapist securely. They can change it later.
                  </p>
                </div>
              ) : (
                <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
                  <p className="text-sm text-success">
                    <strong>✓ Password Already Set:</strong> The therapist provided their password during registration. They can login with their registered credentials.
                  </p>
                </div>
              )}
              
              <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
                <p className="text-sm text-warning">
                  <strong>Important:</strong> Account will be created with a 30-day free trial.
                </p>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={confirmApproval}
                  className="flex-1 bg-success hover:bg-success/80"
                  data-testid="confirm-approve-button"
                >
                  Confirm Approval
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowApproveDialog(false)}
                  data-testid="cancel-approve-button"
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

export default TherapistApplications;
