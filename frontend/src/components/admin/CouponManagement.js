import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { toast } from 'sonner';
import { Plus, Trash2, Tag, Copy } from 'lucide-react';

const CouponManagement = () => {
  const [coupons, setCoupons] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newCoupon, setNewCoupon] = useState({
    code: '',
    discount_percent: '',
    valid_until: '',
    max_uses: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCoupons();
  }, []);

  const fetchCoupons = async () => {
    try {
      const response = await axios.get(`${API}/api/admin/coupons`);
      setCoupons(response.data);
    } catch (error) {
      toast.error('Failed to load coupons');
    } finally {
      setLoading(false);
    }
  };

  const generateRandomCode = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 8; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
  };

  const handleCreateCoupon = async (e) => {
    e.preventDefault();

    try {
      const payload = {
        code: newCoupon.code.toUpperCase(),
        discount_percent: parseFloat(newCoupon.discount_percent),
        valid_until: new Date(newCoupon.valid_until).toISOString(),
        max_uses: newCoupon.max_uses ? parseInt(newCoupon.max_uses) : null,
      };

      await axios.post(`${API}/api/admin/coupons`, payload);
      toast.success('Coupon created');
      setShowCreateDialog(false);
      setNewCoupon({
        code: '',
        discount_percent: '',
        valid_until: '',
        max_uses: '',
      });
      fetchCoupons();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create coupon');
    }
  };

  const handleDeleteCoupon = async (couponId) => {
    if (!window.confirm('Are you sure you want to delete this coupon?')) return;

    try {
      await axios.delete(`${API}/api/admin/coupons/${couponId}`);
      toast.success('Coupon deleted');
      fetchCoupons();
    } catch (error) {
      toast.error('Failed to delete coupon');
    }
  };

  const copyToClipboard = (code) => {
    navigator.clipboard.writeText(code);
    toast.success('Code copied to clipboard');
  };

  const isExpired = (validUntil) => {
    return new Date(validUntil) < new Date();
  };

  if (loading) {
    return <div className="text-center py-12">Loading coupons...</div>;
  }

  return (
    <div data-testid="coupon-management">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Coupon Codes</h2>
          <p className="text-muted-foreground">Create and manage promotional discount codes</p>
        </div>
        <Button
          onClick={() => setShowCreateDialog(true)}
          className="bg-primary hover:bg-primary-700 rounded-full"
          data-testid="create-coupon-button"
        >
          <Plus size={20} className="mr-2" />
          Create Coupon
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {coupons.map((coupon) => (
          <Card
            key={coupon.id}
            className={`p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl ${
              isExpired(coupon.valid_until) ? 'opacity-50' : ''
            }`}
            data-testid={`coupon-${coupon.id}`}
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-2">
                <Tag className="text-primary" size={20} />
                <h3 className="text-xl font-bold text-primary font-mono">{coupon.code}</h3>
              </div>
              <div className="flex gap-1">
                <Button
                  onClick={() => copyToClipboard(coupon.code)}
                  variant="ghost"
                  size="sm"
                  data-testid={`copy-${coupon.id}`}
                >
                  <Copy size={16} />
                </Button>
                <Button
                  onClick={() => handleDeleteCoupon(coupon.id)}
                  variant="ghost"
                  size="sm"
                  data-testid={`delete-coupon-${coupon.id}`}
                >
                  <Trash2 size={16} className="text-error" />
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-2xl font-bold text-success">{coupon.discount_percent}% OFF</p>
              <p className="text-sm text-muted-foreground">
                Valid until: {new Date(coupon.valid_until).toLocaleDateString()}
              </p>
              <p className="text-sm text-muted-foreground">
                Used: {coupon.used_count}
                {coupon.max_uses ? ` / ${coupon.max_uses}` : ' / Unlimited'}
              </p>
              {isExpired(coupon.valid_until) && (
                <span className="inline-block px-2 py-1 bg-error/10 text-error text-xs rounded-full">
                  Expired
                </span>
              )}
            </div>
          </Card>
        ))}

        {coupons.length === 0 && (
          <div className="col-span-3 text-center py-12">
            <p className="text-muted-foreground">No coupons created yet</p>
          </div>
        )}
      </div>

      {/* Create Coupon Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent data-testid="create-coupon-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Create Coupon Code</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateCoupon} className="space-y-4">
            <div>
              <Label htmlFor="coupon-code">Coupon Code *</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="coupon-code"
                  data-testid="coupon-code-input"
                  value={newCoupon.code}
                  onChange={(e) => setNewCoupon({ ...newCoupon, code: e.target.value.toUpperCase() })}
                  required
                  className="flex-1"
                  placeholder="SUMMER2024"
                  maxLength={20}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setNewCoupon({ ...newCoupon, code: generateRandomCode() })}
                  data-testid="generate-code-button"
                >
                  Generate
                </Button>
              </div>
            </div>

            <div>
              <Label htmlFor="discount">Discount Percentage *</Label>
              <Input
                id="discount"
                type="number"
                step="0.01"
                min="0"
                max="100"
                data-testid="discount-input"
                value={newCoupon.discount_percent}
                onChange={(e) => setNewCoupon({ ...newCoupon, discount_percent: e.target.value })}
                required
                className="mt-1"
                placeholder="e.g., 20 for 20% off"
              />
            </div>

            <div>
              <Label htmlFor="valid-until">Valid Until *</Label>
              <Input
                id="valid-until"
                type="datetime-local"
                data-testid="valid-until-input"
                value={newCoupon.valid_until}
                onChange={(e) => setNewCoupon({ ...newCoupon, valid_until: e.target.value })}
                required
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="max-uses">Max Uses (Optional)</Label>
              <Input
                id="max-uses"
                type="number"
                data-testid="max-uses-input"
                value={newCoupon.max_uses}
                onChange={(e) => setNewCoupon({ ...newCoupon, max_uses: e.target.value })}
                className="mt-1"
                placeholder="Leave empty for unlimited uses"
              />
            </div>

            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="save-coupon-button">
                Create Coupon
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                data-testid="cancel-coupon-button"
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

export default CouponManagement;
