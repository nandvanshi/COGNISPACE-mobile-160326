import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Clock, Plus, Trash2, Calendar, Settings, Ban, Copy } from 'lucide-react';
import { formatDateWithDay, formatTime, formatTimeRange } from '../utils/formatUtils';

const DAYS = [
  { key: 'monday', label: 'Monday', short: 'Mon' },
  { key: 'tuesday', label: 'Tuesday', short: 'Tue' },
  { key: 'wednesday', label: 'Wednesday', short: 'Wed' },
  { key: 'thursday', label: 'Thursday', short: 'Thu' },
  { key: 'friday', label: 'Friday', short: 'Fri' },
  { key: 'saturday', label: 'Saturday', short: 'Sat' },
  { key: 'sunday', label: 'Sunday', short: 'Sun' },
];

const AvailabilitySettings = ({ isReadOnly = false }) => {
  const { user } = useAuth();
  const [availability, setAvailability] = useState(null);
  const [blockedTimes, setBlockedTimes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showBlockDialog, setShowBlockDialog] = useState(false);
  const [showCopyDialog, setShowCopyDialog] = useState(false);
  const [copySourceDay, setCopySourceDay] = useState(null);
  const [copyTargetDays, setCopyTargetDays] = useState({});
  const [newBlock, setNewBlock] = useState({
    start_datetime: '',
    end_datetime: '',
    reason: '',
    is_all_day: false,
  });

  // Only therapists can use copy feature (not assistants)
  const canUseCopyFeature = user?.role === 'therapist' && !isReadOnly;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [availRes, blockedRes] = await Promise.all([
        axios.get(`${API}/availability`),
        axios.get(`${API}/blocked-times`),
      ]);
      setAvailability(availRes.data);
      setBlockedTimes(blockedRes.data);
    } catch (error) {
      toast.error('Failed to load availability settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAvailability = async () => {
    if (!availability) return;
    setSaving(true);

    try {
      const payload = {
        session_duration: availability.session_duration,
        buffer_time: availability.buffer_time,
      };

      DAYS.forEach((day) => {
        payload[day.key] = availability[day.key];
      });

      await axios.put(`${API}/availability`, payload);
      toast.success('Availability settings saved');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleDayToggle = (dayKey, enabled) => {
    setAvailability((prev) => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        enabled,
      },
    }));
  };

  const handleAddTimeBlock = (dayKey) => {
    setAvailability((prev) => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        time_blocks: [
          ...prev[dayKey].time_blocks,
          { start_time: '09:00', end_time: '17:00' },
        ],
      },
    }));
  };

  const handleRemoveTimeBlock = (dayKey, index) => {
    setAvailability((prev) => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        time_blocks: prev[dayKey].time_blocks.filter((_, i) => i !== index),
      },
    }));
  };

  const handleTimeBlockChange = (dayKey, index, field, value) => {
    setAvailability((prev) => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        time_blocks: prev[dayKey].time_blocks.map((block, i) =>
          i === index ? { ...block, [field]: value } : block
        ),
      },
    }));
  };

  // Copy Day functionality
  const openCopyDialog = (dayKey) => {
    setCopySourceDay(dayKey);
    // Initialize all other days as unchecked
    const targets = {};
    DAYS.forEach(d => {
      if (d.key !== dayKey) {
        targets[d.key] = false;
      }
    });
    setCopyTargetDays(targets);
    setShowCopyDialog(true);
  };

  const handleCopyDay = () => {
    if (!copySourceDay || !availability) return;

    const sourceSchedule = availability[copySourceDay];
    const selectedTargets = Object.entries(copyTargetDays).filter(([_, selected]) => selected).map(([day]) => day);

    if (selectedTargets.length === 0) {
      toast.error('Please select at least one day to copy to');
      return;
    }

    // Check if any target day has existing schedules
    const daysWithSchedules = selectedTargets.filter(dayKey => {
      const daySchedule = availability[dayKey];
      return daySchedule?.enabled && daySchedule?.time_blocks?.length > 0;
    });

    if (daysWithSchedules.length > 0) {
      const dayLabels = daysWithSchedules.map(dk => DAYS.find(d => d.key === dk)?.label).join(', ');
      if (!window.confirm(`The following days have existing schedules that will be overwritten: ${dayLabels}. Continue?`)) {
        return;
      }
    }

    // Copy the schedule to selected days
    setAvailability((prev) => {
      const updated = { ...prev };
      selectedTargets.forEach(targetDay => {
        updated[targetDay] = {
          enabled: sourceSchedule.enabled,
          time_blocks: sourceSchedule.time_blocks.map(block => ({ ...block })), // Deep copy time blocks
        };
      });
      return updated;
    });

    const sourceDayLabel = DAYS.find(d => d.key === copySourceDay)?.label;
    toast.success(`${sourceDayLabel}'s schedule copied to ${selectedTargets.length} day(s)`);
    setShowCopyDialog(false);
    setCopySourceDay(null);
    setCopyTargetDays({});
  };

  const toggleTargetDay = (dayKey) => {
    setCopyTargetDays(prev => ({
      ...prev,
      [dayKey]: !prev[dayKey]
    }));
  };

  const selectAllTargets = () => {
    const allSelected = {};
    DAYS.forEach(d => {
      if (d.key !== copySourceDay) {
        allSelected[d.key] = true;
      }
    });
    setCopyTargetDays(allSelected);
  };

  const selectWeekdays = () => {
    const weekdays = {};
    DAYS.forEach(d => {
      if (d.key !== copySourceDay) {
        weekdays[d.key] = !['saturday', 'sunday'].includes(d.key);
      }
    });
    setCopyTargetDays(weekdays);
  };

  const handleCreateBlockedTime = async (e) => {
    e.preventDefault();

    if (!newBlock.start_datetime || !newBlock.end_datetime) {
      toast.error('Please fill in start and end times');
      return;
    }

    try {
      await axios.post(`${API}/blocked-times`, {
        start_datetime: new Date(newBlock.start_datetime).toISOString(),
        end_datetime: new Date(newBlock.end_datetime).toISOString(),
        reason: newBlock.reason,
        is_all_day: newBlock.is_all_day,
      });
      toast.success('Time blocked successfully');
      setShowBlockDialog(false);
      setNewBlock({ start_datetime: '', end_datetime: '', reason: '', is_all_day: false });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to block time');
    }
  };

  const handleDeleteBlockedTime = async (blockId) => {
    if (!window.confirm('Are you sure you want to remove this blocked time?')) return;

    try {
      await axios.delete(`${API}/blocked-times/${blockId}`);
      toast.success('Blocked time removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove blocked time');
    }
  };

  const getSourceDayInfo = () => {
    if (!copySourceDay || !availability) return null;
    const daySchedule = availability[copySourceDay];
    const dayLabel = DAYS.find(d => d.key === copySourceDay)?.label;
    return {
      label: dayLabel,
      enabled: daySchedule?.enabled,
      blockCount: daySchedule?.time_blocks?.length || 0,
      blocks: daySchedule?.time_blocks || []
    };
  };

  if (loading) {
    return <div className="text-center py-12">Loading availability settings...</div>;
  }

  if (!availability) {
    return <div className="text-center py-12">Failed to load availability settings</div>;
  }

  const sourceDayInfo = getSourceDayInfo();

  return (
    <div data-testid="availability-settings">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-4xl font-serif text-primary mb-2">Availability Settings</h2>
        <p className="text-muted-foreground">Define your working hours and session preferences</p>
      </div>

      {/* Session Settings */}
      <Card className="p-6 mb-6 bg-white/70 backdrop-blur-xl border border-border/40">
        <div className="flex items-center gap-2 mb-4">
          <Settings size={20} className="text-primary" />
          <h3 className="text-xl font-serif text-primary">Session Settings</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <Label htmlFor="session-duration">Session Duration (minutes)</Label>
            <Input
              id="session-duration"
              type="number"
              min="15"
              max="240"
              step="5"
              value={availability.session_duration}
              onChange={(e) =>
                setAvailability((prev) => ({
                  ...prev,
                  session_duration: parseInt(e.target.value) || 60,
                }))
              }
              disabled={isReadOnly}
              className="mt-1"
              data-testid="session-duration-input"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Default length for each appointment (15-240 minutes)
            </p>
          </div>
          <div>
            <Label htmlFor="buffer-time">Buffer Time (minutes)</Label>
            <Input
              id="buffer-time"
              type="number"
              min="0"
              max="60"
              step="5"
              value={availability.buffer_time}
              onChange={(e) =>
                setAvailability((prev) => ({
                  ...prev,
                  buffer_time: parseInt(e.target.value) || 0,
                }))
              }
              disabled={isReadOnly}
              className="mt-1"
              data-testid="buffer-time-input"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Break between appointments (0-60 minutes)
            </p>
          </div>
        </div>
      </Card>

      {/* Weekly Schedule */}
      <Card className="p-6 mb-6 bg-white/70 backdrop-blur-xl border border-border/40">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Calendar size={20} className="text-primary" />
            <h3 className="text-xl font-serif text-primary">Weekly Schedule</h3>
          </div>
          {canUseCopyFeature && (
            <p className="text-xs text-muted-foreground">
              Use <Copy size={12} className="inline mx-1" /> to copy a day's schedule to other days
            </p>
          )}
        </div>
        <div className="space-y-4">
          {DAYS.map((day) => (
            <div
              key={day.key}
              className="border border-border/40 rounded-lg p-4"
              data-testid={`day-${day.key}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <Switch
                    checked={availability[day.key]?.enabled || false}
                    onCheckedChange={(checked) => handleDayToggle(day.key, checked)}
                    disabled={isReadOnly}
                    data-testid={`toggle-${day.key}`}
                  />
                  <span className="font-medium text-foreground">{day.label}</span>
                  {availability[day.key]?.enabled && availability[day.key]?.time_blocks?.length > 0 && (
                    <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                      {availability[day.key].time_blocks.length} block(s)
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {/* Copy Day Button - only for therapists, not read-only, and day must be enabled with blocks */}
                  {canUseCopyFeature && availability[day.key]?.enabled && availability[day.key]?.time_blocks?.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openCopyDialog(day.key)}
                      className="text-muted-foreground hover:text-primary"
                      title={`Copy ${day.label}'s schedule to other days`}
                      data-testid={`copy-day-${day.key}`}
                    >
                      <Copy size={14} className="mr-1" />
                      Copy
                    </Button>
                  )}
                  {availability[day.key]?.enabled && !isReadOnly && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleAddTimeBlock(day.key)}
                      data-testid={`add-block-${day.key}`}
                    >
                      <Plus size={14} className="mr-1" />
                      Add Time Block
                    </Button>
                  )}
                </div>
              </div>

              {availability[day.key]?.enabled && (
                <div className="space-y-2 ml-12">
                  {availability[day.key].time_blocks.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No time blocks defined. Add a time block to set your working hours.
                    </p>
                  ) : (
                    availability[day.key].time_blocks.map((block, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                          <Clock size={14} className="text-muted-foreground" />
                          <Input
                            type="time"
                            value={block.start_time}
                            onChange={(e) =>
                              handleTimeBlockChange(day.key, index, 'start_time', e.target.value)
                            }
                            disabled={isReadOnly}
                            className="w-32"
                            data-testid={`start-time-${day.key}-${index}`}
                          />
                          <span className="text-muted-foreground">to</span>
                          <Input
                            type="time"
                            value={block.end_time}
                            onChange={(e) =>
                              handleTimeBlockChange(day.key, index, 'end_time', e.target.value)
                            }
                            disabled={isReadOnly}
                            className="w-32"
                            data-testid={`end-time-${day.key}-${index}`}
                          />
                        </div>
                        {!isReadOnly && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveTimeBlock(day.key, index)}
                            className="text-error hover:text-error hover:bg-error/10"
                            data-testid={`remove-block-${day.key}-${index}`}
                          >
                            <Trash2 size={14} />
                          </Button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {!isReadOnly && (
          <div className="mt-6 flex justify-end">
            <Button
              onClick={handleSaveAvailability}
              disabled={saving}
              className="bg-primary hover:bg-primary-700"
              data-testid="save-availability-button"
            >
              {saving ? 'Saving...' : 'Save Availability'}
            </Button>
          </div>
        )}
      </Card>

      {/* Blocked Times */}
      <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Ban size={20} className="text-primary" />
            <h3 className="text-xl font-serif text-primary">Blocked Times</h3>
          </div>
          {!isReadOnly && (
            <Button
              variant="outline"
              onClick={() => setShowBlockDialog(true)}
              data-testid="add-blocked-time-button"
            >
              <Plus size={16} className="mr-2" />
              Block Time
            </Button>
          )}
        </div>
        <p className="text-sm text-muted-foreground mb-4">
          Block specific dates or time ranges when you're unavailable (holidays, vacation, etc.)
        </p>

        {blockedTimes.length === 0 ? (
          <div className="text-center py-8">
            <Ban size={32} className="mx-auto text-muted-foreground/30 mb-2" />
            <p className="text-muted-foreground">No blocked times</p>
          </div>
        ) : (
          <div className="space-y-2">
            {blockedTimes.map((block) => (
              <div
                key={block.id}
                className="flex items-center justify-between p-3 bg-error/5 border border-error/20 rounded-lg"
                data-testid={`blocked-time-${block.id}`}
              >
                <div>
                  <p className="font-medium text-foreground">
                    {formatDateWithDay(block.start_datetime)}
                    {!block.is_all_day && (
                      <>
                        {' '}
                        {formatTimeRange(block.start_datetime, block.end_datetime)}
                      </>
                    )}
                    {block.is_all_day && ' (All Day)'}
                  </p>
                  {block.reason && (
                    <p className="text-sm text-muted-foreground">{block.reason}</p>
                  )}
                </div>
                {!isReadOnly && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteBlockedTime(block.id)}
                    className="text-error hover:text-error hover:bg-error/10"
                    data-testid={`delete-blocked-${block.id}`}
                  >
                    <Trash2 size={14} />
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Block Time Dialog */}
      <Dialog open={showBlockDialog} onOpenChange={setShowBlockDialog}>
        <DialogContent data-testid="block-time-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Block Time</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateBlockedTime} className="space-y-4">
            <div>
              <Label htmlFor="block-start">Start Date & Time</Label>
              <Input
                id="block-start"
                type="datetime-local"
                value={newBlock.start_datetime}
                onChange={(e) => setNewBlock({ ...newBlock, start_datetime: e.target.value })}
                required
                className="mt-1"
                data-testid="block-start-input"
              />
            </div>
            <div>
              <Label htmlFor="block-end">End Date & Time</Label>
              <Input
                id="block-end"
                type="datetime-local"
                value={newBlock.end_datetime}
                onChange={(e) => setNewBlock({ ...newBlock, end_datetime: e.target.value })}
                required
                className="mt-1"
                data-testid="block-end-input"
              />
            </div>
            <div>
              <Label htmlFor="block-reason">Reason (optional)</Label>
              <Input
                id="block-reason"
                value={newBlock.reason}
                onChange={(e) => setNewBlock({ ...newBlock, reason: e.target.value })}
                placeholder="e.g., Vacation, Personal time, Conference"
                className="mt-1"
                data-testid="block-reason-input"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="all-day"
                checked={newBlock.is_all_day}
                onCheckedChange={(checked) => setNewBlock({ ...newBlock, is_all_day: checked })}
                data-testid="block-all-day-switch"
              />
              <Label htmlFor="all-day">All day event</Label>
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1" data-testid="save-block-button">
                Block Time
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowBlockDialog(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Copy Day Dialog */}
      <Dialog open={showCopyDialog} onOpenChange={setShowCopyDialog}>
        <DialogContent data-testid="copy-day-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary flex items-center gap-2">
              <Copy size={24} />
              Copy Day Schedule
            </DialogTitle>
          </DialogHeader>
          
          {sourceDayInfo && (
            <div className="space-y-4">
              {/* Source Day Info */}
              <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
                <p className="font-medium text-foreground mb-2">
                  Copying from: <span className="text-primary">{sourceDayInfo.label}</span>
                </p>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>• {sourceDayInfo.blockCount} time block(s)</p>
                  {sourceDayInfo.blocks.map((block, idx) => (
                    <p key={idx} className="ml-4">
                      {block.start_time} - {block.end_time}
                    </p>
                  ))}
                  <p>• Session duration: {availability.session_duration} minutes</p>
                  <p>• Buffer time: {availability.buffer_time} minutes</p>
                </div>
              </div>

              {/* Target Days Selection */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-base">Copy to:</Label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={selectWeekdays}
                      className="text-xs"
                      data-testid="select-weekdays"
                    >
                      Weekdays
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={selectAllTargets}
                      className="text-xs"
                      data-testid="select-all-days"
                    >
                      All Days
                    </Button>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-2">
                  {DAYS.filter(d => d.key !== copySourceDay).map((day) => {
                    const hasExisting = availability[day.key]?.enabled && availability[day.key]?.time_blocks?.length > 0;
                    return (
                      <label
                        key={day.key}
                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                          copyTargetDays[day.key]
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        }`}
                        data-testid={`target-day-${day.key}`}
                      >
                        <input
                          type="checkbox"
                          checked={copyTargetDays[day.key] || false}
                          onChange={() => toggleTargetDay(day.key)}
                          className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                        />
                        <div className="flex-1">
                          <span className="font-medium">{day.label}</span>
                          {hasExisting && (
                            <span className="ml-2 text-xs text-warning">(has schedule)</span>
                          )}
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Warning for overwriting */}
              {Object.entries(copyTargetDays).some(([day, selected]) => 
                selected && availability[day]?.enabled && availability[day]?.time_blocks?.length > 0
              ) && (
                <div className="p-3 bg-warning/10 border border-warning/30 rounded-lg text-sm text-warning-foreground">
                  <strong>Note:</strong> Some selected days have existing schedules that will be overwritten.
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button
                  onClick={handleCopyDay}
                  className="flex-1"
                  disabled={!Object.values(copyTargetDays).some(v => v)}
                  data-testid="confirm-copy-button"
                >
                  <Copy size={16} className="mr-2" />
                  Copy Schedule
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCopyDialog(false);
                    setCopySourceDay(null);
                    setCopyTargetDays({});
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AvailabilitySettings;
