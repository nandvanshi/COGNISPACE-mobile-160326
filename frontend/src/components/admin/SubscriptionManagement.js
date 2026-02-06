import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Switch } from '../ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Plus, Trash2, CreditCard, Settings, FileText, ClipboardCheck, Brain, BookOpen, MessageSquare, DollarSign, Users, BarChart, Mail, Phone, Edit } from 'lucide-react';

// Feature toggle configuration with icons and labels
const FEATURE_CONFIG = [
  { key: 'session_notes', label: 'Session Notes', icon: FileText, description: 'SOAP/DAP clinical notes' },
  { key: 'assessments', label: 'Assessments', icon: ClipboardCheck, description: 'Clinical assessment tools' },
  { key: 'ai_clinical', label: 'TheraGenie', icon: Brain, description: 'CI-powered insights' },
  { key: 'protocols', label: 'Protocols', icon: BookOpen, description: 'Therapy protocols' },
  { key: 'messaging', label: 'Messaging', icon: MessageSquare, description: 'Client messaging' },
  { key: 'payments', label: 'Payments', icon: DollarSign, description: 'Payment tracking' },
  { key: 'assistants', label: 'Assistants', icon: Users, description: 'Therapist assistants' },
  { key: 'reports', label: 'Reports', icon: BarChart, description: 'Analytics & reports' },
  { key: 'email_notifications', label: 'Email Notifications', icon: Mail, description: 'Send emails to clients' },
  { key: 'whatsapp_notifications', label: 'WhatsApp Notifications', icon: Phone, description: 'Send WhatsApp messages' },
];

