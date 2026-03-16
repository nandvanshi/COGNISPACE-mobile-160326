import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { Calendar as CalendarWidget } from './ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { toast } from 'sonner';
import {
  CalendarPlus, Calendar, Users, AlertTriangle, Clock,
  CheckCircle2, UserX, TrendingUp, Loader2, RefreshCw,
  Phone, Mail, ArrowRight, BarChart3
} from 'lucide-react';

const statusConfig = {
  overdue: { label: 'Overdue', color: 'text-red-600', bg: 'bg-red-50 border-red-200', badge: 'bg-red-100 text-red-700' },
  dropout_risk: { label: 'Dropout Risk', color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200', badge: 'bg-orange-100 text-orange-700' },
  recommended: { label: 'Recommended', color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200', badge: 'bg-blue-100 text-blue-700' },
  booked: { label: 'Booked', color: 'text-green-600', bg: 'bg-green-50 border-green-200', badge: 'bg-green-100 text-green-700' },
  no_recommendation: { label: 'No Follow-Up', color: 'text-gray-500', bg: 'bg-gray-50 border-gray-200', badge: 'bg-gray-100 text-gray-600' },
};

const FollowUpDashboard = ({ onNavigateToClient }) => {
  const [summary, setSummary] = useState(null);
  const [clients, setClients] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showRecommendDialog, setShowRecommendDialog] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [recDate, setRecDate] = useState(null);
  const [recNotes, setRecNotes] = useState('');
  const [recCalOpen, setRecCalOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [sumRes, cliRes] = await Promise.all([
        axios.get(`${API}/follow-ups/summary`),
        axios.get(`${API}/follow-ups/clients`)
      ]);
      setSummary(sumRes.data);
      setClients(cliRes.data);
    } catch (err) {
      console.error('Follow-up fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      const [basicRes, detailedRes] = await Promise.all([
        axios.get(`${API}/follow-ups/retention-analytics`),
        axios.get(`${API}/follow-ups/retention-analytics/detailed`)
      ]);
      setAnalytics({ ...basicRes.data, ...detailedRes.data });
    } catch (err) {
      console.error('Analytics fetch error:', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (activeTab === 'analytics') fetchAnalytics();
  }, [activeTab, fetchAnalytics]);

  const handleRecommend = async () => {
    if (!selectedClient || !recDate) return;
    setSaving(true);
    try {
      await axios.post(`${API}/follow-ups/recommend`, {
        client_id: selectedClient.client_id,
        recommended_date: recDate.toISOString().split('T')[0],
        notes: recNotes
      });
      toast.success('Follow-up recommendation saved');
      setShowRecommendDialog(false);
      setSelectedClient(null);
      setRecDate(null);
      setRecNotes('');
      fetchData();
    } catch (err) {
      toast.error('Failed to save recommendation');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="follow-up-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Follow-Up Intelligence</h2>
          <p className="text-sm text-muted-foreground mt-1">Track client follow-ups and retention</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} data-testid="refresh-followups">
          <RefreshCw size={14} className="mr-1" /> Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="followup-summary-cards">
          <Card className="p-4 border-l-4 border-l-green-500">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle2 size={14} /> Booked
            </div>
            <p className="text-2xl font-bold mt-1" data-testid="stat-booked">{summary.booked}</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-blue-500">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar size={14} /> Recommended
            </div>
            <p className="text-2xl font-bold mt-1" data-testid="stat-recommended">{summary.recommended}</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-red-500">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertTriangle size={14} /> Overdue
            </div>
            <p className="text-2xl font-bold mt-1" data-testid="stat-overdue">{summary.overdue}</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-orange-500">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <UserX size={14} /> Dropout Risk
            </div>
            <p className="text-2xl font-bold mt-1" data-testid="stat-dropout">{summary.dropout_risk}</p>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b pb-2">
        {[
          { id: 'overview', label: 'Client List', icon: Users },
          { id: 'analytics', label: 'Retention Analytics', icon: BarChart3 }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-t-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-primary/10 text-primary font-medium border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
            data-testid={`followup-tab-${tab.id}`}
          >
            <tab.icon size={14} /> {tab.label}
          </button>
        ))}
      </div>

      {/* Client List Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-3" data-testid="followup-client-list">
          {clients.length === 0 ? (
            <Card className="p-8 text-center text-muted-foreground">
              <Users size={40} className="mx-auto mb-3 opacity-50" />
              <p>No follow-up data yet</p>
              <p className="text-xs mt-1">Complete sessions and set recommendations to see data here</p>
            </Card>
          ) : (
            clients.map(client => {
              const cfg = statusConfig[client.status] || statusConfig.no_recommendation;
              return (
                <Card
                  key={client.client_id}
                  className={`p-4 border ${cfg.bg} transition-all hover:shadow-md`}
                  data-testid={`followup-client-${client.client_id}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-medium truncate">{client.client_name}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${cfg.badge}`} data-testid={`status-badge-${client.client_id}`}>
                          {cfg.label}
                        </span>
                        {client.is_dropout_risk && client.status !== 'dropout_risk' && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">
                            Dropout Risk
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-muted-foreground">
                        {client.days_since_last_session !== null && (
                          <span className="flex items-center gap-1">
                            <Clock size={12} /> Last session: {client.days_since_last_session} days ago
                          </span>
                        )}
                        {client.recommended_date && (
                          <span className="flex items-center gap-1">
                            <Calendar size={12} /> Recommended: {new Date(client.recommended_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                          </span>
                        )}
                        {client.upcoming_appointment && (
                          <span className="flex items-center gap-1 text-green-600">
                            <CheckCircle2 size={12} /> Next: {new Date(client.upcoming_appointment).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                          </span>
                        )}
                      </div>
                      {client.recommendation_notes && (
                        <p className="text-xs text-muted-foreground mt-1 italic">"{client.recommendation_notes}"</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {client.status !== 'booked' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => { setSelectedClient(client); setShowRecommendDialog(true); }}
                          className="text-xs"
                          data-testid={`recommend-btn-${client.client_id}`}
                        >
                          <CalendarPlus size={12} className="mr-1" /> Recommend
                        </Button>
                      )}
                      {onNavigateToClient && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onNavigateToClient(client.client_id)}
                          data-testid={`view-client-${client.client_id}`}
                        >
                          <ArrowRight size={14} />
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="space-y-4" data-testid="followup-analytics">
          {!analytics ? (
            <div className="flex justify-center py-10">
              <Loader2 className="animate-spin" size={24} />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <Card className="p-4 text-center">
                  <p className="text-sm text-muted-foreground">Total Clients</p>
                  <p className="text-3xl font-bold mt-1">{analytics.total_clients}</p>
                </Card>
                <Card className="p-4 text-center">
                  <p className="text-sm text-muted-foreground">Retention Rate</p>
                  <p className="text-3xl font-bold mt-1 text-green-600">{analytics.retention_rate}%</p>
                </Card>
                <Card className="p-4 text-center">
                  <p className="text-sm text-muted-foreground">Active Clients</p>
                  <p className="text-3xl font-bold mt-1 text-blue-600">{analytics.active_clients}</p>
                </Card>
              </div>

              <Card className="p-4">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <TrendingUp size={16} /> Monthly Sessions (Last 6 Months)
                </h3>
                <div className="flex items-end gap-2 h-32">
                  {analytics.monthly_sessions?.map((m, i) => {
                    const maxSessions = Math.max(...analytics.monthly_sessions.map(s => s.sessions), 1);
                    const height = (m.sessions / maxSessions) * 100;
                    return (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-xs font-medium">{m.sessions}</span>
                        <div
                          className="w-full bg-primary/70 rounded-t transition-all"
                          style={{ height: `${Math.max(height, 4)}%` }}
                        />
                        <span className="text-[10px] text-muted-foreground">{m.month.split(' ')[0]}</span>
                      </div>
                    );
                  })}
                </div>
              </Card>

              <div className="grid grid-cols-2 gap-3">
                <Card className="p-4 border-l-4 border-l-red-400">
                  <p className="text-sm text-muted-foreground">Overdue</p>
                  <p className="text-2xl font-bold text-red-600">{analytics.overdue_clients}</p>
                </Card>
                <Card className="p-4 border-l-4 border-l-orange-400">
                  <p className="text-sm text-muted-foreground">Dropout Risk</p>
                  <p className="text-2xl font-bold text-orange-600">{analytics.dropout_risk_clients}</p>
                </Card>
              </div>

              {/* Detailed Client Metrics */}
              {analytics.avg_sessions_per_client != null && (
                <div className="grid grid-cols-2 gap-3">
                  <Card className="p-4 text-center border-l-4 border-l-indigo-400">
                    <p className="text-sm text-muted-foreground">Avg Sessions/Client</p>
                    <p className="text-2xl font-bold text-indigo-600">{analytics.avg_sessions_per_client}</p>
                  </Card>
                  <Card className="p-4 text-center border-l-4 border-l-teal-400">
                    <p className="text-sm text-muted-foreground">Avg Gap (days)</p>
                    <p className="text-2xl font-bold text-teal-600">{analytics.avg_gap_between_sessions ?? '-'}</p>
                  </Card>
                </div>
              )}

              {/* Per-Client Retention Table */}
              {analytics.client_details?.length > 0 && (
                <Card className="p-4">
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <Users size={16} /> Client Retention Details
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs text-muted-foreground border-b">
                          <th className="text-left py-2 pr-3">Client</th>
                          <th className="text-center py-2 px-2">Sessions</th>
                          <th className="text-center py-2 px-2">Avg Gap</th>
                          <th className="text-center py-2 pl-2">Last Visit</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.client_details.map((cd, i) => (
                          <tr key={i} className="border-b border-dashed last:border-0 hover:bg-muted/30">
                            <td className="py-2 pr-3">
                              <div className="flex items-center gap-2">
                                <span className="font-medium truncate max-w-[120px]">{cd.client_name}</span>
                                {cd.days_since_last_session > 30 && (
                                  <span className="text-[10px] px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded-full">At Risk</span>
                                )}
                              </div>
                            </td>
                            <td className="text-center py-2 px-2 font-medium">{cd.session_count}</td>
                            <td className="text-center py-2 px-2 text-muted-foreground">{cd.avg_gap_days ? `${cd.avg_gap_days}d` : '-'}</td>
                            <td className="text-center py-2 pl-2">
                              <span className={cd.days_since_last_session > 14 ? 'text-red-600' : 'text-green-600'}>
                                {cd.days_since_last_session}d ago
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {/* Recommend Dialog */}
      <Dialog open={showRecommendDialog} onOpenChange={setShowRecommendDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CalendarPlus size={20} className="text-primary" /> Recommend Next Session
            </DialogTitle>
          </DialogHeader>

          {selectedClient && (
            <Card className="p-3 bg-muted/30">
              <p className="font-medium">{selectedClient.client_name}</p>
              {selectedClient.days_since_last_session !== null && (
                <p className="text-xs text-muted-foreground">Last session: {selectedClient.days_since_last_session} days ago</p>
              )}
            </Card>
          )}

          <div>
            <Label>Recommended Date</Label>
            <Popover open={recCalOpen} onOpenChange={setRecCalOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full mt-1 justify-start text-left font-normal" data-testid="dialog-followup-date">
                  <Calendar size={14} className="mr-2" />
                  {recDate ? recDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Select date'}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <CalendarWidget
                  mode="single"
                  selected={recDate}
                  onSelect={(d) => { setRecDate(d); setRecCalOpen(false); }}
                  disabled={(date) => date < new Date()}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          <div>
            <Label>Notes (optional)</Label>
            <Input
              value={recNotes}
              onChange={(e) => setRecNotes(e.target.value)}
              placeholder="e.g., Weekly CBT session..."
              className="mt-1"
              data-testid="dialog-followup-notes"
            />
          </div>

          <div className="flex gap-2">
            <Button onClick={handleRecommend} disabled={saving || !recDate} className="flex-1" data-testid="save-recommendation-btn">
              {saving ? <Loader2 className="animate-spin mr-2" size={16} /> : <CalendarPlus size={16} className="mr-2" />}
              Save Recommendation
            </Button>
            <Button variant="outline" onClick={() => setShowRecommendDialog(false)}>Cancel</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FollowUpDashboard;
