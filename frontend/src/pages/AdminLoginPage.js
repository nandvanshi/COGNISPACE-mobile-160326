import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card } from '../components/ui/card';
import { Shield } from 'lucide-react';

const AdminLoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/super-admin-login`, loginForm);
      login(response.data.token, response.data.user);
      toast.success('Welcome, Admin!');
      navigate('/admin');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-8">
      <Card className="w-full max-w-md p-8 bg-white/70 backdrop-blur-xl border-none shadow-2xl rounded-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
            <Shield className="text-primary" size={32} />
          </div>
          <h2 className="text-3xl font-serif text-primary mb-2">Admin Access</h2>
          <p className="text-muted-foreground text-center">Super Admin Login</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <Label htmlFor="admin-username">Username</Label>
            <Input
              id="admin-username"
              data-testid="admin-username-input"
              value={loginForm.username}
              onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
              required
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="admin-password">Password</Label>
            <Input
              id="admin-password"
              type="password"
              data-testid="admin-password-input"
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
            data-testid="admin-login-button"
          >
            {loading ? 'Signing in...' : 'Admin Sign In'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Button
            variant="link"
            onClick={() => navigate('/login')}
            className="text-sm"
            data-testid="back-to-regular-login"
          >
            Back to Regular Login
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AdminLoginPage;
