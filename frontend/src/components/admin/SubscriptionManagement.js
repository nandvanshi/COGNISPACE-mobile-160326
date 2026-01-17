import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Plus, Trash2, DollarSign } from 'lucide-react';

const SubscriptionManagement = () => {
  const [plans, setPlans] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newPlan, setNewPlan] = useState({
    name: '',
    price: '',
    duration_days: '',
    features: [''],
    max_clients: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/admin/subscription-plans`);
      setPlans(response.data);
    } catch (error) {
      toast.error('Failed to load subscription plans');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async (e) => {
    e.preventDefault();

    try {
      const payload = {
        name: newPlan.name,
        price: parseFloat(newPlan.price),
        duration_days: parseInt(newPlan.duration_days),
        features: newPlan.features.filter((f) => f.trim() !== ''),
        max_clients: newPlan.max_clients ? parseInt(newPlan.max_clients) : null,
      };

      await axios.post(`${API}/admin/subscription-plans`, payload);
      toast.success('Subscription plan created');
      setShowCreateDialog(false);
      setNewPlan({
        name: '',
        price: '',
        duration_days: '',
        features: [''],
        max_clients: '',
      });
      fetchPlans();
    } catch (error) {
      toast.error('Failed to create plan');
    }
  };

  const handleDeletePlan = async (planId) => {
    if (!window.confirm('Are you sure you want to delete this plan?')) return;

    try {
      await axios.delete(`${API}/admin/subscription-plans/${planId}`);
      toast.success('Plan deleted');
      fetchPlans();
    } catch (error) {
      toast.error('Failed to delete plan');
    }
  };

  const addFeature = () => {
    setNewPlan({ ...newPlan, features: [...newPlan.features, ''] });
  };

  const updateFeature = (index, value) => {
    const updatedFeatures = [...newPlan.features];
    updatedFeatures[index] = value;
    setNewPlan({ ...newPlan, features: updatedFeatures });
  };

  const removeFeature = (index) => {
    setNewPlan({ ...newPlan, features: newPlan.features.filter((_, i) => i !== index) });
  };

  if (loading) {
    return <div className="text-center py-12">Loading plans...</div>;
  }

  return (
    <div data-testid="subscription-management">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Subscription Plans</h2>
          <p className="text-muted-foreground">Manage subscription plans for therapists</p>
        </div>
        <Button
          onClick={() => setShowCreateDialog(true)}
          className="bg-primary hover:bg-primary-700 rounded-full"
          data-testid="create-plan-button"
        >
          <Plus size={20} className="mr-2" />
          Create Plan
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card
            key={plan.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
            data-testid={`plan-${plan.id}`}
          >
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-2xl font-serif text-primary">{plan.name}</h3>
              <Button
                onClick={() => handleDeletePlan(plan.id)}
                variant="ghost"
                size="sm"
                data-testid={`delete-plan-${plan.id}`}
              >
                <Trash2 size={16} className="text-error" />
              </Button>
            </div>
            <div className="mb-4">
              <p className="text-3xl font-bold text-foreground">
                ${plan.price}
                <span className="text-sm text-muted-foreground font-normal">/{plan.duration_days} days</span>
              </p>
            </div>
            <div className="space-y-2 mb-4">
              {plan.features.map((feature, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-success mt-1">✓</span>
                  <p className="text-sm text-foreground">{feature}</p>
                </div>
              ))}
            </div>
            {plan.max_clients && (
              <p className="text-xs text-muted-foreground">Max {plan.max_clients} clients</p>
            )}
          </Card>
        ))}

        {plans.length === 0 && (
          <div className="col-span-3 text-center py-12">
            <p className="text-muted-foreground">No subscription plans yet</p>
          </div>
        )}
      </div>

      {/* Create Plan Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl" data-testid="create-plan-dialog">
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
                required
                className="mt-1"
                placeholder="e.g., Basic, Professional, Enterprise"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="plan-price">Price ($) *</Label>
                <Input
                  id="plan-price"
                  type="number"
                  step="0.01"
                  data-testid="plan-price-input"
                  value={newPlan.price}
                  onChange={(e) => setNewPlan({ ...newPlan, price: e.target.value })}
                  required
                  className="mt-1"
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
                  required
                  className="mt-1"
                  placeholder="e.g., 30, 90, 365"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="max-clients">Max Clients (Optional)</Label>
              <Input
                id="max-clients"
                type="number"
                data-testid="max-clients-input"
                value={newPlan.max_clients}
                onChange={(e) => setNewPlan({ ...newPlan, max_clients: e.target.value })}
                className="mt-1"
                placeholder="Leave empty for unlimited"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <Label>Features *</Label>
                <Button type="button" onClick={addFeature} size="sm" data-testid="add-feature-button">
                  <Plus size={16} className="mr-1" />
                  Add Feature
                </Button>
              </div>
              {newPlan.features.map((feature, idx) => (
                <div key={idx} className="flex gap-2 mb-2">
                  <Input
                    value={feature}
                    onChange={(e) => updateFeature(idx, e.target.value)}
                    placeholder="Feature description"
                    data-testid={`feature-input-${idx}`}
                  />
                  {newPlan.features.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeFeature(idx)}
                      data-testid={`remove-feature-${idx}`}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="save-plan-button">
                Create Plan
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                data-testid="cancel-plan-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SubscriptionManagement;
