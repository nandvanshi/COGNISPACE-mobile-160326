import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';
import { 
  Link2, Copy, CheckCircle, RefreshCw, 
  UserPlus, ExternalLink, Loader2, Share2
} from 'lucide-react';

const ClientRegistrationLink = () => {
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [registrationCode, setRegistrationCode] = useState('');
  const [copied, setCopied] = useState(false);

  const baseUrl = window.location.origin;

  useEffect(() => {
    fetchRegistrationLink();
  }, []);

  const fetchRegistrationLink = async () => {
    try {
      const response = await axios.get(`${API}/auth/therapist-registration-link`);
      setRegistrationCode(response.data.registration_code);
    } catch (error) {
      console.error('Failed to fetch registration link:', error);
      toast.error('Failed to load registration link');
    } finally {
      setLoading(false);
    }
  };

  const regenerateLink = async () => {
    setRegenerating(true);
    try {
      const response = await axios.post(`${API}/auth/therapist-registration-link/regenerate`);
      setRegistrationCode(response.data.registration_code);
      toast.success('New registration link generated!');
    } catch (error) {
      toast.error('Failed to regenerate link');
    } finally {
      setRegenerating(false);
    }
  };

  const fullLink = `${baseUrl}/register/client/${registrationCode}`;

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(fullLink);
      setCopied(true);
      toast.success('Link copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = fullLink;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      toast.success('Link copied!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const shareLink = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Register as my client',
          text: 'Use this link to register as my client on COGNISPACE',
          url: fullLink,
        });
      } catch (err) {
        if (err.name !== 'AbortError') {
          copyToClipboard();
        }
      }
    } else {
      copyToClipboard();
    }
  };

  if (loading) {
    return (
      <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100 rounded-2xl">
        <div className="flex items-center justify-center py-4">
          <Loader2 className="animate-spin text-blue-600" size={24} />
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100 rounded-2xl" data-testid="client-registration-link-card">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <UserPlus className="text-blue-600" size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-blue-900 mb-1">Client Registration Link</h3>
          <p className="text-xs text-blue-700 mb-3">
            Share this link with new clients to let them register themselves
          </p>
          
          {/* Link Input with Copy Button */}
          <div className="flex gap-2 mb-3">
            <div className="flex-1 relative">
              <Input
                value={fullLink}
                readOnly
                className="pr-10 text-sm font-mono bg-white border-blue-200 rounded-xl truncate"
                data-testid="registration-link-input"
              />
              <Link2 className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-400" size={16} />
            </div>
            <Button
              onClick={copyToClipboard}
              variant="outline"
              size="icon"
              className={`rounded-xl border-blue-200 ${copied ? 'bg-green-100 border-green-300' : 'hover:bg-blue-100'}`}
              data-testid="copy-link-button"
            >
              {copied ? (
                <CheckCircle className="text-green-600" size={18} />
              ) : (
                <Copy className="text-blue-600" size={18} />
              )}
            </Button>
          </div>
          
          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={shareLink}
              size="sm"
              className="rounded-xl bg-blue-600 hover:bg-blue-700 text-xs"
              data-testid="share-link-button"
            >
              <Share2 size={14} className="mr-1" /> Share Link
            </Button>
            
            <Button
              onClick={() => window.open(fullLink, '_blank')}
              variant="outline"
              size="sm"
              className="rounded-xl border-blue-200 text-blue-700 hover:bg-blue-50 text-xs"
              data-testid="preview-link-button"
            >
              <ExternalLink size={14} className="mr-1" /> Preview
            </Button>
            
            <Button
              onClick={regenerateLink}
              variant="ghost"
              size="sm"
              disabled={regenerating}
              className="rounded-xl text-blue-600 hover:bg-blue-100 text-xs"
              data-testid="regenerate-link-button"
            >
              {regenerating ? (
                <Loader2 size={14} className="mr-1 animate-spin" />
              ) : (
                <RefreshCw size={14} className="mr-1" />
              )}
              Regenerate
            </Button>
          </div>
          
          {/* Note */}
          <p className="text-xs text-blue-600 mt-3 bg-blue-100/50 p-2 rounded-lg">
            💡 Regenerating creates a new link and invalidates the old one.
          </p>
        </div>
      </div>
    </Card>
  );
};

export default ClientRegistrationLink;
