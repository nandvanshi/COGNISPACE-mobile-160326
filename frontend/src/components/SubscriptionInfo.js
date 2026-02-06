import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { 
  CreditCard, Calendar, CheckCircle, AlertTriangle, 
  Sparkles, Clock, Mail, MessageCircle, ExternalLink
} from 'lucide-react';
import { formatDate } from '../utils/formatUtils';

const SubscriptionInfo = () => {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const response = await axios.get(`${API}/auth/subscription-status`);
      setSubscription(response.data);
    } catch (error) {
      toast.error('Failed to load subscription details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const getStatusBadge = () => {
    if (!subscription) return null;
    
    const status = subscription.subscription_status;
    if (status === 'trial') {
      return <Badge className="bg-blue-100 text-blue-700 border-blue-200">Free Trial</Badge>;
    } else if (status === 'active') {
      return <Badge className="bg-green-100 text-green-700 border-green-200">Active</Badge>;
    } else if (status === 'expired') {
      return <Badge className="bg-red-100 text-red-700 border-red-200">Expired</Badge>;
    }
    return <Badge variant="outline">Unknown</Badge>;
  };

  const handleWhatsApp = () => {
    const message = encodeURIComponent('Hi, I have a query about my COGNISPACE subscription.');
    window.open(`https://wa.me/917348700555?text=${message}`, '_blank');
  };

  const handleEmail = () => {
    window.open('mailto:care@cognispace.in?subject=Subscription Inquiry', '_blank');
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <CreditCard size={28} className="text-primary" />
        <h1 className="text-2xl font-serif text-foreground">Subscription</h1>
      </div>

      {/* Current Plan Card */}
      <Card className="p-6 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Current Plan</h2>
            <p className="text-2xl font-bold text-primary mt-1">
              {subscription?.subscription_plan || 'Free Trial'}
            </p>
          </div>
          {getStatusBadge()}
        </div>

        <div className="grid grid-cols-2 gap-4 mt-6">
          <div className="flex items-center gap-3 p-3 bg-white/50 rounded-lg">
            <Calendar size={20} className="text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Valid Until</p>
              <p className="font-medium">
                {subscription?.subscription_end_date ? formatDate(subscription.subscription_end_date) : 'N/A'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-white/50 rounded-lg">
            <Clock size={20} className="text-primary" />
            <div>
              <p className="text-xs text-muted-foreground">Days Remaining</p>
              <p className="font-medium">
                {subscription?.days_remaining || 0} days
              </p>
            </div>
          </div>
        </div>

        {subscription?.subscription_status === 'trial' && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
            <Sparkles size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-800">You're on a Free Trial</p>
              <p className="text-xs text-blue-600 mt-1">
                Explore all features during your trial period. Upgrade anytime to continue using COGNISPACE.
              </p>
            </div>
          </div>
        )}

        {subscription?.days_remaining <= 7 && subscription?.days_remaining > 0 && (
          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
            <AlertTriangle size={20} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">Subscription Expiring Soon</p>
              <p className="text-xs text-amber-600 mt-1">
                Your subscription expires in {subscription.days_remaining} days. Contact support to renew.
              </p>
            </div>
          </div>
        )}

        {subscription?.subscription_status === 'expired' && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertTriangle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800">Subscription Expired</p>
              <p className="text-xs text-red-600 mt-1">
                Your subscription has expired. Please contact support to renew and regain full access.
              </p>
            </div>
          </div>
        )}
      </Card>

      {/* Features Included */}
      <Card className="p-6">
        <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
          <CheckCircle size={18} className="text-success" />
          Features Included in Your Plan
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {[
            'Client Management',
            'Appointment Scheduling',
            'Session Notes',
            'Assessments',
            'TheraGenie AI',
            'Payment Tracking',
            'Email Notifications',
            'Assistant Management'
          ].map((feature, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm">
              <CheckCircle size={14} className="text-success" />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Contact Support */}
      <Card className="p-6 bg-surface">
        <h3 className="font-semibold text-foreground mb-4">Need Help with Subscription?</h3>
        <p className="text-sm text-muted-foreground mb-4">
          For subscription upgrades, renewals, or any billing queries, please contact our support team.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button 
            onClick={handleWhatsApp}
            className="flex-1 bg-green-600 hover:bg-green-700"
          >
            <MessageCircle size={16} className="mr-2" />
            WhatsApp Support
          </Button>
          <Button 
            variant="outline"
            onClick={handleEmail}
            className="flex-1"
          >
            <Mail size={16} className="mr-2" />
            Email Support
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-3 text-center">
          WhatsApp: +91 7348700555 • Email: care@cognispace.in
        </p>
      </Card>
    </div>
  );
};

export default SubscriptionInfo;
