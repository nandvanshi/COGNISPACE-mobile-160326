import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card } from '../components/ui/card';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loginForm, setLoginForm] = useState({ identifier: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, loginForm);
      login(response.data.token, response.data.user);
      toast.success('Welcome back!');
      navigate(response.data.user.role === 'therapist' ? '/therapist' : '/client');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div
        className="hidden lg:flex lg:w-1/2 bg-cover bg-center relative"
        style={{
          backgroundImage:
            'url(https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=1200)',
        }}
      >
        <div className="absolute inset-0 bg-primary/40 backdrop-blur-sm" />
        <div className="relative z-10 p-12 flex flex-col justify-end">
          <h1 className="text-5xl font-serif text-white mb-4">COGNISPACE</h1>
          <p className="text-xl text-white/90">
            Precision Insights. Personal Growth.
          </p>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <Card className="w-full max-w-md p-8 bg-white/70 backdrop-blur-xl border border-border/40 rounded-2xl shadow-xl">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-serif text-primary mb-2">Welcome Back</h2>
            <p className="text-muted-foreground">Sign in to your account</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="login-identifier">Mobile or Email</Label>
              <Input
                id="login-identifier"
                data-testid="login-identifier-input"
                value={loginForm.identifier}
                onChange={(e) => setLoginForm({ ...loginForm, identifier: e.target.value })}
                required
                className="mt-1"
                placeholder="10-digit mobile or email"
              />
            </div>
            <div>
              <Label htmlFor="login-password">Password</Label>
              <Input
                id="login-password"
                type="password"
                data-testid="login-password-input"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                required
                className="mt-1"
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-primary hover:bg-primary-700 text-white rounded-full h-12 text-base font-medium"
              disabled={loading}
              data-testid="login-submit-button"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-border/40">
            <p className="text-sm text-muted-foreground text-center mb-4">
              Are you a therapist looking to join COGNISPACE?
            </p>
            <Button
              variant="outline"
              onClick={() => navigate('/therapist-application')}
              className="w-full"
              data-testid="therapist-apply-button"
            >
              Apply as Therapist
            </Button>
          </div>

          <div className="mt-6 p-4 bg-info/10 border border-info/20 rounded-lg">
            <p className="text-sm text-info text-center">
              <strong>Clients:</strong> Please contact your therapist to create an account for you.
              Client self-registration is not available.
            </p>
          </div>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            <p>Secure, HIPAA-minded therapy platform</p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
