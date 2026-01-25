import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { 
  User, Phone, Mail, Lock, MapPin, Heart, 
  AlertCircle, CheckCircle, Loader2, Shield,
  UserPlus, ArrowRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ClientRegisterPage = () => {
  const { therapistCode } = useParams();
  const navigate = useNavigate();
  
  const [verifying, setVerifying] = useState(true);
  const [therapistInfo, setTherapistInfo] = useState(null);
  const [invalidLink, setInvalidLink] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [registeredClientId, setRegisteredClientId] = useState('');
  
  const [formData, setFormData] = useState({
    full_name: '',
    mobile: '',
    email: '',
    password: '',
    confirm_password: '',
    age: '',
    guardian_name: '',
    address: '',
    referred_by: '',
    emergency_contact_name: '',
    emergency_contact_phone: ''
  });
  
  const [errors, setErrors] = useState({});

  useEffect(() => {
    verifyCode();
  }, [therapistCode]);

  const verifyCode = async () => {
    try {
      const response = await axios.get(`${API}/auth/verify-registration-code/${therapistCode}`);
      setTherapistInfo(response.data);
      setInvalidLink(false);
    } catch (error) {
      setInvalidLink(true);
      toast.error(error.response?.data?.detail || 'Invalid registration link');
    } finally {
      setVerifying(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Name is required';
    }
    
    if (!formData.mobile.trim()) {
      newErrors.mobile = 'Mobile number is required';
    } else if (!/^\d{10}$/.test(formData.mobile)) {
      newErrors.mobile = 'Mobile must be exactly 10 digits';
    }
    
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }
    
    if (formData.emergency_contact_phone && !/^\d{10}$/.test(formData.emergency_contact_phone)) {
      newErrors.emergency_contact_phone = 'Must be 10 digits';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors in the form');
      return;
    }
    
    setSubmitting(true);
    try {
      const payload = {
        full_name: formData.full_name.trim(),
        mobile: formData.mobile.trim(),
        password: formData.password,
        email: formData.email.trim() || null,
        age: formData.age ? parseInt(formData.age) : null,
        guardian_name: formData.guardian_name.trim() || null,
        address: formData.address.trim() || null,
        referred_by: formData.referred_by.trim() || null,
        emergency_contact_name: formData.emergency_contact_name.trim() || null,
        emergency_contact_phone: formData.emergency_contact_phone.trim() || null
      };
      
      const response = await axios.post(`${API}/auth/client-self-register/${therapistCode}`, payload);
      
      setSuccess(true);
      setRegisteredClientId(response.data.client_id);
      toast.success('Registration successful!');
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state
  if (verifying) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50 flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-white rounded-3xl shadow-lg border-0 max-w-md w-full">
          <Loader2 className="animate-spin h-12 w-12 text-emerald-600 mx-auto mb-4" />
          <p className="text-gray-600">Verifying registration link...</p>
        </Card>
      </div>
    );
  }

  // Invalid link
  if (invalidLink) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50 flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-white rounded-3xl shadow-lg border-0 max-w-md w-full">
          <div className="w-16 h-16 mx-auto bg-red-100 rounded-full flex items-center justify-center mb-6">
            <AlertCircle className="text-red-600" size={32} />
          </div>
          <h2 className="text-2xl font-serif text-gray-800 mb-4">Invalid Link</h2>
          <p className="text-gray-600 mb-6">
            This registration link is invalid or has expired. 
            Please contact your therapist for a new link.
          </p>
          <Button onClick={() => navigate('/login')} variant="outline" className="rounded-xl">
            Go to Login
          </Button>
        </Card>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50 flex items-center justify-center p-4">
        <Card className="p-8 text-center bg-white rounded-3xl shadow-lg border-0 max-w-md w-full">
          <div className="w-16 h-16 mx-auto bg-emerald-100 rounded-full flex items-center justify-center mb-6">
            <CheckCircle className="text-emerald-600" size={32} />
          </div>
          <h2 className="text-2xl font-serif text-emerald-800 mb-4">Registration Successful!</h2>
          <p className="text-gray-600 mb-2">
            Welcome! Your account has been created.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Your Client ID: <span className="font-mono font-semibold text-emerald-700">{registeredClientId}</span>
          </p>
          <div className="bg-emerald-50 p-4 rounded-2xl mb-6 text-left">
            <p className="text-sm text-emerald-800">
              <strong>Your Therapist:</strong> {therapistInfo?.therapist_name}
            </p>
            <p className="text-xs text-emerald-600 mt-2">
              You can now login using your mobile number and password.
            </p>
          </div>
          <Button 
            onClick={() => navigate('/login')} 
            className="w-full py-5 rounded-2xl bg-emerald-700 hover:bg-emerald-800"
          >
            Go to Login <ArrowRight className="ml-2" size={18} />
          </Button>
        </Card>
      </div>
    );
  }

  // Registration form
  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-teal-50/30 to-sky-50/50 py-8 px-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="flex items-center justify-center gap-2 mb-4">
            <img src="/logo-symbol.png" alt="COGNISPACE" className="h-10 w-auto" />
            <span className="text-2xl font-serif text-primary">COGNISPACE</span>
          </div>
          <h1 className="text-2xl font-serif text-emerald-800">Create Your Account</h1>
          <p className="text-gray-600 mt-2">Register to connect with your therapist</p>
        </div>

        {/* Therapist Info Card */}
        <Card className="p-4 bg-white rounded-2xl border-0 shadow-sm mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
              <Shield className="text-emerald-600" size={24} />
            </div>
            <div>
              <p className="text-xs text-emerald-600">Your Therapist</p>
              <p className="font-semibold text-emerald-800">{therapistInfo?.therapist_name}</p>
            </div>
          </div>
        </Card>

        {/* Registration Form */}
        <Card className="p-6 bg-white rounded-3xl border-0 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Required Fields */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <UserPlus size={16} /> Required Information
              </h3>
              
              {/* Full Name */}
              <div>
                <Label className="text-gray-700">Full Name *</Label>
                <div className="relative mt-1">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <Input
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    placeholder="Enter your full name"
                    className={`pl-10 rounded-xl ${errors.full_name ? 'border-red-500' : ''}`}
                    data-testid="register-full-name"
                  />
                </div>
                {errors.full_name && <p className="text-xs text-red-500 mt-1">{errors.full_name}</p>}
              </div>

              {/* Mobile */}
              <div>
                <Label className="text-gray-700">Mobile Number *</Label>
                <div className="relative mt-1">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <Input
                    name="mobile"
                    value={formData.mobile}
                    onChange={handleChange}
                    placeholder="10-digit mobile number"
                    maxLength={10}
                    className={`pl-10 rounded-xl ${errors.mobile ? 'border-red-500' : ''}`}
                    data-testid="register-mobile"
                  />
                </div>
                {errors.mobile && <p className="text-xs text-red-500 mt-1">{errors.mobile}</p>}
              </div>

              {/* Email */}
              <div>
                <Label className="text-gray-700">Email (Optional)</Label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <Input
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="your@email.com"
                    className={`pl-10 rounded-xl ${errors.email ? 'border-red-500' : ''}`}
                    data-testid="register-email"
                  />
                </div>
                {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
              </div>

              {/* Password */}
              <div>
                <Label className="text-gray-700">Password *</Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <Input
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Create a password"
                    className={`pl-10 rounded-xl ${errors.password ? 'border-red-500' : ''}`}
                    data-testid="register-password"
                  />
                </div>
                {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password}</p>}
              </div>

              {/* Confirm Password */}
              <div>
                <Label className="text-gray-700">Confirm Password *</Label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                  <Input
                    name="confirm_password"
                    type="password"
                    value={formData.confirm_password}
                    onChange={handleChange}
                    placeholder="Confirm your password"
                    className={`pl-10 rounded-xl ${errors.confirm_password ? 'border-red-500' : ''}`}
                    data-testid="register-confirm-password"
                  />
                </div>
                {errors.confirm_password && <p className="text-xs text-red-500 mt-1">{errors.confirm_password}</p>}
              </div>
            </div>

            {/* Optional Fields */}
            <div className="pt-4 border-t space-y-4">
              <h3 className="text-sm font-semibold text-gray-700">Additional Information (Optional)</h3>
              
              <div className="grid grid-cols-2 gap-3">
                {/* Age */}
                <div>
                  <Label className="text-gray-700 text-sm">Age</Label>
                  <Input
                    name="age"
                    type="number"
                    value={formData.age}
                    onChange={handleChange}
                    placeholder="Age"
                    className="rounded-xl mt-1"
                    data-testid="register-age"
                  />
                </div>

                {/* Referred By */}
                <div>
                  <Label className="text-gray-700 text-sm">Referred By</Label>
                  <Input
                    name="referred_by"
                    value={formData.referred_by}
                    onChange={handleChange}
                    placeholder="Who referred you?"
                    className="rounded-xl mt-1"
                    data-testid="register-referred-by"
                  />
                </div>
              </div>

              {/* Guardian Name */}
              <div>
                <Label className="text-gray-700 text-sm">Guardian Name (if applicable)</Label>
                <Input
                  name="guardian_name"
                  value={formData.guardian_name}
                  onChange={handleChange}
                  placeholder="Parent/Guardian name"
                  className="rounded-xl mt-1"
                  data-testid="register-guardian-name"
                />
              </div>

              {/* Address */}
              <div>
                <Label className="text-gray-700 text-sm">Address</Label>
                <div className="relative mt-1">
                  <MapPin className="absolute left-3 top-3 text-gray-400" size={18} />
                  <Textarea
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    placeholder="Your address"
                    rows={2}
                    className="pl-10 rounded-xl"
                    data-testid="register-address"
                  />
                </div>
              </div>

              {/* Emergency Contact */}
              <div className="bg-red-50 p-4 rounded-2xl space-y-3">
                <h4 className="text-sm font-medium text-red-800 flex items-center gap-2">
                  <Heart size={16} /> Emergency Contact
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-gray-700 text-xs">Name</Label>
                    <Input
                      name="emergency_contact_name"
                      value={formData.emergency_contact_name}
                      onChange={handleChange}
                      placeholder="Contact name"
                      className="rounded-xl mt-1 text-sm"
                      data-testid="register-emergency-name"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-700 text-xs">Phone</Label>
                    <Input
                      name="emergency_contact_phone"
                      value={formData.emergency_contact_phone}
                      onChange={handleChange}
                      placeholder="10-digit number"
                      maxLength={10}
                      className={`rounded-xl mt-1 text-sm ${errors.emergency_contact_phone ? 'border-red-500' : ''}`}
                      data-testid="register-emergency-phone"
                    />
                    {errors.emergency_contact_phone && (
                      <p className="text-xs text-red-500 mt-1">{errors.emergency_contact_phone}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={submitting}
              className="w-full py-5 text-base rounded-2xl bg-emerald-700 hover:bg-emerald-800 mt-6"
              data-testid="register-submit-button"
            >
              {submitting ? (
                <><Loader2 className="animate-spin mr-2" size={18} /> Creating Account...</>
              ) : (
                <>Create Account</>
              )}
            </Button>

            {/* Login Link */}
            <p className="text-center text-sm text-gray-500 mt-4">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="text-emerald-600 hover:text-emerald-700 font-medium"
              >
                Login here
              </button>
            </p>
          </form>
        </Card>

        {/* Privacy Note */}
        <p className="text-xs text-gray-400 text-center mt-6 px-4">
          By creating an account, you agree to share your information with your therapist 
          for the purpose of providing therapy services.
        </p>
      </div>
    </div>
  );
};

export default ClientRegisterPage;
