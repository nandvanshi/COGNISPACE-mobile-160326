import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { API } from '../App';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card } from '../components/ui/card';

const TherapistApplicationPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [application, setApplication] = useState({
    mobile: '',
    email: '',
    full_name: '',
    credentials: '',
    specialization: '',
    years_of_experience: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!/^\d{10}$/.test(application.mobile)) {
      toast.error('Mobile number must be exactly 10 digits');
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
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <Card className="w-full max-w-2xl p-8 bg-white/70 backdrop-blur-xl border-none shadow-2xl rounded-2xl">
        <div className="mb-8">
          <h2 className="text-4xl font-serif text-primary mb-2">Apply as Therapist</h2>
          <p className="text-muted-foreground">
            Submit your application to join the Haven platform
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label htmlFor="full-name">Full Name *</Label>
            <Input
              id="full-name"
              data-testid="application-name-input"
              value={application.full_name}
              onChange={(e) => setApplication({ ...application, full_name: e.target.value })}
              required
              className="mt-1"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
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
              />
            </div>
          </div>

          <div>
            <Label htmlFor="credentials">License / Credentials *</Label>
            <Input
              id="credentials"
              data-testid="application-credentials-input"
              value={application.credentials}
              onChange={(e) => setApplication({ ...application, credentials: e.target.value })}
              required
              className="mt-1"
              placeholder="e.g., Licensed Clinical Social Worker (LCSW), License #12345"
            />
          </div>

          <div>
            <Label htmlFor="specialization">Specialization (Optional)</Label>
            <Input
              id="specialization"
              data-testid="application-specialization-input"
              value={application.specialization}
              onChange={(e) => setApplication({ ...application, specialization: e.target.value })}
              className="mt-1"
              placeholder="e.g., CBT, Trauma, Anxiety, Depression"
            />
          </div>

          <div>
            <Label htmlFor="experience">Years of Experience (Optional)</Label>
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
            />
          </div>

          <div className="p-4 bg-info/10 border border-info/20 rounded-lg">
            <p className="text-sm text-info">
              <strong>Note:</strong> Your application will be reviewed by our admin team. You will
              receive login credentials once approved.
            </p>
          </div>

          <div className="flex gap-4">
            <Button
              type="submit"
              className="flex-1 bg-primary hover:bg-primary-700 rounded-full h-12"
              disabled={loading}
              data-testid="submit-application-button"
            >
              {loading ? 'Submitting...' : 'Submit Application'}
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
    </div>
  );
};

export default TherapistApplicationPage;
