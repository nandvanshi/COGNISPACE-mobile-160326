import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { 
  Plus, MessageSquare, Clock, AlertCircle, CheckCircle2, 
  ChevronRight, ArrowLeft, User, Shield
} from 'lucide-react';
import { toast } from 'sonner';

const SupportTickets = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewTicket, setShowNewTicket] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [newTicket, setNewTicket] = useState({
    subject: '',
    category: 'technical',
    description: '',
    priority: 'medium'
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = async () => {
    try {
      const res = await axios.get(`${API}/support/tickets`);
      setTickets(res.data);
    } catch (error) {
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!newTicket.subject.trim() || !newTicket.description.trim()) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setSubmitting(true);
    try {
      await axios.post(`${API}/support/tickets`, newTicket);
      toast.success('Ticket created successfully');
      setShowNewTicket(false);
      setNewTicket({ subject: '', category: 'technical', description: '', priority: 'medium' });
      fetchTickets();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const fetchTicketDetails = async (ticketId) => {
    try {
      const res = await axios.get(`${API}/support/tickets/${ticketId}`);
      setSelectedTicket(res.data);
    } catch (error) {
      toast.error('Failed to load ticket details');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      open: 'bg-blue-100 text-blue-800 border-blue-200',
      in_progress: 'bg-amber-100 text-amber-800 border-amber-200',
      closed: 'bg-green-100 text-green-800 border-green-200'
    };
    const labels = { open: 'Open', in_progress: 'In Progress', closed: 'Closed' };
    return <Badge variant="outline" className={styles[status]}>{labels[status]}</Badge>;
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      low: 'bg-slate-100 text-slate-700',
      medium: 'bg-blue-100 text-blue-700',
      high: 'bg-red-100 text-red-700'
    };
    return <Badge variant="outline" className={styles[priority]}>{priority.charAt(0).toUpperCase() + priority.slice(1)}</Badge>;
  };

  const getCategoryLabel = (category) => {
    const labels = { technical: 'Technical', billing: 'Billing', subscription: 'Subscription', other: 'Other' };
    return labels[category] || category;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${minutes}`;
  };

  if (selectedTicket) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setSelectedTicket(null)}>
            <ArrowLeft size={18} className="mr-2" /> Back to Tickets
          </Button>
        </div>

        <Card className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-semibold">{selectedTicket.subject}</h2>
              <div className="flex gap-2 mt-2">
                {getStatusBadge(selectedTicket.status)}
                {getPriorityBadge(selectedTicket.priority)}
                <Badge variant="outline">{getCategoryLabel(selectedTicket.category)}</Badge>
              </div>
            </div>
            <span className="text-sm text-muted-foreground">{formatDate(selectedTicket.created_at)}</span>
          </div>
          
          <div className="bg-muted/30 p-4 rounded-lg mb-6">
            <p className="whitespace-pre-wrap">{selectedTicket.description}</p>
          </div>

          <div className="space-y-4">
            <h3 className="font-medium flex items-center gap-2">
              <MessageSquare size={18} /> Conversation
            </h3>
            
            {selectedTicket.replies && selectedTicket.replies.length > 0 ? (
              <div className="space-y-4">
                {selectedTicket.replies.map((reply) => (
                  <div 
                    key={reply.id} 
                    className={`p-4 rounded-lg ${
                      reply.author_role === 'super_admin' 
                        ? 'bg-primary/10 border-l-4 border-primary ml-4' 
                        : 'bg-muted/50 mr-4'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {reply.author_role === 'super_admin' ? (
                        <Shield size={16} className="text-primary" />
                      ) : (
                        <User size={16} className="text-muted-foreground" />
                      )}
                      <span className="font-medium text-sm">{reply.author_name}</span>
                      <span className="text-xs text-muted-foreground">{formatDate(reply.created_at)}</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">{reply.message}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
                <p>No replies yet. Our support team will respond soon.</p>
              </div>
            )}

            {selectedTicket.status === 'closed' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <CheckCircle2 className="mx-auto text-green-600 mb-2" size={24} />
                <p className="text-green-800 font-medium">This ticket has been resolved</p>
              </div>
            )}
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Support</h1>
          <p className="text-muted-foreground">Create and track support tickets</p>
        </div>
        <Button onClick={() => setShowNewTicket(true)} className="gap-2" data-testid="new-ticket-btn">
          <Plus size={18} /> New Ticket
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : tickets.length === 0 ? (
        <Card className="p-12 text-center">
          <MessageSquare size={48} className="mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No support tickets</h3>
          <p className="text-muted-foreground mb-4">Create a ticket to get help from our support team</p>
          <Button onClick={() => setShowNewTicket(true)} className="gap-2">
            <Plus size={18} /> Create Ticket
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {tickets.map((ticket) => (
            <Card 
              key={ticket.id} 
              className="p-4 hover:bg-muted/30 cursor-pointer transition-colors"
              onClick={() => fetchTicketDetails(ticket.id)}
              data-testid={`ticket-${ticket.id}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium">{ticket.subject}</h3>
                    {ticket.replies?.length > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {ticket.replies.length} {ticket.replies.length === 1 ? 'reply' : 'replies'}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {getStatusBadge(ticket.status)}
                    {getPriorityBadge(ticket.priority)}
                    <span className="text-muted-foreground">
                      <Clock size={14} className="inline mr-1" />
                      {formatDate(ticket.created_at)}
                    </span>
                  </div>
                </div>
                <ChevronRight size={20} className="text-muted-foreground" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* New Ticket Dialog */}
      <Dialog open={showNewTicket} onOpenChange={setShowNewTicket}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Support Ticket</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTicket} className="space-y-4">
            <div>
              <Label htmlFor="subject">Subject *</Label>
              <Input
                id="subject"
                value={newTicket.subject}
                onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                placeholder="Brief description of the issue"
                className="mt-1"
                required
                data-testid="ticket-subject"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="category">Category</Label>
                <select
                  id="category"
                  value={newTicket.category}
                  onChange={(e) => setNewTicket({ ...newTicket, category: e.target.value })}
                  className="w-full mt-1 h-10 px-3 rounded-md border border-input bg-background"
                  data-testid="ticket-category"
                >
                  <option value="technical">Technical</option>
                  <option value="billing">Billing</option>
                  <option value="subscription">Subscription</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <Label htmlFor="priority">Priority</Label>
                <select
                  id="priority"
                  value={newTicket.priority}
                  onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                  className="w-full mt-1 h-10 px-3 rounded-md border border-input bg-background"
                  data-testid="ticket-priority"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            
            <div>
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                value={newTicket.description}
                onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                placeholder="Please describe your issue in detail..."
                className="mt-1"
                rows={5}
                required
                data-testid="ticket-description"
              />
            </div>
            
            <div className="flex gap-3 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowNewTicket(false)} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="flex-1" data-testid="submit-ticket-btn">
                {submitting ? 'Creating...' : 'Create Ticket'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SupportTickets;
