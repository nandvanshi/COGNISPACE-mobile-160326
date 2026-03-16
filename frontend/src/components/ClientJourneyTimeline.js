import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import {
  Calendar, FileText, ClipboardList, Bell, CheckCircle2,
  XCircle, AlertTriangle, CalendarPlus, Loader2, Clock,
  TrendingUp, BarChart3
} from 'lucide-react';

const typeConfig = {
  session: { icon: Calendar, label: 'Session', getColor: (s) => s === 'completed' ? 'bg-green-100 text-green-700 border-green-200' : s === 'cancelled' ? 'bg-red-100 text-red-700 border-red-200' : 'bg-yellow-100 text-yellow-700 border-yellow-200' },
  recommendation: { icon: CalendarPlus, label: 'Follow-Up Recommendation', getColor: () => 'bg-blue-100 text-blue-700 border-blue-200' },
  note: { icon: FileText, label: 'Session Note', getColor: () => 'bg-purple-100 text-purple-700 border-purple-200' },
  assessment: { icon: ClipboardList, label: 'Assessment', getColor: (s) => s === 'completed' ? 'bg-green-100 text-green-700 border-green-200' : 'bg-indigo-100 text-indigo-700 border-indigo-200' },
  reminder_sent: { icon: Bell, label: 'Reminder Sent', getColor: () => 'bg-amber-100 text-amber-700 border-amber-200' },
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime()) || d.getFullYear() < 2000) return '';
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch { return ''; }
};

const ClientJourneyTimeline = ({ clientId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!clientId) return;
    const fetch = async () => {
      try {
        const res = await axios.get(`${API}/follow-ups/journey/${clientId}`);
        setData(res.data);
      } catch (e) {
        console.error('Journey fetch error:', e);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [clientId]);

  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <Loader2 className="animate-spin text-primary" size={24} />
      </div>
    );
  }

  if (!data || !data.timeline?.length) {
    return (
      <Card className="p-6 text-center text-muted-foreground" data-testid="journey-empty">
        <Clock size={36} className="mx-auto mb-3 opacity-40" />
        <p className="text-sm">No journey data yet</p>
        <p className="text-xs mt-1">Events will appear here as sessions are completed</p>
      </Card>
    );
  }

  const { stats, timeline } = data;

  return (
    <div className="space-y-4" data-testid="client-journey-timeline">
      {/* Stats Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <Card className="p-3 text-center">
          <p className="text-xl font-bold text-green-600">{stats.total_sessions}</p>
          <p className="text-[11px] text-muted-foreground">Sessions</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xl font-bold text-blue-600">{stats.total_recommendations}</p>
          <p className="text-[11px] text-muted-foreground">Follow-Ups</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xl font-bold text-purple-600">{stats.total_assessments}</p>
          <p className="text-[11px] text-muted-foreground">Assessments</p>
        </Card>
        <Card className="p-3 text-center">
          <p className="text-xl font-bold text-amber-600">{stats.avg_gap_days ?? '-'}</p>
          <p className="text-[11px] text-muted-foreground">Avg Gap (days)</p>
        </Card>
      </div>

      {stats.journey_duration_days > 0 && stats.first_session_date && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
          <TrendingUp size={12} />
          <span>Journey: {stats.journey_duration_days} days since {formatDate(stats.first_session_date)}</span>
        </div>
      )}

      {/* Timeline */}
      <div className="relative pl-6 border-l-2 border-gray-200 space-y-3">
        {timeline.filter(e => formatDate(e.date)).map((event, idx) => {
          const cfg = typeConfig[event.type] || typeConfig.session;
          const Icon = cfg.icon;
          const colorClass = cfg.getColor(event.status);

          return (
            <div key={idx} className="relative" data-testid={`timeline-event-${idx}`}>
              {/* Dot on timeline */}
              <div className={`absolute -left-[25px] w-3 h-3 rounded-full border-2 ${
                event.type === 'session' && event.status === 'completed' ? 'bg-green-500 border-green-300' :
                event.type === 'session' && event.status === 'cancelled' ? 'bg-red-400 border-red-300' :
                event.type === 'recommendation' ? 'bg-blue-500 border-blue-300' :
                event.type === 'reminder_sent' ? 'bg-amber-500 border-amber-300' :
                'bg-gray-400 border-gray-300'
              }`} />

              <div className={`p-3 rounded-lg border ${colorClass} transition-all hover:shadow-sm`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <Icon size={14} className="shrink-0" />
                    <span className="text-xs font-medium">{cfg.label}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap">{formatDate(event.date)}</span>
                </div>

                {/* Event-specific details */}
                {event.type === 'session' && (
                  <div className="mt-1 flex items-center gap-2 text-xs">
                    {event.status === 'completed' && <CheckCircle2 size={12} className="text-green-600" />}
                    {event.status === 'cancelled' && <XCircle size={12} className="text-red-500" />}
                    {event.status === 'no_show' && <AlertTriangle size={12} className="text-yellow-600" />}
                    <span className="capitalize">{event.status}</span>
                    {event.duration_minutes && <span className="text-muted-foreground">({event.duration_minutes} min)</span>}
                    {event.session_type && <span className="text-muted-foreground capitalize">{event.session_type}</span>}
                  </div>
                )}

                {event.type === 'recommendation' && (
                  <div className="mt-1 text-xs">
                    <span>For: {formatDate(event.recommended_date)}</span>
                    {event.notes && <span className="text-muted-foreground ml-2 italic">- {event.notes}</span>}
                    {event.status === 'fulfilled' && <span className="text-green-600 ml-1">(Booked)</span>}
                  </div>
                )}

                {event.type === 'assessment' && (
                  <div className="mt-1 text-xs">
                    {event.title && <span>{event.title}</span>}
                    {event.status && <span className="ml-1 capitalize text-muted-foreground">({event.status})</span>}
                  </div>
                )}

                {event.type === 'reminder_sent' && (
                  <div className="mt-1 text-xs text-muted-foreground">
                    {event.reminder_type?.replace(/_/g, ' ')} via {event.channel}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ClientJourneyTimeline;
