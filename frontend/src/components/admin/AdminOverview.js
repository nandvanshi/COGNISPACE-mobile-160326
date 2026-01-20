import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  Users, UserCheck, UserX, CreditCard, AlertTriangle, Clock,
  MessageSquare, ChevronRight, RefreshCw, TrendingUp, Shield
} from 'lucide-react';
import { toast } from 'sonner';

const AdminOverview = ({ onNavigate }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/admin/dashboard-stats`);
      setStats(res.data);
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  const metrics = stats?.metrics || {};
  const attention = stats?.attention_items || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Admin Dashboard</h1>
          <p className="text-muted-foreground">System overview and priorities</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStats} className="gap-2">
          <RefreshCw size={16} /> Refresh
        </Button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <Card 
          className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => onNavigate('therapists')}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.total_therapists}</p>
              <p className="text-xs text-muted-foreground">Total Therapists</p>
            </div>
          </div>
        </Card>

        <Card 
          className={`p-4 cursor-pointer hover:bg-muted/50 transition-colors ${metrics.pending_applications > 0 ? 'border-amber-300 bg-amber-50' : ''}`}
          onClick={() => onNavigate('applications')}
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${metrics.pending_applications > 0 ? 'bg-amber-100' : 'bg-slate-100'}`}>
              <UserCheck size={20} className={metrics.pending_applications > 0 ? 'text-amber-600' : 'text-slate-600'} />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.pending_applications}</p>
              <p className="text-xs text-muted-foreground">Pending Applications</p>
            </div>
          </div>
        </Card>

        <Card 
          className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => onNavigate('clients')}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Users size={20} className="text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.total_clients}</p>
              <p className="text-xs text-muted-foreground">Total Clients</p>
            </div>
          </div>
        </Card>

        <Card 
          className="p-4 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => onNavigate('subscriptions')}
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <CreditCard size={20} className="text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.active_subscriptions}</p>
              <p className="text-xs text-muted-foreground">Active Subscriptions</p>
            </div>
          </div>
        </Card>

        <Card 
          className={`p-4 cursor-pointer hover:bg-muted/50 transition-colors ${metrics.expired_subscriptions > 0 ? 'border-red-300 bg-red-50' : ''}`}
          onClick={() => onNavigate('therapists')}
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${metrics.expired_subscriptions > 0 ? 'bg-red-100' : 'bg-slate-100'}`}>
              <AlertTriangle size={20} className={metrics.expired_subscriptions > 0 ? 'text-red-600' : 'text-slate-600'} />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.expired_subscriptions}</p>
              <p className="text-xs text-muted-foreground">Expired Subs</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Needs Admin Attention */}
      <Card className="p-5">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <AlertTriangle size={20} className="text-amber-500" />
          Needs Admin Attention
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Pending Applications */}
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-medium flex items-center gap-2">
                <UserCheck size={16} className="text-amber-600" />
                Pending Applications
                {metrics.pending_applications > 0 && (
                  <Badge variant="destructive" className="text-xs">{metrics.pending_applications}</Badge>
                )}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => onNavigate('applications')}>
                View All <ChevronRight size={14} />
              </Button>
            </div>
            {attention.pending_applications?.length > 0 ? (
              <div className="space-y-2">
                {attention.pending_applications.map((app) => (
                  <div key={app.id} className="flex justify-between items-center text-sm p-2 bg-muted/30 rounded">
                    <span className="font-medium">{app.full_name}</span>
                    <span className="text-muted-foreground text-xs">{formatDate(app.created_at)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No pending applications</p>
            )}
          </div>

          {/* Open Support Tickets */}
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-medium flex items-center gap-2">
                <MessageSquare size={16} className="text-blue-600" />
                Open Support Tickets
                {metrics.open_tickets > 0 && (
                  <Badge className="text-xs bg-blue-100 text-blue-800">{metrics.open_tickets}</Badge>
                )}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => onNavigate('support')}>
                View All <ChevronRight size={14} />
              </Button>
            </div>
            {attention.open_tickets?.length > 0 ? (
              <div className="space-y-2">
                {attention.open_tickets.map((ticket) => (
                  <div key={ticket.id} className="flex justify-between items-center text-sm p-2 bg-muted/30 rounded">
                    <div>
                      <span className="font-medium">{ticket.subject}</span>
                      <span className="text-muted-foreground text-xs ml-2">by {ticket.therapist_name}</span>
                    </div>
                    <Badge variant="outline" className={ticket.priority === 'high' ? 'border-red-300 text-red-700' : ''}>
                      {ticket.priority}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No open tickets</p>
            )}
          </div>

          {/* Expired Subscriptions */}
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-medium flex items-center gap-2">
                <CreditCard size={16} className="text-red-600" />
                Expired Subscriptions
                {metrics.expired_subscriptions > 0 && (
                  <Badge variant="destructive" className="text-xs">{metrics.expired_subscriptions}</Badge>
                )}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => onNavigate('therapists')}>
                View All <ChevronRight size={14} />
              </Button>
            </div>
            {attention.expired_subscriptions?.length > 0 ? (
              <div className="space-y-2">
                {attention.expired_subscriptions.map((t) => (
                  <div key={t.id} className="flex justify-between items-center text-sm p-2 bg-muted/30 rounded">
                    <span className="font-medium">{t.full_name}</span>
                    <span className="text-muted-foreground text-xs">{t.email}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No expired subscriptions</p>
            )}
          </div>

          {/* Suspended Therapists */}
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-medium flex items-center gap-2">
                <UserX size={16} className="text-slate-600" />
                Suspended Accounts
                {metrics.suspended_therapists > 0 && (
                  <Badge variant="secondary" className="text-xs">{metrics.suspended_therapists}</Badge>
                )}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => onNavigate('therapists')}>
                View All <ChevronRight size={14} />
              </Button>
            </div>
            {attention.suspended_therapists?.length > 0 ? (
              <div className="space-y-2">
                {attention.suspended_therapists.map((t) => (
                  <div key={t.id} className="flex justify-between items-center text-sm p-2 bg-muted/30 rounded">
                    <span className="font-medium">{t.full_name}</span>
                    <span className="text-muted-foreground text-xs">{t.email}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No suspended accounts</p>
            )}
          </div>
        </div>
      </Card>

      {/* Quick Links */}
      <Card className="p-5">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-primary" />
          Quick Actions
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => onNavigate('applications')}>
            <UserCheck size={20} className="text-amber-600" />
            <span className="text-sm">Review Applications</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => onNavigate('subscriptions')}>
            <CreditCard size={20} className="text-primary" />
            <span className="text-sm">Manage Subscriptions</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => onNavigate('support')}>
            <MessageSquare size={20} className="text-blue-600" />
            <span className="text-sm">Support Tickets</span>
          </Button>
          <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => onNavigate('therapists')}>
            <Users size={20} className="text-green-600" />
            <span className="text-sm">Manage Therapists</span>
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AdminOverview;
