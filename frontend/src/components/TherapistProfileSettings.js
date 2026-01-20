import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { toast } from 'sonner';
import { 
  User, Building2, MapPin, Phone, Mail, Save, Loader2, 
  Search, CheckCircle, Shield, CreditCard, GraduationCap,
  Clock, BadgeIndianRupee
} from 'lucide-react';
import { formatCurrency } from '../utils/formatUtils';

const TherapistProfileSettings = ({ isReadOnly = false }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pincodeLoading, setPincodeLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    mobile: '',
    profile_photo: '',
    clinic_name: '',
    specialization: '',
    qualifications: '',
    experience_years: '',
    consultation_fee: '',
    address_line_1: '',
    address_line_2: '',
    pincode: '',
    city: '',
    state: '',
    district: '',
    show_mobile_on_receipt: true,
    show_email_on_receipt: true
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/therapist/profile`);
      setProfile(response.data);
      setFormData({
        full_name: response.data.full_name || '',
        email: response.data.email || '',
        mobile: response.data.mobile || '',
        profile_photo: response.data.profile_photo || '',
        clinic_name: response.data.clinic_name || '',
        specialization: response.data.specialization || '',
        qualifications: response.data.qualifications || '',
        experience_years: response.data.experience_years || '',
        consultation_fee: response.data.consultation_fee || '',
        address_line_1: response.data.address_line_1 || '',
        address_line_2: response.data.address_line_2 || '',
        pincode: response.data.pincode || '',
        city: response.data.city || '',
        state: response.data.state || '',
        district: response.data.district || '',
        show_mobile_on_receipt: response.data.show_mobile_on_receipt ?? true,
        show_email_on_receipt: response.data.show_email_on_receipt ?? true
      });
    } catch (error) {
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const lookupPincode = useCallback(async (pincode) => {
    if (!pincode || pincode.length !== 6) return;
    
    setPincodeLoading(true);
    try {
      const response = await axios.get(`${API}/therapist/pincode/${pincode}`);
      setFormData(prev => ({
        ...prev,
        city: response.data.city,
        state: response.data.state,
        district: response.data.district
      }));
      toast.success('Address auto-filled from pincode');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Pincode not found');
    } finally {
      setPincodeLoading(false);
    }
  }, []);

  const handlePincodeChange = (e) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setFormData(prev => ({ ...prev, pincode: value }));
    
    // Auto-lookup when 6 digits entered
    if (value.length === 6) {
      lookupPincode(value);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isReadOnly) return;
    
    setSaving(true);
    try {
      const updateData = {
        ...formData,
        experience_years: formData.experience_years ? parseInt(formData.experience_years) : null,
        consultation_fee: formData.consultation_fee ? parseFloat(formData.consultation_fee) : null
      };
      
      await axios.put(`${API}/therapist/profile`, updateData);
      toast.success('Profile updated successfully');
      await fetchProfile();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  return (
    <div data-testid="therapist-profile-settings">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-4xl font-serif text-primary mb-2">Profile Settings</h2>
        <p className="text-muted-foreground">Manage your professional profile and clinic details</p>
      </div>

      {isReadOnly && (
        <Card className="p-4 mb-6 bg-warning/10 border-warning/30">
          <p className="text-sm text-warning-foreground">
            <strong>Read-only mode:</strong> Your subscription has expired. You can view but not edit your profile.
          </p>
        </Card>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-2 mb-6">
            <User className="text-primary" size={20} />
            <h3 className="text-xl font-serif text-primary">Basic Information</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="full_name">Full Name *</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="Dr. Your Name"
                disabled={isReadOnly}
                data-testid="profile-full-name"
              />
            </div>

            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="doctor@clinic.com"
                disabled={isReadOnly}
                data-testid="profile-email"
              />
            </div>

            <div>
              <Label htmlFor="mobile">Mobile Number</Label>
              <Input
                id="mobile"
                value={formData.mobile}
                onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                placeholder="9999999999"
                disabled={isReadOnly}
                data-testid="profile-mobile"
              />
            </div>

            <div>
              <Label htmlFor="profile_photo">Profile Photo URL</Label>
              <Input
                id="profile_photo"
                value={formData.profile_photo}
                onChange={(e) => setFormData({ ...formData, profile_photo: e.target.value })}
                placeholder="https://example.com/photo.jpg"
                disabled={isReadOnly}
              />
            </div>
          </div>
        </Card>

        {/* Clinic Information */}
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-2 mb-6">
            <Building2 className="text-primary" size={20} />
            <h3 className="text-xl font-serif text-primary">Clinic Information</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="clinic_name">Clinic/Practice Name</Label>
              <Input
                id="clinic_name"
                value={formData.clinic_name}
                onChange={(e) => setFormData({ ...formData, clinic_name: e.target.value })}
                placeholder="Mind Wellness Clinic"
                disabled={isReadOnly}
                data-testid="profile-clinic-name"
              />
            </div>

            <div>
              <Label htmlFor="specialization">Specialization</Label>
              <Input
                id="specialization"
                value={formData.specialization}
                onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                placeholder="Clinical Psychology, CBT"
                disabled={isReadOnly}
              />
            </div>

            <div className="md:col-span-2">
              <Label htmlFor="qualifications">Qualifications</Label>
              <Input
                id="qualifications"
                value={formData.qualifications}
                onChange={(e) => setFormData({ ...formData, qualifications: e.target.value })}
                placeholder="M.Phil Clinical Psychology, RCI Licensed"
                disabled={isReadOnly}
                data-testid="profile-qualifications"
              />
            </div>

            <div>
              <Label htmlFor="experience_years">Years of Experience</Label>
              <Input
                id="experience_years"
                type="number"
                min="0"
                value={formData.experience_years}
                onChange={(e) => setFormData({ ...formData, experience_years: e.target.value })}
                placeholder="5"
                disabled={isReadOnly}
              />
            </div>

            <div>
              <Label htmlFor="consultation_fee">Consultation Fee (₹)</Label>
              <Input
                id="consultation_fee"
                type="number"
                min="0"
                value={formData.consultation_fee}
                onChange={(e) => setFormData({ ...formData, consultation_fee: e.target.value })}
                placeholder="1500"
                disabled={isReadOnly}
                data-testid="profile-consultation-fee"
              />
            </div>
          </div>
        </Card>

        {/* Address - Indian Format */}
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-2 mb-6">
            <MapPin className="text-primary" size={20} />
            <h3 className="text-xl font-serif text-primary">Clinic Address</h3>
            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full ml-2">Indian Format</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2">
              <Label htmlFor="address_line_1">Address Line 1</Label>
              <Input
                id="address_line_1"
                value={formData.address_line_1}
                onChange={(e) => setFormData({ ...formData, address_line_1: e.target.value })}
                placeholder="Building/House No., Street Name"
                disabled={isReadOnly}
                data-testid="profile-address-line-1"
              />
            </div>

            <div className="md:col-span-2">
              <Label htmlFor="address_line_2">Address Line 2</Label>
              <Input
                id="address_line_2"
                value={formData.address_line_2}
                onChange={(e) => setFormData({ ...formData, address_line_2: e.target.value })}
                placeholder="Locality, Area, Landmark"
                disabled={isReadOnly}
              />
            </div>

            <div>
              <Label htmlFor="pincode">PIN Code</Label>
              <div className="relative">
                <Input
                  id="pincode"
                  value={formData.pincode}
                  onChange={handlePincodeChange}
                  placeholder="110001"
                  maxLength={6}
                  disabled={isReadOnly}
                  className="pr-10"
                  data-testid="profile-pincode"
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {pincodeLoading ? (
                    <Loader2 size={16} className="animate-spin text-primary" />
                  ) : formData.city && formData.pincode.length === 6 ? (
                    <CheckCircle size={16} className="text-green-500" />
                  ) : (
                    <Search size={16} className="text-muted-foreground" />
                  )}
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-1">Enter 6-digit PIN to auto-fill city & state</p>
            </div>

            <div>
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                placeholder="Auto-filled from PIN"
                disabled={isReadOnly}
                data-testid="profile-city"
              />
            </div>

            <div>
              <Label htmlFor="district">District</Label>
              <Input
                id="district"
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                placeholder="Auto-filled from PIN"
                disabled={isReadOnly}
              />
            </div>

            <div>
              <Label htmlFor="state">State</Label>
              <Input
                id="state"
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                placeholder="Auto-filled from PIN"
                disabled={isReadOnly}
                data-testid="profile-state"
              />
            </div>
          </div>
        </Card>

        {/* Privacy Settings */}
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-2 mb-6">
            <Shield className="text-primary" size={20} />
            <h3 className="text-xl font-serif text-primary">Receipt Privacy Settings</h3>
          </div>

          <p className="text-sm text-muted-foreground mb-6">
            Choose what contact information appears on payment receipts generated for clients.
          </p>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-surface rounded-lg">
              <div className="flex items-center gap-3">
                <Phone size={18} className="text-primary" />
                <div>
                  <p className="font-medium">Show Mobile Number</p>
                  <p className="text-sm text-muted-foreground">Display your mobile on receipts</p>
                </div>
              </div>
              <Switch
                checked={formData.show_mobile_on_receipt}
                onCheckedChange={(checked) => setFormData({ ...formData, show_mobile_on_receipt: checked })}
                disabled={isReadOnly}
                data-testid="profile-show-mobile-switch"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-surface rounded-lg">
              <div className="flex items-center gap-3">
                <Mail size={18} className="text-primary" />
                <div>
                  <p className="font-medium">Show Email Address</p>
                  <p className="text-sm text-muted-foreground">Display your email on receipts</p>
                </div>
              </div>
              <Switch
                checked={formData.show_email_on_receipt}
                onCheckedChange={(checked) => setFormData({ ...formData, show_email_on_receipt: checked })}
                disabled={isReadOnly}
                data-testid="profile-show-email-switch"
              />
            </div>
          </div>
        </Card>

        {/* Subscription Info (Read-only) */}
        {profile && (
          <Card className="p-6 bg-surface/50 border border-border/40">
            <div className="flex items-center gap-2 mb-4">
              <CreditCard className="text-primary" size={20} />
              <h3 className="text-lg font-medium">Subscription Status</h3>
            </div>
            <div className="flex items-center gap-4">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                profile.subscription_status === 'active' ? 'bg-green-100 text-green-700' :
                profile.subscription_status === 'trial' ? 'bg-blue-100 text-blue-700' :
                'bg-red-100 text-red-700'
              }`}>
                {profile.subscription_status?.toUpperCase() || 'N/A'}
              </span>
              <span className="text-muted-foreground">Plan: {profile.subscription_plan || 'N/A'}</span>
            </div>
          </Card>
        )}

        {/* Save Button */}
        {!isReadOnly && (
          <div className="flex justify-end">
            <Button
              type="submit"
              disabled={saving}
              className="bg-primary hover:bg-primary-700 rounded-full px-8"
              data-testid="profile-save-button"
            >
              {saving ? (
                <>
                  <Loader2 size={16} className="mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={16} className="mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        )}
      </form>
    </div>
  );
};

export default TherapistProfileSettings;
