import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { RefreshCw, Clock, GitCommit } from 'lucide-react';
import { toast } from 'sonner';

const UpdateLog = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLog = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/update-log`);
      setEntries(data.entries || []);
    } catch {
      toast.error('Failed to load update log');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLog(); }, []);

  const formatTimestamp = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: true,
        timeZone: 'Asia/Kolkata'
      });
    } catch {
      return ts;
    }
  };

  const getDateLabel = (ts) => {
    try {
      return new Date(ts).toLocaleDateString('en-IN', {
        day: '2-digit', month: 'long', year: 'numeric',
        timeZone: 'Asia/Kolkata'
      });
    } catch {
      return '';
    }
  };

  // Group entries by date
  const grouped = entries.reduce((acc, entry) => {
    const label = getDateLabel(entry.timestamp);
    if (!acc[label]) acc[label] = [];
    acc[label].push(entry);
    return acc;
  }, {});

  return (
    <div data-testid="update-log-view">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-serif text-primary" data-testid="update-log-title">Update Log</h2>
          <p className="text-sm text-muted-foreground mt-1">All code updates with timestamps</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchLog} data-testid="refresh-log-btn">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {loading ? (
        <div className="py-12 text-center text-muted-foreground">Loading...</div>
      ) : entries.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">No updates logged yet</Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([dateLabel, dateEntries]) => (
            <div key={dateLabel}>
              <div className="flex items-center gap-2 mb-3">
                <div className="h-px flex-1 bg-border" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2">{dateLabel}</span>
                <div className="h-px flex-1 bg-border" />
              </div>
              <div className="space-y-2 ml-4 border-l-2 border-primary/20 pl-4">
                {dateEntries.map((entry, idx) => (
                  <div key={idx} className="relative" data-testid={`log-entry-${idx}`}>
                    <div className="absolute -left-[21px] top-1.5 w-2.5 h-2.5 rounded-full bg-primary border-2 border-white" />
                    <Card className="p-3 hover:shadow-sm transition-shadow">
                      <div className="flex items-start gap-3">
                        <GitCommit size={16} className="text-primary mt-0.5 shrink-0" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-foreground">{entry.note}</p>
                          <div className="flex items-center gap-1 mt-1">
                            <Clock size={11} className="text-muted-foreground" />
                            <span className="text-xs text-muted-foreground font-mono">{formatTimestamp(entry.timestamp)}</span>
                          </div>
                        </div>
                      </div>
                    </Card>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Card className="mt-6 p-4 bg-muted/30 border-dashed">
        <p className="text-xs text-muted-foreground">
          <strong>How to add entries:</strong> Edit <code className="bg-muted px-1 py-0.5 rounded text-[11px]">/backend/update_log.txt</code> and add a new line at the top:
        </p>
        <pre className="mt-2 text-[11px] font-mono bg-muted p-2 rounded overflow-x-auto">
          2026-04-21T10:30:00+05:30 | Your update description here
        </pre>
      </Card>
    </div>
  );
};

export default UpdateLog;
