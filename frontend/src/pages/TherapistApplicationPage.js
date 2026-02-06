import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { API } from '../App';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card } from '../components/ui/card';
import { ArrowLeft, MapPin, Loader2 } from 'lucide-react';

const SPECIALIZATION_OPTIONS = [
  'Anxiety Disorders',
  'Depression',
  'Trauma & PTSD',
  'OCD',
  'Relationship Issues',
  'Family Therapy',
  'Child & Adolescent',
  'Addiction & Substance Abuse',
  'Eating Disorders',
  'Grief & Loss',
  'Stress Management',
  'Career Counseling',
  'CBT',
  'DBT',
  'EMDR',
  'Psychodynamic',
  'Mindfulness-Based'
];

const TherapistApplicationPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [pincodeLoading, setPincodeLoading] = useState(false);
  const [showSpecDropdown, setShowSpecDropdown] = useState(false);
  
  const [application, setApplication] = useState({
    mobile: '',
    email: '',
    full_name: '',
    qualifications: '',
    specializations: [],
    years_of_experience: '',
    clinic_name: '',
    address_line_1: '',
    address_line_2: '',
    pincode: '',
    city: '',
    state: '',
    district: '',
    google_maps_link: ''
  });

  const handlePincodeChange = async (pincode) => {
    setApplication({ ...application, pincode });
    
    if (pincode.length === 6) {
      setPincodeLoading(true);
      try {
        const response = await axios.get(`https://api.postalpincode.in/pincode/${pincode}`);
        if (response.data[0]?.Status === 'Success' && response.data[0]?.PostOffice?.length > 0) {
          const postOffice = response.data[0].PostOffice[0];
          setApplication(prev => ({
            ...prev,
            city: postOffice.Block || postOffice.Name,
            district: postOffice.District,
            state: postOffice.State
          }));
        }
      } catch (error) {
        console.error('Pincode lookup failed:', error);
      } finally {
        setPincodeLoading(false);
      }
    }
  };

  const toggleSpecialization = (spec) => {
    setApplication(prev => ({
      ...prev,
      specializations: prev.specializations.includes(spec)
        ? prev.specializations.filter(s => s !== spec)
        : [...prev.specializations, spec]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!/^\d{10}$/.test(application.mobile)) {
      toast.error('Mobile number must be exactly 10 digits');
      return;
    }

    if (!application.qualifications.trim()) {
      toast.error('Please enter your qualifications/credentials');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...application,
        years_of_experience: application.years_of_experience
          ? parseInt(application.years_of_experience)
          : null,
      };

      await axios.post(`${API}/auth/therapist-application`, payload);
      toast.success('Application submitted! You will be notified once approved.');
      setTimeout(() => navigate('/login'), 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Application failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white py-8 px-4">
      {/* Navigation */}
      <nav className="max-w-3xl mx-auto mb-6">
        <Link to="/login" className="flex items-center gap-2 text-slate-600 hover:text-primary transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">Back to Login</span>
        </Link>
      </nav>

      <Card className="w-full max-w-3xl mx-auto p-8 bg-white/70 backdrop-blur-xl border border-slate-200 shadow-xl rounded-2xl">
        <div className="mb-8 text-center">
          <img src="/logo-cognispace.png" alt="COGNISPACE" className="h-20 mx-auto mb-4 object-contain" />
          <h2 className="text-3xl font-serif text-primary mb-2">Apply as Therapist</h2>
          <p className="text-muted-foreground">
            Submit your application to join the COGNISPACE platform
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Info Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-700 border-b pb-2">Personal Information</h3>
            
            <div>
              <Label htmlFor="full-name">Full Name *</Label>
              <Input
                id="full-name"
                data-testid="application-name-input"
                value={application.full_name}
                onChange={(e) => setApplication({ ...application, full_name: e.target.value })}
                required
                className="mt-1"
                placeholder="Dr. / Mr. / Ms. Full Name"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="mobile">Mobile Number *</Label>
                <Input
                  id="mobile"
                  data-testid="application-mobile-input"
                  value={application.mobile}
                  onChange={(e) =>
                    setApplication({
                      ...application,
                      mobile: e.target.value.replace(/\D/g, '').slice(0, 10),
                    })
                  }
                  required
                  className="mt-1"
                  placeholder="10-digit mobile"
                  maxLength={10}
                />
              </div>

              <div>
                <Label htmlFor="email">Email *</Label>
                <Input
                  id="email"
                  type="email"
                  data-testid="application-email-input"
                  value={application.email}
                  onChange={(e) => setApplication({ ...application, email: e.target.value })}
                  required
                  className="mt-1"
                  placeholder="your.email@example.com"
                />
              </div>
            </div>
          </div>

          {/* Professional Info Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-700 border-b pb-2">Professional Information</h3>
            
            <div>
              <Label htmlFor="qualifications">Qualifications / Credentials *</Label>
              <Input
                id="qualifications"
                data-testid="application-qualifications-input"
                value={application.qualifications}
                onChange={(e) => setApplication({ ...application, qualifications: e.target.value })}
                required
                className="mt-1"
                placeholder="e.g., M.Phil Clinical Psychology, RCI License #12345"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="experience">Years of Experience</Label>
                <Input
                  id="experience"
                  type="number"
                  data-testid="application-experience-input"
                  value={application.years_of_experience}
                  onChange={(e) =>
                    setApplication({ ...application, years_of_experience: e.target.value })
                  }
                  className="mt-1"
                  min="0"
                  placeholder="e.g., 5"
                />
              </div>

              <div>
                <Label htmlFor="clinic_name">Clinic / Practice Name</Label>
                <Input
                  id="clinic_name"
                  value={application.clinic_name}
                  onChange={(e) => setApplication({ ...application, clinic_name: e.target.value })}
                  className="mt-1"
                  placeholder="e.g., Mind Wellness Clinic"
                />
              </div>
            </div>

            {/* Specializations */}
            <div>
              <Label>Specializations</Label>
              <div className="relative mt-1">
                <div 
                  className="min-h-[42px] p-2 border rounded-md cursor-pointer bg-white flex flex-wrap gap-1"
                  onClick={() => setShowSpecDropdown(!showSpecDropdown)}
                >
                  {application.specializations.length === 0 ? (
                    <span className="text-muted-foreground text-sm">Select specializations...</span>
                  ) : (
                    application.specializations.map(spec => (
                      <span key={spec} className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full">
                        {spec}
                      </span>
                    ))
                  )}
                </div>
                
                {showSpecDropdown && (
                  <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {SPECIALIZATION_OPTIONS.map(spec => (
                      <div
                        key={spec}
                        className={`px-3 py-2 cursor-pointer hover:bg-slate-50 flex items-center gap-2 ${
                          application.specializations.includes(spec) ? 'bg-primary/5' : ''
                        }`}
                        onClick={() => toggleSpecialization(spec)}
                      >
                        <input
                          type="checkbox"
                          checked={application.specializations.includes(spec)}
                          onChange={() => {}}
                          className="rounded"
                        />
                        <span className="text-sm">{spec}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Address Section */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-700 border-b pb-2">Clinic Address (Optional)</h3>
            
            <div>
              <Label htmlFor="address_line_1">Address Line 1</Label>
              <Input
                id="address_line_1"
                value={application.address_line_1}
                onChange={(e) => setApplication({ ...application, address_line_1: e.target.value })}
                className="mt-1"
                placeholder="Building, Street"
              />
            </div>

            <div>
              <Label htmlFor="address_line_2">Address Line 2</Label>
              <Input
                id="address_line_2"
                value={application.address_line_2}
                onChange={(e) => setApplication({ ...application, address_line_2: e.target.value })}
                className="mt-1"
                placeholder="Area, Landmark"
              />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="pincode">Pincode</Label>
                <div className="relative">
                  <Input
                    id="pincode"
                    value={application.pincode}
                    onChange={(e) => handlePincodeChange(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="mt-1"
                    placeholder="6-digit"
                    maxLength={6}
                  />
                  {pincodeLoading && (
                    <Loader2 className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-primary" />
                  )}
                </div>
              </div>

              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  value={application.city}
                  onChange={(e) => setApplication({ ...application, city: e.target.value })}
                  className="mt-1"
                  placeholder="City"
                />
              </div>

              <div>
                <Label htmlFor="district">District</Label>
                <Input
                  id="district"
                  value={application.district}
                  onChange={(e) => setApplication({ ...application, district: e.target.value })}
                  className="mt-1"
                  placeholder="District"
                />
              </div>

              <div>
                <Label htmlFor="state">State</Label>
                <Input
                  id="state"
                  value={application.state}
                  onChange={(e) => setApplication({ ...application, state: e.target.value })}
                  className="mt-1"
                  placeholder="State"
                />
              </div>
            </div>

            {/* Google Maps Link */}
            <div>
              <Label htmlFor="google_maps_link" className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-slate-500" />
                Google Maps Link (Optional)
              </Label>
              <Input
                id="google_maps_link"
                value={application.google_maps_link}
                onChange={(e) => setApplication({ ...application, google_maps_link: e.target.value })}
                className="mt-1"
                placeholder="https://maps.google.com/..."
              />
              <p className="text-xs text-muted-foreground mt-1">
                Paste your clinic's Google Maps location link for easy navigation
              </p>
            </div>
          </div>

          {/* Info Box */}
          <div className="p-4 bg-info/10 border border-info/20 rounded-lg">
            <p className="text-sm text-info">
              <strong>Note:</strong> Your application will be reviewed by our admin team. You will
              receive login credentials via email once approved.
            </p>
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-4">
            <Button
              type="submit"
              className="flex-1 bg-primary hover:bg-primary/90 rounded-full h-12"
              disabled={loading}
              data-testid="submit-application-button"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Submit Application'
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/login')}
              className="flex-1 rounded-full h-12"
              data-testid="back-to-login-button"
            >
              Back to Login
            </Button>
          </div>
        </form>
      </Card>

      {/* Footer */}
      <footer className="max-w-3xl mx-auto mt-8 text-center text-xs text-slate-400">
        <p>© 2026 COGNISPACE by Vedic Wellness Solutions</p>
      </footer>
    </div>
  );
};

export default TherapistApplicationPage;
