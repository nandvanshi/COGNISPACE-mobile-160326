import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { toast } from 'sonner';
import {
  Mail, Send, Sparkles, Loader2, Users, UserCog, Filter,
  CheckCircle2, XCircle, Clock, History, Eye, ChevronDown,
  ChevronUp, Search
} from 'lucide-react';

const AdminEmailBroadcast = () => {
  const [recipientSummary, setRecipientSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Composer state
  const [showComposer, setShowComposer] = useState(false);
  const [recipientType, setRecipientType] = useState('all_therapists');
  const [planFilter, setPlanFilter] = useState('');
  const [specificIds, setSpecificIds] = useState([]);
  const [subject, setSubject] = useState('');
  const [htmlBody, setHtmlBody] = useState('');
  const [textBody, setTextBody] = useState('');

  // AI draft state
  const [aiTopic, setAiTopic] = useState('');
  const [aiTone, setAiTone] = useState('professional');
  const [aiAudience, setAiAudience] = useState('therapists');
  const [aiExtra, setAiExtra] = useState('');
  const [generatingDraft, setGeneratingDraft] = useState(false);

  // Send state
  const [sending, setSending] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showRecipientPicker, setShowRecipientPicker] = useState(false);
  const [recipientList, setRecipientList] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingRecipients, setLoadingRecipients] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [sumRes, histRes] = await Promise.all([
        axios.get(`${API}/admin/email/recipients/summary`),
        axios.get(`${API}/admin/email/history`)
      ]);
      setRecipientSummary(sumRes.data);
      setHistory(histRes.data);
    } catch (e) {
      console.error('Email data fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const fetchRecipientList = async (role) => {
    setLoadingRecipients(true);
    try {
      const params = { role };
      const res = await axios.get(`${API}/admin/email/recipients/list`, { params });
      setRecipientList(res.data);
    } catch (e) {
      toast.error('Failed to load recipients');
    } finally {
      setLoadingRecipients(false);
    }
  };

  const generateAIDraft = async () => {
    if (!aiTopic.trim()) { toast.error('Enter a topic'); return; }
    setGeneratingDraft(true);
    try {
      const res = await axios.post(`${API}/admin/email/ai-draft`, {
        topic: aiTopic,
        tone: aiTone,
        audience: aiAudience,
        additional_instructions: aiExtra || null
      });
      if (res.data.generated) {
        setSubject(res.data.data.subject || '');
        setHtmlBody(res.data.data.html_body || '');
        setTextBody(res.data.data.text_body || '');
        toast.success('AI draft generated! Review and edit before sending.');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'AI generation failed');
    } finally {
      setGeneratingDraft(false);
    }
  };

  const handleSend = async () => {
    if (!subject.trim() || !htmlBody.trim()) {
      toast.error('Subject and body are required');
      return;
    }
    setSending(true);
    try {
      const payload = {
        subject,
        html_body: htmlBody,
        text_body: textBody || subject,
        recipient_type: recipientType,
        plan_filter: recipientType === 'by_plan' ? planFilter : null,
        specific_ids: recipientType === 'specific' ? specificIds : null
      };
      const res = await axios.post(`${API}/admin/email/send`, payload);
      toast.success(`Sent to ${res.data.sent}/${res.data.total_recipients} recipients`);
      if (res.data.failed > 0) {
        toast.warning(`${res.data.failed} emails failed`);
      }
      setShowComposer(false);
      resetComposer();
      fetchData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Send failed');
    } finally {
      setSending(false);
    }
  };

  const resetComposer = () => {
    setSubject('');
    setHtmlBody('');
    setTextBody('');
    setAiTopic('');
    setAiExtra('');
    setSpecificIds([]);
    setRecipientType('all_therapists');
  };

  const getRecipientLabel = () => {
    const labels = {
      all_therapists: 'All Therapists',
      all_clients: 'All Clients',
      by_plan: `Therapists (${planFilter || 'Select Plan'})`,
      specific: `${specificIds.length} Selected`
    };
    return labels[recipientType] || recipientType;
  };

  const getRecipientCount = () => {
    if (!recipientSummary) return 0;
    if (recipientType === 'all_therapists') return recipientSummary.therapists.with_email;
    if (recipientType === 'all_clients') return recipientSummary.clients.with_email;
    if (recipientType === 'by_plan') return recipientSummary.therapists.by_plan?.[planFilter] || 0;
    if (recipientType === 'specific') return specificIds.length;
    return 0;
  };

  const filteredRecipients = recipientList.filter(r =>
    r.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="animate-spin" size={32} /></div>;
  }

  return (
    <div className="space-y-6" data-testid="admin-email-broadcast">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Email Broadcast</h2>
          <p className="text-sm text-muted-foreground mt-1">AI-powered email composer for therapists & clients</p>
        </div>
        <Button onClick={() => setShowComposer(true)} className="gap-2" data-testid="compose-email-btn">
          <Mail size={16} /> Compose Email
        </Button>
      </div>

      {/* Stats Cards */}
      {recipientSummary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="p-4 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-2 text-sm text-muted-foreground"><UserCog size={14} /> Therapists</div>
            <p className="text-2xl font-bold mt-1">{recipientSummary.therapists.with_email}</p>
            <p className="text-xs text-muted-foreground">with email</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-green-500">
            <div className="flex items-center gap-2 text-sm text-muted-foreground"><Users size={14} /> Clients</div>
            <p className="text-2xl font-bold mt-1">{recipientSummary.clients.with_email}</p>
            <p className="text-xs text-muted-foreground">with email</p>
          </Card>
          {Object.entries(recipientSummary.therapists.by_plan || {}).map(([plan, count]) => (
            <Card key={plan} className="p-4 border-l-4 border-l-purple-500">
              <div className="flex items-center gap-2 text-sm text-muted-foreground"><Filter size={14} /> {plan}</div>
              <p className="text-2xl font-bold mt-1">{count}</p>
              <p className="text-xs text-muted-foreground">therapists</p>
            </Card>
          ))}
        </div>
      )}

      {/* History */}
      <Card className="p-4">
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="w-full flex items-center justify-between"
          data-testid="email-history-toggle"
        >
          <h3 className="font-medium flex items-center gap-2"><History size={16} /> Email History</h3>
          {showHistory ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
        {showHistory && (
          <div className="mt-4 space-y-2">
            {history.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No emails sent yet</p>
            ) : (
              history.map((h, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium truncate">{h.subject}</p>
                    <p className="text-xs text-muted-foreground">
                      To: {h.recipient_type}{h.plan_filter ? ` (${h.plan_filter})` : ''} | {new Date(h.sent_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 ml-3">
                    <span className="flex items-center gap-1 text-green-600"><CheckCircle2 size={14} /> {h.sent}</span>
                    {h.failed > 0 && <span className="flex items-center gap-1 text-red-500"><XCircle size={14} /> {h.failed}</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </Card>

      {/* Composer Dialog */}
      <Dialog open={showComposer} onOpenChange={setShowComposer}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail size={20} className="text-primary" /> Compose Email
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5">
            {/* AI Draft Generator */}
            <Card className="p-4 bg-gradient-to-r from-violet-50 to-blue-50 border-violet-200">
              <h4 className="font-medium flex items-center gap-2 mb-3">
                <Sparkles size={16} className="text-violet-600" /> AI Draft Generator
              </h4>
              <div className="space-y-3">
                <div>
                  <Label>Topic / What do you want to say?</Label>
                  <Input
                    value={aiTopic}
                    onChange={(e) => setAiTopic(e.target.value)}
                    placeholder="e.g., New feature announcement, Workshop invitation, Holiday greetings..."
                    className="mt-1"
                    data-testid="ai-topic-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Tone</Label>
                    <Select value={aiTone} onValueChange={setAiTone}>
                      <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="professional">Professional</SelectItem>
                        <SelectItem value="friendly">Friendly</SelectItem>
                        <SelectItem value="formal">Formal</SelectItem>
                        <SelectItem value="casual">Casual</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Audience</Label>
                    <Select value={aiAudience} onValueChange={setAiAudience}>
                      <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="therapists">Therapists</SelectItem>
                        <SelectItem value="clients">Clients</SelectItem>
                        <SelectItem value="everyone">Everyone</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label>Additional Instructions (optional)</Label>
                  <Input
                    value={aiExtra}
                    onChange={(e) => setAiExtra(e.target.value)}
                    placeholder="Any specific points to include..."
                    className="mt-1"
                  />
                </div>
                <Button
                  onClick={generateAIDraft}
                  disabled={generatingDraft || !aiTopic.trim()}
                  variant="outline"
                  className="w-full border-violet-300 text-violet-700 hover:bg-violet-100"
                  data-testid="generate-draft-btn"
                >
                  {generatingDraft ? <Loader2 size={16} className="animate-spin mr-2" /> : <Sparkles size={16} className="mr-2" />}
                  {generatingDraft ? 'Generating...' : 'Generate Draft'}
                </Button>
              </div>
            </Card>

            {/* Recipients */}
            <div>
              <Label>Recipients</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {[
                  { value: 'all_therapists', label: 'All Therapists', icon: UserCog },
                  { value: 'all_clients', label: 'All Clients', icon: Users },
                  { value: 'by_plan', label: 'By Plan', icon: Filter },
                  { value: 'specific', label: 'Specific Users', icon: Search },
                ].map(opt => (
                  <button
                    key={opt.value}
                    onClick={() => {
                      setRecipientType(opt.value);
                      if (opt.value === 'specific') {
                        fetchRecipientList('therapist');
                        setShowRecipientPicker(true);
                      }
                    }}
                    className={`flex items-center gap-2 p-3 rounded-lg border text-sm transition-all ${
                      recipientType === opt.value
                        ? 'border-primary bg-primary/5 text-primary font-medium'
                        : 'border-border hover:border-primary/50'
                    }`}
                    data-testid={`recipient-${opt.value}`}
                  >
                    <opt.icon size={16} /> {opt.label}
                  </button>
                ))}
              </div>

              {recipientType === 'by_plan' && recipientSummary && (
                <div className="mt-2">
                  <Select value={planFilter} onValueChange={setPlanFilter}>
                    <SelectTrigger><SelectValue placeholder="Select Plan" /></SelectTrigger>
                    <SelectContent>
                      {Object.keys(recipientSummary.therapists.by_plan || {}).map(plan => (
                        <SelectItem key={plan} value={plan}>{plan} ({recipientSummary.therapists.by_plan[plan]})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <p className="text-xs text-muted-foreground mt-2">
                Sending to: <strong>{getRecipientLabel()}</strong> ({getRecipientCount()} recipients)
              </p>
            </div>

            {/* Subject */}
            <div>
              <Label>Subject</Label>
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Email subject line..."
                className="mt-1"
                data-testid="email-subject-input"
              />
            </div>

            {/* Body */}
            <div>
              <div className="flex items-center justify-between">
                <Label>Email Body (HTML)</Label>
                <Button variant="ghost" size="sm" onClick={() => setShowPreview(!showPreview)} className="text-xs gap-1">
                  <Eye size={12} /> {showPreview ? 'Edit' : 'Preview'}
                </Button>
              </div>
              {showPreview ? (
                <Card className="mt-1 p-4 min-h-[200px] max-h-[300px] overflow-y-auto prose prose-sm">
                  <div dangerouslySetInnerHTML={{ __html: htmlBody }} />
                </Card>
              ) : (
                <textarea
                  value={htmlBody}
                  onChange={(e) => setHtmlBody(e.target.value)}
                  placeholder="<p>Write your email content here...</p>"
                  className="mt-1 w-full min-h-[200px] p-3 rounded-lg border border-border text-sm font-mono bg-background resize-y"
                  data-testid="email-body-input"
                />
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <Button
                onClick={handleSend}
                disabled={sending || !subject.trim() || !htmlBody.trim() || getRecipientCount() === 0}
                className="flex-1 gap-2"
                data-testid="send-email-btn"
              >
                {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                {sending ? 'Sending...' : `Send to ${getRecipientCount()} recipients`}
              </Button>
              <Button variant="outline" onClick={() => { setShowComposer(false); resetComposer(); }}>Cancel</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Specific Recipients Picker Dialog */}
      <Dialog open={showRecipientPicker} onOpenChange={setShowRecipientPicker}>
        <DialogContent className="max-w-lg max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Select Recipients</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex gap-2">
              <Button size="sm" variant={recipientList[0]?.role !== 'client' ? 'default' : 'outline'} onClick={() => fetchRecipientList('therapist')}>Therapists</Button>
              <Button size="sm" variant={recipientList[0]?.role === 'client' ? 'default' : 'outline'} onClick={() => fetchRecipientList('client')}>Clients</Button>
            </div>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or email..."
              data-testid="recipient-search"
            />
            <div className="max-h-[400px] overflow-y-auto space-y-1">
              {loadingRecipients ? (
                <div className="flex justify-center py-8"><Loader2 className="animate-spin" size={20} /></div>
              ) : (
                filteredRecipients.map(r => (
                  <label key={r.id} className="flex items-center gap-3 p-2 rounded hover:bg-muted/50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={specificIds.includes(r.id)}
                      onChange={(e) => {
                        if (e.target.checked) setSpecificIds([...specificIds, r.id]);
                        else setSpecificIds(specificIds.filter(id => id !== r.id));
                      }}
                      className="rounded"
                    />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{r.full_name}</p>
                      <p className="text-xs text-muted-foreground truncate">{r.email || 'No email'}</p>
                    </div>
                  </label>
                ))
              )}
            </div>
            <div className="flex justify-between items-center pt-2 border-t">
              <p className="text-sm text-muted-foreground">{specificIds.length} selected</p>
              <Button size="sm" onClick={() => setShowRecipientPicker(false)}>Done</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminEmailBroadcast;
