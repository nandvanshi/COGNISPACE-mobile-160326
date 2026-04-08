import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { RefreshCw, Copy, Check, Eye, EyeOff, Shield } from 'lucide-react';
import { toast } from 'sonner';

const SystemConfig = () => {
  const [vars, setVars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [revealed, setRevealed] = useState({});
  const [copiedKey, setCopiedKey] = useState(null);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/admin/system-config`);
      setVars(data.variables);
    } catch {
      toast.error('Failed to load config');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchConfig(); }, []);

  const isSensitive = (key) => {
    const sensitive = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'AUTH', 'MONGO_URL'];
    return sensitive.some(s => key.toUpperCase().includes(s));
  };

  const toggleReveal = (key) => setRevealed(prev => ({ ...prev, [key]: !prev[key] }));

  const revealAll = () => {
    const allRevealed = vars.every(v => revealed[v.key]);
    if (allRevealed) {
      setRevealed({});
    } else {
      const all = {};
      vars.forEach(v => { all[v.key] = true; });
      setRevealed(all);
    }
  };

  const copyValue = (value, key) => {
    navigator.clipboard.writeText(value);
    setCopiedKey(key);
    toast.success('Copied!');
    setTimeout(() => setCopiedKey(null), 1500);
  };

  const maskValue = (val) => {
    if (val.length <= 6) return '*'.repeat(val.length);
    return val.slice(0, 3) + '*'.repeat(Math.min(val.length - 6, 20)) + val.slice(-3);
  };

  return (
    <div data-testid="system-config-view">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-serif text-primary" data-testid="system-config-title">System Configuration</h2>
          <p className="text-sm text-muted-foreground mt-1">Backend environment variables (.env)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={revealAll} data-testid="toggle-all-btn">
            {vars.every(v => revealed[v.key]) ? <EyeOff size={16} /> : <Eye size={16} />}
            <span className="ml-2">{vars.every(v => revealed[v.key]) ? 'Hide All' : 'Show All'}</span>
          </Button>
          <Button variant="outline" size="sm" onClick={fetchConfig} data-testid="refresh-config-btn">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            <span className="ml-2">Refresh</span>
          </Button>
        </div>
      </div>

      <Card className="overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">Loading...</div>
        ) : (
          <div className="divide-y divide-border">
            {vars.map((v) => {
              const sensitive = isSensitive(v.key);
              const isRevealed = revealed[v.key] || !sensitive;
              return (
                <div key={v.key} className="flex items-center gap-4 px-4 py-3 hover:bg-muted/20 transition-colors" data-testid={`config-row-${v.key}`}>
                  <div className="w-[280px] shrink-0 flex items-center gap-2">
                    {sensitive && <Shield size={14} className="text-amber-500" />}
                    <span className="font-mono text-sm font-semibold text-foreground">{v.key}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className={`font-mono text-sm break-all ${sensitive && !isRevealed ? 'text-muted-foreground' : 'text-foreground'}`}>
                      {isRevealed ? v.value : maskValue(v.value)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {sensitive && (
                      <button
                        onClick={() => toggleReveal(v.key)}
                        className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                        data-testid={`reveal-${v.key}`}
                      >
                        {isRevealed ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    )}
                    <button
                      onClick={() => copyValue(v.value, v.key)}
                      className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                      data-testid={`copy-${v.key}`}
                    >
                      {copiedKey === v.key ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>
    </div>
  );
};

export default SystemConfig;