const SubscriptionManagement = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showFeaturesDialog, setShowFeaturesDialog] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [newPlan, setNewPlan] = useState({
    name: '',
    price: '',
    duration_days: 30,
    features: '',
    max_clients: '',
  });
  const [editPlan, setEditPlan] = useState({
    name: '',
    price: '',
    duration_days: '',
    features: '',
    max_clients: '',
  });
  const [featureToggles, setFeatureToggles] = useState({});

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const res = await axios.get(`${API}/admin/subscription-plans`);
      setPlans(res.data);
    } catch (error) {
      toast.error('Failed to fetch plans');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async (e) => {
    e.preventDefault();
    
    if (!newPlan.name || !newPlan.price || !newPlan.duration_days) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      // All features enabled by default for new plans
      const defaultToggles = {};
      FEATURE_CONFIG.forEach(f => defaultToggles[f.key] = true);

      await axios.post(`${API}/admin/subscription-plans`, {
        name: newPlan.name,
        price: parseFloat(newPlan.price),
        duration_days: parseInt(newPlan.duration_days),
        features: newPlan.features.split(',').map(f => f.trim()).filter(f => f),
        max_clients: newPlan.max_clients ? parseInt(newPlan.max_clients) : null,
        feature_toggles: defaultToggles
      });
      
      toast.success('Plan created successfully');
      setShowCreateDialog(false);
      setNewPlan({ name: '', price: '', duration_days: 30, features: '', max_clients: '' });
      fetchPlans();
    } catch (error) {
      toast.error('Failed to create plan');
    }
  };

  const handleDeletePlan = async (planId) => {
    if (!confirm('Are you sure you want to delete this plan?')) return;
    
    try {
      await axios.delete(`${API}/admin/subscription-plans/${planId}`);
      toast.success('Plan deleted');
      fetchPlans();
    } catch (error) {
      toast.error('Failed to delete plan');
    }
  };

  const openEditDialog = (plan) => {
    setSelectedPlan(plan);
    setEditPlan({
      name: plan.name || '',
      price: plan.price?.toString() || '',
      duration_days: plan.duration_days?.toString() || '30',
      features: plan.features?.join(', ') || '',
      max_clients: plan.max_clients?.toString() || '',
    });
    setShowEditDialog(true);
  };

  const handleEditPlan = async (e) => {
    e.preventDefault();
    
    if (!editPlan.name || !editPlan.price || !editPlan.duration_days) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      await axios.put(`${API}/admin/subscription-plans/${selectedPlan.id}`, {
        name: editPlan.name,
        price: parseFloat(editPlan.price),
        duration_days: parseInt(editPlan.duration_days),
        features: editPlan.features.split(',').map(f => f.trim()).filter(f => f),
        max_clients: editPlan.max_clients ? parseInt(editPlan.max_clients) : null,
      });
      
      toast.success('Plan updated successfully');
      setShowEditDialog(false);
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update plan');
    }
  };

  const openFeaturesDialog = (plan) => {
    setSelectedPlan(plan);
    // Initialize toggles from plan or defaults
    const toggles = plan.feature_toggles || {};
    const initialToggles = {};
    FEATURE_CONFIG.forEach(f => {
      initialToggles[f.key] = toggles[f.key] !== false; // Default to true if not set
    });
    setFeatureToggles(initialToggles);
    setShowFeaturesDialog(true);
  };

  const handleToggleFeature = (featureKey) => {
    setFeatureToggles(prev => ({
      ...prev,
      [featureKey]: !prev[featureKey]
    }));
  };

  const handleSaveFeatures = async () => {
    if (!selectedPlan) return;

    try {
      await axios.put(`${API}/admin/subscription-plans/${selectedPlan.id}/feature-toggles`, {
        feature_toggles: featureToggles
      });
      toast.success('Feature toggles updated');
      setShowFeaturesDialog(false);
      fetchPlans();
    } catch (error) {
      toast.error('Failed to update features');
    }
  };

  const countEnabledFeatures = (plan) => {
    if (!plan.feature_toggles) return FEATURE_CONFIG.length;
    return FEATURE_CONFIG.filter(f => plan.feature_toggles[f.key] !== false).length;
  };

  if (loading) {
    return <div className="text-center py-8">Loading subscription plans...</div>;
  }

  return (
    <div data-testid="subscription-management">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
        <div>
          <h2 className="text-3xl font-serif text-primary mb-2">Subscription Plans</h2>
          <p className="text-muted-foreground">Manage subscription plans and feature access</p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)} data-testid="create-plan-btn">
          <Plus size={20} className="mr-2" />
          New Plan
        </Button>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card key={plan.id} className="p-6 bg-white/70 backdrop-blur-xl border border-border/40" data-testid={`plan-${plan.id}`}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-semibold text-primary">{plan.name}</h3>
                <p className="text-2xl font-bold mt-1">
                  ₹{plan.price.toLocaleString('en-IN')}
                  <span className="text-sm font-normal text-muted-foreground">
                    /{plan.duration_days} days
                  </span>
                </p>
              </div>
              <CreditCard className="text-primary" size={24} />
            </div>

            {/* Feature Summary */}
            <div className="mb-4">
              <Badge variant="outline" className="mb-2">
                {countEnabledFeatures(plan)}/{FEATURE_CONFIG.length} Features Enabled
              </Badge>
              {plan.max_clients && (
                <p className="text-sm text-muted-foreground">
                  Max {plan.max_clients} clients
                </p>
              )}
            </div>

            {/* Quick Feature Preview */}
            <div className="flex flex-wrap gap-1 mb-4">
              {FEATURE_CONFIG.slice(0, 4).map((feature) => {
                const isEnabled = plan.feature_toggles?.[feature.key] !== false;
                const Icon = feature.icon;
                return (
                  <div
                    key={feature.key}
                    className={`p-1 rounded ${isEnabled ? 'text-success' : 'text-muted-foreground/30'}`}
                    title={`${feature.label}: ${isEnabled ? 'ON' : 'OFF'}`}
                  >
                    <Icon size={16} />
                  </div>
                );
              })}
              {FEATURE_CONFIG.length > 4 && (
                <span className="text-xs text-muted-foreground">+{FEATURE_CONFIG.length - 4} more</span>
              )}
            </div>

            {/* Plan Features List */}
            {plan.features && plan.features.length > 0 && (
              <ul className="text-sm text-muted-foreground mb-4 space-y-1">
                {plan.features.slice(0, 3).map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="w-1 h-1 bg-primary rounded-full" />
                    {feature}
                  </li>
                ))}
                {plan.features.length > 3 && (
                  <li className="text-xs">+{plan.features.length - 3} more features</li>
                )}
              </ul>
            )}

            {/* Actions */}
            <div className="flex gap-2 mt-4 pt-4 border-t border-border/40">
              <Button
                variant="outline"
                size="sm"
                onClick={() => openEditDialog(plan)}
                className="flex-1"
                data-testid={`edit-plan-${plan.id}`}
              >
                <Edit size={16} className="mr-1" />
                Edit
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => openFeaturesDialog(plan)}
                className="flex-1"
                data-testid={`manage-features-${plan.id}`}
              >
                <Settings size={16} className="mr-1" />
                Features
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDeletePlan(plan.id)}
                className="text-destructive hover:text-destructive"
                data-testid={`delete-plan-${plan.id}`}
              >
                <Trash2 size={16} />
              </Button>
            </div>
          </Card>
        ))}

        {plans.length === 0 && (
          <Card className="col-span-full p-12 text-center">
            <CreditCard className="mx-auto text-muted-foreground mb-4" size={48} />
            <p className="text-muted-foreground mb-4">No subscription plans created yet</p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus size={20} className="mr-2" />
              Create First Plan
            </Button>
          </Card>
        )}
      </div>

      {/* Create Plan Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent data-testid="create-plan-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Create Subscription Plan</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreatePlan} className="space-y-4">
            <div>
              <Label htmlFor="plan-name">Plan Name *</Label>
              <Input
                id="plan-name"
                data-testid="plan-name-input"
                value={newPlan.name}
                onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })}
                placeholder="e.g., Gold, Premium"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="plan-price">Price (₹) *</Label>
                <Input
                  id="plan-price"
                  type="number"
                  data-testid="plan-price-input"
                  value={newPlan.price}
                  onChange={(e) => setNewPlan({ ...newPlan, price: e.target.value })}
                  placeholder="1999"
                  required
                />
              </div>
              <div>
                <Label htmlFor="plan-duration">Duration (days) *</Label>
                <Input
                  id="plan-duration"
                  type="number"
                  data-testid="plan-duration-input"
                  value={newPlan.duration_days}
                  onChange={(e) => setNewPlan({ ...newPlan, duration_days: e.target.value })}
                  placeholder="30"
                  required
                />
              </div>
            </div>
            <div>
              <Label htmlFor="plan-max-clients">Max Clients (optional)</Label>
              <Input
                id="plan-max-clients"
                type="number"
                data-testid="plan-max-clients-input"
                value={newPlan.max_clients}
                onChange={(e) => setNewPlan({ ...newPlan, max_clients: e.target.value })}
                placeholder="Leave blank for unlimited"
              />
            </div>
            <div>
              <Label htmlFor="plan-features">Feature Descriptions (comma-separated)</Label>
              <Input
                id="plan-features"
                data-testid="plan-features-input"
                value={newPlan.features}
                onChange={(e) => setNewPlan({ ...newPlan, features: e.target.value })}
                placeholder="Unlimited clients, Priority support, TheraGenie features"
              />
            </div>
            <p className="text-sm text-muted-foreground">
              All features will be enabled by default. You can configure feature toggles after creating the plan.
            </p>
            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1" data-testid="save-plan-btn">
                Create Plan
              </Button>
              <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Plan Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent data-testid="edit-plan-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Edit Subscription Plan</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditPlan} className="space-y-4">
            <div>
              <Label htmlFor="edit-plan-name">Plan Name *</Label>
              <Input
                id="edit-plan-name"
                data-testid="edit-plan-name-input"
                value={editPlan.name}
                onChange={(e) => setEditPlan({ ...editPlan, name: e.target.value })}
                placeholder="e.g., Gold, Premium"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit-plan-price">Price (₹) *</Label>
                <Input
                  id="edit-plan-price"
                  type="number"
                  data-testid="edit-plan-price-input"
                  value={editPlan.price}
                  onChange={(e) => setEditPlan({ ...editPlan, price: e.target.value })}
                  placeholder="1999"
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit-plan-duration">Duration (days) *</Label>
                <Input
                  id="edit-plan-duration"
                  type="number"
                  data-testid="edit-plan-duration-input"
                  value={editPlan.duration_days}
                  onChange={(e) => setEditPlan({ ...editPlan, duration_days: e.target.value })}
                  placeholder="30"
                  required
                />
              </div>
            </div>
            <div>
              <Label htmlFor="edit-plan-max-clients">Max Clients (optional)</Label>
              <Input
                id="edit-plan-max-clients"
                type="number"
                data-testid="edit-plan-max-clients-input"
                value={editPlan.max_clients}
                onChange={(e) => setEditPlan({ ...editPlan, max_clients: e.target.value })}
                placeholder="Leave blank for unlimited"
              />
            </div>
            <div>
              <Label htmlFor="edit-plan-features">Feature Descriptions (comma-separated)</Label>
              <Input
                id="edit-plan-features"
                data-testid="edit-plan-features-input"
                value={editPlan.features}
                onChange={(e) => setEditPlan({ ...editPlan, features: e.target.value })}
                placeholder="Unlimited clients, Priority support, TheraGenie features"
              />
            </div>
            <p className="text-sm text-info bg-info/10 p-3 rounded-lg">
              Note: Changes to price and duration only affect new subscriptions. Existing therapist subscriptions remain unchanged.
            </p>
            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1" data-testid="update-plan-btn">
                Update Plan
              </Button>
              <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Feature Toggles Dialog */}
      <Dialog open={showFeaturesDialog} onOpenChange={setShowFeaturesDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] flex flex-col" data-testid="features-dialog">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="text-2xl font-serif text-primary">
              Feature Toggles - {selectedPlan?.name}
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto pr-2">
            <p className="text-sm text-muted-foreground mb-4">
              Control which features are available to therapists on this plan.
              Changes apply immediately to all therapists on this plan.
            </p>
            
            <div className="space-y-3">
              {FEATURE_CONFIG.map((feature) => {
                const Icon = feature.icon;
                const isEnabled = featureToggles[feature.key];
                return (
                  <div
                    key={feature.key}
                    className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                      isEnabled ? 'bg-success/5 border-success/20' : 'bg-muted/30 border-border'
                    }`}
                    data-testid={`feature-toggle-${feature.key}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${isEnabled ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground'}`}>
                        <Icon size={18} />
                      </div>
                      <div>
                        <p className="font-medium">{feature.label}</p>
                        <p className="text-xs text-muted-foreground">{feature.description}</p>
                      </div>
                    </div>
                    <Switch
                      checked={isEnabled}
                      onCheckedChange={() => handleToggleFeature(feature.key)}
                      data-testid={`switch-${feature.key}`}
                    />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex gap-3 pt-4 mt-4 border-t flex-shrink-0">
            <Button onClick={handleSaveFeatures} className="flex-1" data-testid="save-features-btn">
              Save Changes
            </Button>
            <Button variant="outline" onClick={() => setShowFeaturesDialog(false)}>
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SubscriptionManagement;
