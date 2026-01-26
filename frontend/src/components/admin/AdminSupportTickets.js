import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { 
  MessageSquare, Clock, ArrowLeft, User, Shield, Send,
  Filter, AlertTriangle, CheckCircle2, Circle, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

const AdminSupportTickets = () => {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({ open: 0, in_progress: 0, closed: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [replyText, setReplyText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchTickets();
    fetchStats();
  }, [filterStatus, filterPriority]);

  const fetchTickets = async () => {
    try {
      let url = `${API}/support/tickets`;
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterPriority) params.append('priority', filterPriority);
      if (params.toString()) url += `?${params.toString()}`;
      
      const res = await axios.get(url);
      setTickets(res.data);
    } catch (error) {
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/admin/support/stats`);
      setStats(res.data);
    } catch (error) {
      console.error('Failed to load stats');
    }
  };

  const fetchTicketDetails = async (ticketId) => {
    try {
      const res = await axios.get(`${API}/support/tickets/${ticketId}`);
      setSelectedTicket(res.data);
    } catch (error) {
      toast.error('Failed to load ticket');
    }
  };

  const handleReply = async () => {
    if (!replyText.trim()) {
      toast.error('Please enter a reply');
      return;
    }
    
    setSubmitting(true);
    try {
      await axios.post(`${API}/support/tickets/${selectedTicket.id}/reply`, { message: replyText });
      toast.success('Reply sent');
      setReplyText('');
      fetchTicketDetails(selectedTicket.id);
      fetchTickets();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reply');
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    setSubmitting(true);
    try {
      await axios.put(`${API}/support/tickets/${selectedTicket.id}/status`, { status: newStatus });
      toast.success(`Ticket marked as ${newStatus.replace('_', ' ')}`);
      fetchTicketDetails(selectedTicket.id);
      fetchTickets();
      fetchStats();
    } catch (error) {
      toast.error('Failed to update status');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      open: { style: 'bg-blue-100 text-blue-800 border-blue-200', icon: Circle },
      in_progress: { style: 'bg-amber-100 text-amber-800 border-amber-200', icon: RefreshCw },
      closed: { style: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle2 }
    };
    const { style, icon: Icon } = config[status];
    const labels = { open: 'Open', in_progress: 'In Progress', closed: 'Closed' };
    return (
      <Badge variant="outline" className={`${style} gap-1`}>
        <Icon size={12} /> {labels[status]}
      </Badge>
    );
  };

  const getPriorityBadge = (priority) => {
    const styles = {
      low: 'bg-slate-100 text-slate-700',
      medium: 'bg-blue-100 text-blue-700',
      high: 'bg-red-100 text-red-700'
    };
    return <Badge variant="outline" className={styles[priority]}>{priority.charAt(0).toUpperCase() + priority.slice(1)}</Badge>;
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

  // Ticket Detail View
  if (selectedTicket) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => setSelectedTicket(null)}>
            <ArrowLeft size={18} className="mr-2" /> Back to Tickets
          </Button>
          <div className="flex gap-2">
            {selectedTicket.status !== 'in_progress' && selectedTicket.status !== 'closed' && (
              <Button size="sm" variant="outline" onClick={() => handleStatusChange('in_progress')} disabled={submitting}>
                Mark In Progress
              </Button>
            )}
            {selectedTicket.status !== 'closed' && (
              <Button size="sm" variant="default" onClick={() => handleStatusChange('closed')} disabled={submitting} className="bg-green-600 hover:bg-green-700">
                Mark Closed
              </Button>
            )}
            {selectedTicket.status === 'closed' && (
              <Button size="sm" variant="outline" onClick={() => handleStatusChange('open')} disabled={submitting}>
                Reopen Ticket
              </Button>
            )}
          </div>
        </div>

        <Card className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="text-xl font-semibold">{selectedTicket.subject}</h2>
              <p className="text-sm text-muted-foreground mt-1">
                From: {selectedTicket.therapist_name} ({selectedTicket.therapist_email})
              </p>
              <div className="flex gap-2 mt-2">
                {getStatusBadge(selectedTicket.status)}
                {getPriorityBadge(selectedTicket.priority)}
                <Badge variant="outline">{selectedTicket.category}</Badge>
              </div>
            </div>
            <span className="text-sm text-muted-foreground">{formatDate(selectedTicket.created_at)}</span>
          </div>
          
          <div className="bg-muted/30 p-4 rounded-lg mb-6 border-l-4 border-muted">
            <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
              <User size={14} /> {selectedTicket.therapist_name}
            </div>
            <p className="whitespace-pre-wrap">{selectedTicket.description}</p>
          </div>

          {/* Replies */}
          <div className="space-y-4 mb-6">
            {selectedTicket.replies?.map((reply) => (
              <div 
                key={reply.id} 
                className={`p-4 rounded-lg ${
                  reply.author_role === 'super_admin' 
                    ? 'bg-primary/10 border-l-4 border-primary ml-8' 
                    : 'bg-muted/50 mr-8'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {reply.author_role === 'super_admin' ? (
                    <Shield size={16} className="text-primary" />
                  ) : (
                    <User size={16} />
                  )}
                  <span className="font-medium text-sm">{reply.author_name}</span>
                  <span className="text-xs text-muted-foreground">{formatDate(reply.created_at)}</span>
                </div>
                <p className="text-sm whitespace-pre-wrap">{reply.message}</p>
              </div>
            ))}
          </div>

          {/* Reply Form */}
          {selectedTicket.status !== 'closed' && (
            <div className="border-t pt-4">
              <Label>Reply to Therapist</Label>
              <Textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="Type your response..."
                rows={4}
                className="mt-2"
                data-testid="admin-reply-input"
              />
              <Button 
                onClick={handleReply} 
                disabled={submitting || !replyText.trim()} 
                className="mt-3 gap-2"
                data-testid="send-reply-btn"
              >
                <Send size={16} /> {submitting ? 'Sending...' : 'Send Reply'}
              </Button>
            </div>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Support Tickets</h1>
          <p className="text-muted-foreground">Manage therapist support requests</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4 text-center bg-blue-50 border-blue-200">
          <p className="text-2xl font-bold text-blue-700">{stats.open}</p>
          <p className="text-sm text-blue-600">Open</p>
        </Card>
        <Card className="p-4 text-center bg-amber-50 border-amber-200">
          <p className="text-2xl font-bold text-amber-700">{stats.in_progress}</p>
          <p className="text-sm text-amber-600">In Progress</p>
        </Card>
        <Card className="p-4 text-center bg-green-50 border-green-200">
          <p className="text-2xl font-bold text-green-700">{stats.closed}</p>
          <p className="text-sm text-green-600">Closed</p>
        </Card>
        <Card className="p-4 text-center bg-slate-50 border-slate-200">
          <p className="text-2xl font-bold text-slate-700">{stats.total}</p>
          <p className="text-sm text-slate-600">Total</p>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <Filter size={18} className="text-muted-foreground" />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm"
        >
          <option value="">All Status</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="closed">Closed</option>
        </select>
        <select
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value)}
          className="h-9 px-3 rounded-md border border-input bg-background text-sm"
        >
          <option value="">All Priority</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Tickets List */}
      {loading ? (
        <div className="text-center py-12">Loading...</div>
      ) : tickets.length === 0 ? (
        <Card className="p-12 text-center">
          <MessageSquare size={48} className="mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No tickets found</h3>
          <p className="text-muted-foreground">No support tickets match your filters</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {tickets.map((ticket) => (
            <Card 
              key={ticket.id} 
              className={`p-4 hover:bg-muted/30 cursor-pointer transition-colors ${
                ticket.priority === 'high' && ticket.status !== 'closed' ? 'border-l-4 border-l-red-500' : ''
              }`}
              onClick={() => fetchTicketDetails(ticket.id)}
              data-testid={`admin-ticket-${ticket.id}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {ticket.priority === 'high' && ticket.status !== 'closed' && (
                      <AlertTriangle size={16} className="text-red-500" />
                    )}
                    <h3 className="font-medium">{ticket.subject}</h3>
                    {ticket.replies?.length > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {ticket.replies.length} replies
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {ticket.therapist_name} • {ticket.therapist_email}
                  </p>
                  <div className="flex items-center gap-2 text-sm">
                    {getStatusBadge(ticket.status)}
                    {getPriorityBadge(ticket.priority)}
                    <span className="text-muted-foreground">
                      <Clock size={14} className="inline mr-1" />
                      {formatDate(ticket.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AdminSupportTickets;
