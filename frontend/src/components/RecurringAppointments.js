import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { toast } from 'sonner';
import { Plus, Repeat, Trash2, Play, Pause, Calendar, Clock, User } from 'lucide-react';

const DAYS_OF_WEEK = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
];

const RecurringAppointments = ({ isReadOnly = false }) => {
  const [patterns, setPatterns] = useState([]);
  const [clients, setClients] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newPattern, setNewPattern] = useState({
    client_id: '',
    day_of_week: 0,
    start_time: '09:00',
    end_time: '10:00',
    notes: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
  });
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [patternsRes, clientsRes] = await Promise.all([
        axios.get(`${API}/recurring-appointments`),
        axios.get(`${API}/clients`),
      ]);
      setPatterns(patternsRes.data);
      setClients(clientsRes.data);
    } catch (error) {
      toast.error('Failed to load recurring appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePattern = async (e) => {
    e.preventDefault();

    if (!newPattern.client_id) {
      toast.error('Please select a client');
      return;
    }

    try {
      await axios.post(`${API}/recurring-appointments`, {
        client_id: newPattern.client_id,
        day_of_week: parseInt(newPattern.day_of_week),
        start_time: newPattern.start_time,
        end_time: newPattern.end_time,
        notes: newPattern.notes,
        start_date: newPattern.start_date,
        end_date: newPattern.end_date || null,
      });
      toast.success('Recurring appointment pattern created');
      setShowCreateDialog(false);
      resetNewPattern();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create pattern');
    }
  };

  const handleDeletePattern = async (patternId) => {
    if (!window.confirm('Are you sure you want to delete this recurring pattern?')) return;

    try {
      await axios.delete(`${API}/recurring-appointments/${patternId}`);
      toast.success('Pattern deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete pattern');
    }
  };

  const handleTogglePattern = async (patternId) => {
    try {
      const response = await axios.put(`${API}/recurring-appointments/${patternId}/toggle`);
      toast.success(response.data.message);
      fetchData();
    } catch (error) {
      toast.error('Failed to toggle pattern');
    }
  };

  const handleGenerateAppointments = async (patternId, weeks = 4) => {
    setGenerating(patternId);
    try {
      const response = await axios.post(
        `${API}/recurring-appointments/${patternId}/generate?weeks_ahead=${weeks}`
      );
      toast.success(response.data.message);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate appointments');
    } finally {
      setGenerating(null);
    }
  };

  const resetNewPattern = () => {
    setNewPattern({
      client_id: '',
      day_of_week: 0,
      start_time: '09:00',
      end_time: '10:00',
      notes: '',
      start_date: new Date().toISOString().split('T')[0],
      end_date: '',
    });
  };

  if (loading) {
    return <div className="text-center py-12">Loading recurring patterns...</div>;
  }

  return (
    <div data-testid="recurring-appointments">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Recurring Appointments</h2>
          <p className="text-muted-foreground">Set up weekly recurring sessions with clients</p>
        </div>
        {!isReadOnly && (
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="create-pattern-button"
          >
            <Plus size={20} className="mr-2" />
            New Pattern
          </Button>
        )}
      </div>

      {/* Info Card */}
      <Card className="p-4 mb-6 bg-info/10 border-info/30">
        <div className="flex items-start gap-3">
          <Repeat size={20} className="text-info mt-0.5" />
          <div>
            <p className="font-medium text-foreground">How Recurring Appointments Work</p>
            <p className="text-sm text-muted-foreground mt-1">
              1. Create a pattern specifying the day, time, and client.<br />
              2. Click "Generate" to create appointments for the next 4 weeks.<br />
              3. Generated appointments appear in your regular calendar.<br />
              4. You can pause or delete patterns anytime.
            </p>
          </div>
        </div>
      </Card>

      {/* Patterns List */}
      <div className="space-y-4">
        {patterns.map((pattern) => (
          <Card
            key={pattern.id}
            className={`p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl ${
              !pattern.is_active ? 'opacity-60' : ''
            }`}
            data-testid={`pattern-${pattern.id}`}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Repeat size={24} className="text-primary" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-medium text-lg text-foreground">{pattern.client_name}</p>
                    {!pattern.is_active && (
                      <span className="px-2 py-0.5 rounded text-xs bg-muted text-muted-foreground">
                        Paused
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <Calendar size={14} />
                    Every {DAYS_OF_WEEK.find(d => d.value === pattern.day_of_week)?.label}
                    <Clock size={14} className="ml-2" />
                    {pattern.start_time} - {pattern.end_time}
                  </p>
                  {pattern.notes && (
                    <p className="text-sm text-muted-foreground mt-1">{pattern.notes}</p>
                  )}
                  <p className="text-xs text-muted-foreground mt-2">
                    Starts: {new Date(pattern.start_date).toLocaleDateString()}
                    {pattern.end_date && ` • Ends: ${new Date(pattern.end_date).toLocaleDateString()}`}
                  </p>
                </div>
              </div>

              {!isReadOnly && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleGenerateAppointments(pattern.id)}
                    disabled={!pattern.is_active || generating === pattern.id}
                    data-testid={`generate-${pattern.id}`}
                  >
                    {generating === pattern.id ? (
                      'Generating...'
                    ) : (
                      <>
                        <Play size={14} className="mr-1" />
                        Generate
                      </>
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleTogglePattern(pattern.id)}
                    className={pattern.is_active ? 'text-warning' : 'text-success'}
                    data-testid={`toggle-${pattern.id}`}
                  >
                    {pattern.is_active ? <Pause size={16} /> : <Play size={16} />}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeletePattern(pattern.id)}
                    className="text-error hover:text-error hover:bg-error/10"
                    data-testid={`delete-${pattern.id}`}
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              )}
            </div>
          </Card>
        ))}

        {patterns.length === 0 && (
          <div className="text-center py-12">
            <Repeat size={48} className="mx-auto text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground">No recurring patterns set up</p>
            {!isReadOnly && (
              <Button
                onClick={() => setShowCreateDialog(true)}
                variant="outline"
                className="mt-4"
              >
                Create your first pattern
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Create Pattern Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent data-testid="create-pattern-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">
              New Recurring Pattern
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreatePattern} className="space-y-4">
            <div>
              <Label>Client *</Label>
              <Select
                value={newPattern.client_id}
                onValueChange={(value) => setNewPattern({ ...newPattern, client_id: value })}
              >
                <SelectTrigger className="mt-1" data-testid="pattern-client-select">
                  <SelectValue placeholder="Select a client" />
                </SelectTrigger>
                <SelectContent>
                  {clients.map((client) => (
                    <SelectItem key={client.id} value={client.id}>
                      {client.full_name} ({client.client_id})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Day of Week *</Label>
              <Select
                value={newPattern.day_of_week.toString()}
                onValueChange={(value) => setNewPattern({ ...newPattern, day_of_week: parseInt(value) })}
              >
                <SelectTrigger className="mt-1" data-testid="pattern-day-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DAYS_OF_WEEK.map((day) => (
                    <SelectItem key={day.value} value={day.value.toString()}>
                      {day.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Start Time *</Label>
                <Input
                  type="time"
                  value={newPattern.start_time}
                  onChange={(e) => setNewPattern({ ...newPattern, start_time: e.target.value })}
                  required
                  className="mt-1"
                  data-testid="pattern-start-time"
                />
              </div>
              <div>
                <Label>End Time *</Label>
                <Input
                  type="time"
                  value={newPattern.end_time}
                  onChange={(e) => setNewPattern({ ...newPattern, end_time: e.target.value })}
                  required
                  className="mt-1"
                  data-testid="pattern-end-time"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Start Date *</Label>
                <Input
                  type="date"
                  value={newPattern.start_date}
                  onChange={(e) => setNewPattern({ ...newPattern, start_date: e.target.value })}
                  required
                  className="mt-1"
                  data-testid="pattern-start-date"
                />
              </div>
              <div>
                <Label>End Date (optional)</Label>
                <Input
                  type="date"
                  value={newPattern.end_date}
                  onChange={(e) => setNewPattern({ ...newPattern, end_date: e.target.value })}
                  className="mt-1"
                  data-testid="pattern-end-date"
                />
              </div>
            </div>

            <div>
              <Label>Notes (optional)</Label>
              <Input
                value={newPattern.notes}
                onChange={(e) => setNewPattern({ ...newPattern, notes: e.target.value })}
                placeholder="e.g., Weekly check-in, CBT session"
                className="mt-1"
                data-testid="pattern-notes"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1" data-testid="save-pattern-button">
                Create Pattern
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateDialog(false);
                  resetNewPattern();
                }}
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RecurringAppointments;
