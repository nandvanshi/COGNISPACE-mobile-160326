import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { 
  User, Building2, MapPin, Phone, Mail, Save, Loader2, 
  Search, CheckCircle, Shield, CreditCard, Camera, X,
  Clock, Plus, Trash2, Upload
} from 'lucide-react';
import { formatCurrency } from '../utils/formatUtils';

// Available specializations for therapists
const SPECIALIZATION_OPTIONS = [
  "Clinical Psychology",
  "Counseling Psychology", 
  "Child & Adolescent Therapy",
  "Marriage & Family Therapy",
  "Cognitive Behavioral Therapy (CBT)",
  "Dialectical Behavior Therapy (DBT)",
  "Trauma & PTSD",
  "Anxiety Disorders",
  "Depression",
  "Addiction & Substance Abuse",
  "Eating Disorders",
  "OCD & Related Disorders",
  "Grief & Loss Counseling",
  "Stress Management",
  "Anger Management",
  "Career Counseling",
  "Relationship Issues",
  "Self-Esteem & Confidence",
  "Mindfulness & Meditation",
  "Neuropsychology",
  "Psychoanalysis",
  "Art Therapy",
  "Play Therapy",
  "Group Therapy",
  "EMDR Therapy"
];

const TherapistProfileSettings = ({ isReadOnly = false }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pincodeLoading, setPincodeLoading] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [showSpecDropdown, setShowSpecDropdown] = useState(false);
  const fileInputRef = useRef(null);
  
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    mobile: '',
    profile_photo: '',
    clinic_name: '',
    specializations: [], // Array of selected specializations
    qualifications: '',
    experience_years: '',
    fee_slots: [], // Array of {amount, duration_minutes}
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
      
      // Parse specializations - could be string or array
      let specs = [];
      if (response.data.specializations) {
        specs = Array.isArray(response.data.specializations) 
          ? response.data.specializations 
          : response.data.specializations.split(',').map(s => s.trim()).filter(Boolean);
      } else if (response.data.specialization) {
        specs = response.data.specialization.split(',').map(s => s.trim()).filter(Boolean);
      }
      
      // Parse fee_slots - could be array or single value
      let feeSlots = [];
      if (response.data.fee_slots && Array.isArray(response.data.fee_slots)) {
        feeSlots = response.data.fee_slots;
      } else if (response.data.consultation_fee) {
        feeSlots = [{ amount: response.data.consultation_fee, duration_minutes: 50 }];
      }
      
      setFormData({
        full_name: response.data.full_name || '',
        email: response.data.email || '',
        mobile: response.data.mobile || '',
        profile_photo: response.data.profile_photo || '',
        clinic_name: response.data.clinic_name || '',
        specializations: specs,
        qualifications: response.data.qualifications || '',
        experience_years: response.data.experience_years || '',
        fee_slots: feeSlots.length > 0 ? feeSlots : [{ amount: '', duration_minutes: 50 }],
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
    
    if (value.length === 6) {
      lookupPincode(value);
    }
  };

  // Image compression and upload
  const compressImage = (file, maxWidth = 400, quality = 0.8) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;
          
          // Calculate new dimensions
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
          
          canvas.width = width;
          canvas.height = height;
          
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);
          
          // Convert to base64
          const compressedBase64 = canvas.toDataURL('image/jpeg', quality);
          resolve(compressedBase64);
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }
    
    // Validate file size (max 5MB before compression)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image size should be less than 5MB');
      return;
    }
    
    setUploadingPhoto(true);
    try {
      // Compress image
      const compressedBase64 = await compressImage(file, 400, 0.8);
      
      // Update form data with base64 image
      setFormData(prev => ({ ...prev, profile_photo: compressedBase64 }));
      toast.success('Photo uploaded successfully');
    } catch (error) {
      toast.error('Failed to process image');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const removePhoto = () => {
    setFormData(prev => ({ ...prev, profile_photo: '' }));
  };

  // Specialization handlers
  const toggleSpecialization = (spec) => {
    setFormData(prev => {
      const current = prev.specializations;
      if (current.includes(spec)) {
        return { ...prev, specializations: current.filter(s => s !== spec) };
      } else if (current.length < 5) {
        return { ...prev, specializations: [...current, spec] };
      } else {
        toast.error('Maximum 5 specializations allowed');
        return prev;
      }
    });
  };

  const removeSpecialization = (spec) => {
    setFormData(prev => ({
      ...prev,
      specializations: prev.specializations.filter(s => s !== spec)
    }));
  };

  // Fee slot handlers
  const addFeeSlot = () => {
    if (formData.fee_slots.length >= 5) {
      toast.error('Maximum 5 fee options allowed');
      return;
    }
    setFormData(prev => ({
      ...prev,
      fee_slots: [...prev.fee_slots, { amount: '', duration_minutes: 30 }]
    }));
  };

  const updateFeeSlot = (index, field, value) => {
    setFormData(prev => {
      const newSlots = [...prev.fee_slots];
      newSlots[index] = { ...newSlots[index], [field]: value };
      return { ...prev, fee_slots: newSlots };
    });
  };

  const removeFeeSlot = (index) => {
    if (formData.fee_slots.length <= 1) {
      toast.error('At least one fee option is required');
      return;
    }
    setFormData(prev => ({
      ...prev,
      fee_slots: prev.fee_slots.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isReadOnly) return;
    
    // Validation
    if (formData.specializations.length === 0) {
      toast.error('Please select at least 1 specialization');
      return;
    }
    
    const validFeeSlots = formData.fee_slots.filter(slot => slot.amount && slot.duration_minutes);
    if (validFeeSlots.length === 0) {
      toast.error('Please add at least one consultation fee option');
      return;
    }
    
    setSaving(true);
    try {
      const updateData = {
        ...formData,
        specializations: formData.specializations,
        fee_slots: validFeeSlots.map(slot => ({
          amount: parseFloat(slot.amount),
          duration_minutes: parseInt(slot.duration_minutes)
        })),
        experience_years: formData.experience_years ? parseInt(formData.experience_years) : null
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
        {/* Profile Photo & Basic Info */}
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-2 mb-6">
            <User className="text-primary" size={20} />
            <h3 className="text-xl font-serif text-primary">Basic Information</h3>
          </div>

          <div className="flex flex-col md:flex-row gap-6">
            {/* Profile Photo Upload */}
            <div className="flex flex-col items-center gap-3">
              <div className="relative w-32 h-32 rounded-full bg-primary/10 overflow-hidden border-4 border-white shadow-lg">
                {formData.profile_photo ? (
                  <img 
                    src={formData.profile_photo} 
                    alt="Profile" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Camera size={32} className="text-primary/50" />
                  </div>
                )}
                
                {uploadingPhoto && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <Loader2 className="animate-spin text-white" size={24} />
                  </div>
                )}
              </div>
              
              {!isReadOnly && (
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handlePhotoUpload}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadingPhoto}
                  >
                    <Upload size={14} className="mr-1" />
                    Upload
                  </Button>
                  {formData.profile_photo && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={removePhoto}
                      className="text-destructive"
                    >
                      <Trash2 size={14} />
                    </Button>
                  )}
                </div>
              )}
              <p className="text-xs text-muted-foreground text-center">
                Max 5MB, auto-compressed
              </p>
            </div>

            {/* Basic Fields */}
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
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
            </div>
          </div>
        </Card>

        {/* Qualifications & Specializations */}
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-2 mb-6">
            <Building2 className="text-primary" size={20} />
            <h3 className="text-xl font-serif text-primary">Professional Details</h3>
          </div>

          <div className="space-y-6">
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
              <Label htmlFor="qualifications">Qualifications *</Label>
              <Input
                id="qualifications"
                value={formData.qualifications}
                onChange={(e) => setFormData({ ...formData, qualifications: e.target.value })}
                placeholder="M.Phil Clinical Psychology, RCI Licensed, Ph.D."
                disabled={isReadOnly}
                data-testid="profile-qualifications"
              />
              <p className="text-xs text-muted-foreground mt-1">Your degrees, certifications, and licenses</p>
            </div>

            {/* Specializations Multi-Select */}
            <div>
              <Label>Specializations * <span className="text-muted-foreground font-normal">(Select 1-5)</span></Label>
              
              {/* Selected Specializations */}
              <div className="flex flex-wrap gap-2 mt-2 mb-3 min-h-[32px]">
                {formData.specializations.map((spec, idx) => (
                  <Badge 
                    key={idx} 
                    variant="secondary" 
                    className="px-3 py-1.5 bg-primary/10 text-primary"
                  >
                    {spec}
                    {!isReadOnly && (
                      <button
                        type="button"
                        onClick={() => removeSpecialization(spec)}
                        className="ml-2 hover:text-destructive"
                      >
                        <X size={14} />
                      </button>
                    )}
                  </Badge>
                ))}
                {formData.specializations.length === 0 && (
                  <span className="text-sm text-muted-foreground">No specializations selected</span>
                )}
              </div>
              
              {/* Dropdown */}
              {!isReadOnly && (
                <div className="relative">
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-between"
                    onClick={() => setShowSpecDropdown(!showSpecDropdown)}
                    data-testid="specialization-dropdown"
                  >
                    <span>Select Specializations ({formData.specializations.length}/5)</span>
                    <Plus size={16} />
                  </Button>
                  
                  {showSpecDropdown && (
                    <>
                      <div 
                        className="fixed inset-0 z-[99]" 
                        onClick={() => setShowSpecDropdown(false)}
                      />
                      <div 
                        className="absolute left-0 right-0 z-[100] mt-1 bg-white border-2 border-primary/20 rounded-lg shadow-2xl"
                      >
                        <div className="overflow-y-auto" style={{ maxHeight: '240px' }}>
                          {SPECIALIZATION_OPTIONS.map((spec, idx) => (
                            <button
                              key={idx}
                              type="button"
                              className={`w-full text-left px-4 py-3 text-sm hover:bg-primary/5 flex items-center justify-between border-b border-gray-100 last:border-0 ${
                                formData.specializations.includes(spec) ? 'bg-primary/10 text-primary font-medium' : ''
                              }`}
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleSpecialization(spec);
                              }}
                            >
                              <span>{spec}</span>
                              {formData.specializations.includes(spec) && (
                                <CheckCircle size={16} className="text-primary flex-shrink-0" />
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Consultation Fees */}
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <CreditCard className="text-primary" size={20} />
              <h3 className="text-xl font-serif text-primary">Consultation Fees</h3>
            </div>
            {!isReadOnly && formData.fee_slots.length < 5 && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addFeeSlot}
                data-testid="add-fee-slot"
              >
                <Plus size={16} className="mr-1" />
                Add Option
              </Button>
            )}
          </div>

          <p className="text-sm text-muted-foreground mb-4">
            Add different consultation options with varying durations and fees
          </p>

          <div className="space-y-4">
            {formData.fee_slots.map((slot, index) => (
              <div key={index} className="flex items-center gap-4 p-4 bg-surface rounded-lg">
                <div className="flex-1 grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs">Amount (₹)</Label>
                    <Input
                      type="number"
                      min="0"
                      value={slot.amount}
                      onChange={(e) => updateFeeSlot(index, 'amount', e.target.value)}
                      placeholder="1500"
                      disabled={isReadOnly}
                      data-testid={`fee-amount-${index}`}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Duration (minutes)</Label>
                    <select
                      value={slot.duration_minutes}
                      onChange={(e) => updateFeeSlot(index, 'duration_minutes', e.target.value)}
                      disabled={isReadOnly}
                      className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                      data-testid={`fee-duration-${index}`}
                    >
                      <option value="15">15 min</option>
                      <option value="20">20 min</option>
                      <option value="30">30 min</option>
                      <option value="40">40 min</option>
                      <option value="45">45 min</option>
                      <option value="50">50 min</option>
                      <option value="60">60 min</option>
                      <option value="90">90 min</option>
                      <option value="120">120 min</option>
                    </select>
                  </div>
                </div>
                
                <div className="text-right min-w-[120px]">
                  <p className="font-semibold text-primary">
                    {slot.amount ? `₹${slot.amount}` : '—'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    for {slot.duration_minutes} min
                  </p>
                </div>
                
                {!isReadOnly && formData.fee_slots.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFeeSlot(index)}
                    className="text-destructive"
                  >
                    <Trash2 size={16} />
                  </Button>
                )}
              </div>
            ))}
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
