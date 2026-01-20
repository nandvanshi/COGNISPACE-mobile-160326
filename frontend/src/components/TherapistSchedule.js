import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { 
  ChevronLeft, ChevronRight, Calendar as CalendarIcon, Clock, 
  User, Plus, Edit2, Trash2, X, Check, Ban, ArrowLeft,
  CalendarDays, Settings, AlertTriangle
} from 'lucide-react';

// IST timezone offset
const IST_OFFSET = 5.5 * 60 * 60 * 1000;

// Helper to get current date in IST
const nowIST = () => {
  const now = new Date();
  return new Date(now.getTime() + (IST_OFFSET - now.getTimezoneOffset() * 60000));
};

// Format date as DD/MM/YYYY
const formatDateDMY = (date) => {
  const d = new Date(date);
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
};

// Format time as HH:mm (24-hour)
const formatTime24 = (dateStr) => {
  const d = new Date(dateStr);
  return d.toLocaleTimeString('en-IN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    hour12: false,
    timeZone: 'Asia/Kolkata'
  });
};

// Format date for display
const formatDateLong = (date) => {
  return new Date(date).toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'Asia/Kolkata'
  });
};

// Get day name
const getDayName = (date) => {
  return new Date(date).toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
};

const TherapistSchedule = ({ isReadOnly = false }) => {
  const { user } = useAuth();
  const [view, setView] = useState('month'); // 'month' or 'day'
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [availability, setAvailability] = useState(null);
  const [blockedTimes, setBlockedTimes] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Dialog states
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showBlockDialog, setShowBlockDialog] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  
  // Form states
  const [newAppt, setNewAppt] = useState({
    client_id: '',
    start_time: '',
    end_time: '',
    notes: ''
  });
  const [newBlock, setNewBlock] = useState({
    start_time: '',
    end_time: '',
    reason: '',
    is_all_day: false
  });
  const [jumpToDate, setJumpToDate] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [apptsRes, clientsRes, availRes, blockedRes] = await Promise.all([
        axios.get(`${API}/appointments`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/availability`).catch(() => ({ data: null })),
        axios.get(`${API}/blocked-times`).catch(() => ({ data: [] })),
      ]);
      setAppointments(apptsRes.data);
      setClients(clientsRes.data);
      setAvailability(availRes.data);
      setBlockedTimes(blockedRes.data || []);
    } catch (error) {
      toast.error('Failed to load schedule data');
    } finally {
      setLoading(false);
    }
  };

  // Get calendar data for month view
  const calendarData = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDay = firstDay.getDay(); // 0 = Sunday
    
    const days = [];
    
    // Add empty slots for days before the 1st
    for (let i = 0; i < startDay; i++) {
      days.push(null);
    }
    
    // Add all days of the month
    for (let d = 1; d <= lastDay.getDate(); d++) {
      const date = new Date(year, month, d);
      const dateStr = date.toISOString().split('T')[0];
      
      // Count appointments for this day
      const dayAppts = appointments.filter(appt => {
        const apptDate = new Date(appt.start_time).toISOString().split('T')[0];
        return apptDate === dateStr && appt.status !== 'cancelled';
      });
      
      days.push({
        date,
        day: d,
        appointmentCount: dayAppts.length,
        isToday: dateStr === nowIST().toISOString().split('T')[0],
        isPast: date < new Date(nowIST().toISOString().split('T')[0])
      });
    }
    
    return days;
  }, [currentDate, appointments]);

  // Get schedule for selected day
  const daySchedule = useMemo(() => {
    if (!selectedDate || !availability) return { slots: [], appointments: [] };
    
    const dateStr = selectedDate.toISOString().split('T')[0];
    const dayName = getDayName(selectedDate);
    const dayAvailability = availability[dayName];
    
    // Get appointments for the day
    const dayAppts = appointments.filter(appt => {
      const apptDate = new Date(appt.start_time).toISOString().split('T')[0];
      return apptDate === dateStr && appt.status !== 'cancelled';
    }).sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
    
    // Get blocked times for the day
    const dayBlocks = blockedTimes.filter(block => {
      const blockDate = new Date(block.start_datetime).toISOString().split('T')[0];
      return blockDate === dateStr;
    });
    
    // Generate time slots (8 AM to 10 PM in 30-min increments)
    const slots = [];
    for (let hour = 8; hour <= 21; hour++) {
      for (let min = 0; min < 60; min += 30) {
        const timeStr = `${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}`;
        const slotStart = new Date(`${dateStr}T${timeStr}:00`);
        const slotEnd = new Date(slotStart.getTime() + 30 * 60000);
        
        // Check if slot is within availability
        let isAvailable = false;
        if (dayAvailability?.enabled && dayAvailability.time_blocks) {
          dayAvailability.time_blocks.forEach(avail => {
            const availStart = avail.start;
            const availEnd = avail.end;
            if (timeStr >= availStart && timeStr < availEnd) {
              isAvailable = true;
            }
          });
        }
        
        // Check if slot is blocked
        const isBlocked = dayBlocks.some(block => {
          if (block.is_all_day) return true;
          const blockStart = new Date(block.start_datetime);
          const blockEnd = new Date(block.end_datetime);
          return slotStart >= blockStart && slotStart < blockEnd;
        });
        
        // Check if slot has appointment
        const appointment = dayAppts.find(appt => {
          const apptStart = new Date(appt.start_time);
          const apptEnd = new Date(appt.end_time);
          return slotStart >= apptStart && slotStart < apptEnd;
        });
        
        slots.push({
          time: timeStr,
          start: slotStart,
          end: slotEnd,
          isAvailable: isAvailable && !isBlocked,
          isBlocked,
          appointment
        });
      }
    }
    
    return { slots, appointments: dayAppts, blocks: dayBlocks };
  }, [selectedDate, availability, appointments, blockedTimes]);

  // Navigation handlers
  const goToPrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const goToToday = () => {
    const today = nowIST();
    setCurrentDate(new Date(today.getFullYear(), today.getMonth(), 1));
  };

  const handleDateClick = (dayData) => {
    if (!dayData) return;
    setSelectedDate(dayData.date);
    setView('day');
  };

  const goToPrevDay = () => {
    const prev = new Date(selectedDate);
    prev.setDate(prev.getDate() - 1);
    setSelectedDate(prev);
  };

  const goToNextDay = () => {
    const next = new Date(selectedDate);
    next.setDate(next.getDate() + 1);
    setSelectedDate(next);
  };

  const handleJumpToDate = () => {
    if (!jumpToDate) return;
    const date = new Date(jumpToDate);
    if (isNaN(date.getTime())) {
      toast.error('Invalid date');
      return;
    }
    setCurrentDate(new Date(date.getFullYear(), date.getMonth(), 1));
    setSelectedDate(date);
    setView('day');
    setShowDatePicker(false);
    setJumpToDate('');
  };

  // Schedule new appointment
  const handleScheduleAppointment = async (e) => {
    e.preventDefault();
    if (!newAppt.client_id || !selectedSlot) {
      toast.error('Please select a client');
      return;
    }

    try {
      const dateStr = selectedDate.toISOString().split('T')[0];
      const duration = availability?.session_duration || 60;
      const startTime = new Date(`${dateStr}T${selectedSlot.time}:00`);
      const endTime = new Date(startTime.getTime() + duration * 60000);

      await axios.post(`${API}/appointments`, {
        client_id: newAppt.client_id,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        notes: newAppt.notes
      });

      toast.success('Appointment scheduled');
      setShowScheduleDialog(false);
      setNewAppt({ client_id: '', start_time: '', end_time: '', notes: '' });
      setSelectedSlot(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to schedule appointment');
    }
  };

  // Edit appointment
  const handleEditAppointment = async (e) => {
    e.preventDefault();
    if (!selectedAppointment) return;

    try {
      await axios.put(`${API}/appointments/${selectedAppointment.id}`, {
        notes: selectedAppointment.notes,
        status: selectedAppointment.status
      });
      toast.success('Appointment updated');
      setShowEditDialog(false);
      setSelectedAppointment(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update appointment');
    }
  };

  // Cancel appointment
  const handleCancelAppointment = async (apptId) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;

    try {
      await axios.put(`${API}/appointments/${apptId}`, { status: 'cancelled' });
      toast.success('Appointment cancelled');
      fetchData();
    } catch (error) {
      toast.error('Failed to cancel appointment');
    }
  };

  // Block time
  const handleBlockTime = async (e) => {
    e.preventDefault();
    if (!selectedDate) return;

    try {
      const dateStr = selectedDate.toISOString().split('T')[0];
      let startDatetime, endDatetime;

      if (newBlock.is_all_day) {
        startDatetime = `${dateStr}T00:00:00`;
        endDatetime = `${dateStr}T23:59:59`;
      } else {
        startDatetime = `${dateStr}T${newBlock.start_time}:00`;
        endDatetime = `${dateStr}T${newBlock.end_time}:00`;
      }

      await axios.post(`${API}/blocked-times`, {
        start_datetime: startDatetime,
        end_datetime: endDatetime,
        reason: newBlock.reason,
        is_all_day: newBlock.is_all_day
      });

      toast.success('Time blocked');
      setShowBlockDialog(false);
      setNewBlock({ start_time: '', end_time: '', reason: '', is_all_day: false });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to block time');
    }
  };

  // Remove blocked time
  const handleRemoveBlock = async (blockId) => {
    try {
      await axios.delete(`${API}/blocked-times/${blockId}`);
      toast.success('Block removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove block');
    }
  };

  // Open schedule dialog for a slot
  const openScheduleDialog = (slot) => {
    setSelectedSlot(slot);
    setShowScheduleDialog(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading schedule...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="therapist-schedule">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-serif text-foreground">Schedule</h2>
          <p className="text-muted-foreground mt-1">
            {view === 'month' 
              ? currentDate.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })
              : formatDateLong(selectedDate)
            }
          </p>
        </div>
        <div className="flex items-center gap-2">
          {view === 'day' && (
            <Button 
              variant="outline" 
              onClick={() => setView('month')}
              className="gap-2"
            >
              <ArrowLeft size={16} />
              <span className="hidden sm:inline">Back to Month</span>
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => setShowDatePicker(true)}
            className="gap-2"
          >
            <CalendarIcon size={16} />
            <span className="hidden sm:inline">Jump to Date</span>
          </Button>
        </div>
      </div>

      {/* Month View */}
      {view === 'month' && (
        <Card className="p-4 sm:p-6">
          {/* Month Navigation */}
          <div className="flex items-center justify-between mb-6">
            <Button variant="outline" size="sm" onClick={goToPrevMonth}>
              <ChevronLeft size={18} />
            </Button>
            <div className="flex items-center gap-3">
              <h3 className="text-lg sm:text-xl font-semibold">
                {currentDate.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}
              </h3>
              <Button variant="ghost" size="sm" onClick={goToToday} className="text-sm">
                Today
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={goToNextMonth}>
              <ChevronRight size={18} />
            </Button>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1 sm:gap-2">
            {/* Day Headers */}
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-xs sm:text-sm font-medium text-muted-foreground py-2">
                {day}
              </div>
            ))}

            {/* Calendar Days */}
            {calendarData.map((dayData, idx) => (
              <div
                key={idx}
                onClick={() => handleDateClick(dayData)}
                className={`
                  aspect-square sm:aspect-auto sm:min-h-[80px] p-1 sm:p-2 rounded-lg border transition-all
                  ${!dayData ? 'bg-transparent border-transparent' : 
                    dayData.isToday ? 'bg-primary/10 border-primary' :
                    dayData.isPast ? 'bg-muted/30 border-border/50' :
                    'bg-surface border-border hover:border-primary/50 cursor-pointer'
                  }
                `}
                data-testid={dayData ? `calendar-day-${dayData.day}` : undefined}
              >
                {dayData && (
                  <>
                    <div className={`text-sm sm:text-base font-medium ${
                      dayData.isToday ? 'text-primary' : 
                      dayData.isPast ? 'text-muted-foreground' : 'text-foreground'
                    }`}>
                      {dayData.day}
                    </div>
                    {dayData.appointmentCount > 0 && (
                      <div className="mt-1">
                        <span className={`inline-flex items-center justify-center w-5 h-5 sm:w-6 sm:h-6 text-xs rounded-full ${
                          dayData.isToday ? 'bg-primary text-white' : 'bg-primary/20 text-primary'
                        }`}>
                          {dayData.appointmentCount}
                        </span>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded bg-primary/10 border border-primary"></span>
              <span>Today</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full bg-primary/20"></span>
              <span>Has sessions</span>
            </div>
          </div>
        </Card>
      )}

      {/* Day View */}
      {view === 'day' && selectedDate && (
        <div className="space-y-4">
          {/* Day Navigation */}
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <Button variant="ghost" size="sm" onClick={goToPrevDay} className="gap-1">
                <ChevronLeft size={18} />
                <span className="hidden sm:inline">Previous Day</span>
              </Button>
              <div className="text-center">
                <p className="font-semibold text-lg">{formatDateDMY(selectedDate)}</p>
                <p className="text-sm text-muted-foreground">
                  {selectedDate.toLocaleDateString('en-IN', { weekday: 'long' })}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={goToNextDay} className="gap-1">
                <span className="hidden sm:inline">Next Day</span>
                <ChevronRight size={18} />
              </Button>
            </div>
          </Card>

          {/* Day Actions */}
          {!isReadOnly && (
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => setShowBlockDialog(true)}
                className="gap-2"
              >
                <Ban size={16} />
                Block Time
              </Button>
            </div>
          )}

          {/* Time Slots Grid */}
          <Card className="overflow-hidden">
            <div className="p-4 bg-muted/30 border-b border-border">
              <h3 className="font-semibold flex items-center gap-2">
                <Clock size={18} />
                Day Schedule
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                {daySchedule.appointments.length} session(s) scheduled
              </p>
            </div>

            <div className="divide-y divide-border">
              {daySchedule.slots.map((slot, idx) => {
                const showTimeLabel = idx === 0 || slot.time.endsWith(':00');
                
                return (
                  <div
                    key={slot.time}
                    className={`flex items-stretch min-h-[60px] ${
                      slot.isBlocked ? 'bg-red-50' :
                      slot.appointment ? 'bg-primary/5' :
                      slot.isAvailable ? 'bg-green-50/50 hover:bg-green-50' :
                      'bg-muted/20'
                    }`}
                    data-testid={`time-slot-${slot.time}`}
                  >
                    {/* Time Label */}
                    <div className={`w-16 sm:w-20 flex-shrink-0 p-2 text-right border-r border-border ${
                      showTimeLabel ? 'font-medium text-foreground' : 'text-muted-foreground/50'
                    }`}>
                      {showTimeLabel && (
                        <span className="text-sm">{slot.time}</span>
                      )}
                    </div>

                    {/* Slot Content */}
                    <div className="flex-1 p-2 sm:p-3">
                      {slot.isBlocked && !slot.appointment && (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 text-red-600">
                            <Ban size={16} />
                            <span className="text-sm font-medium">Blocked</span>
                          </div>
                          {!isReadOnly && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                const block = daySchedule.blocks?.find(b => {
                                  const blockStart = new Date(b.start_datetime);
                                  return slot.start >= blockStart;
                                });
                                if (block) handleRemoveBlock(block.id);
                              }}
                              className="text-red-600 h-8"
                            >
                              <X size={14} />
                            </Button>
                          )}
                        </div>
                      )}

                      {slot.appointment && (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-medium ${
                              slot.appointment.status === 'completed' ? 'bg-green-100 text-green-700' :
                              slot.appointment.status === 'in_progress' ? 'bg-amber-100 text-amber-700' :
                              'bg-primary/10 text-primary'
                            }`}>
                              {slot.appointment.client_name?.charAt(0) || 'C'}
                            </div>
                            <div>
                              <p className="font-medium text-sm sm:text-base">{slot.appointment.client_name}</p>
                              <p className="text-xs sm:text-sm text-muted-foreground">
                                {formatTime24(slot.appointment.start_time)} - {formatTime24(slot.appointment.end_time)}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              slot.appointment.status === 'completed' ? 'bg-green-100 text-green-700' :
                              slot.appointment.status === 'in_progress' ? 'bg-amber-100 text-amber-700' :
                              slot.appointment.status === 'cancelled' ? 'bg-red-100 text-red-700' :
                              'bg-blue-100 text-blue-700'
                            }`}>
                              {slot.appointment.status}
                            </span>
                            {!isReadOnly && slot.appointment.status === 'scheduled' && (
                              <div className="flex gap-1 ml-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setSelectedAppointment(slot.appointment);
                                    setShowEditDialog(true);
                                  }}
                                  className="h-8 w-8 p-0"
                                >
                                  <Edit2 size={14} />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleCancelAppointment(slot.appointment.id)}
                                  className="h-8 w-8 p-0 text-red-600"
                                >
                                  <Trash2 size={14} />
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {!slot.appointment && !slot.isBlocked && slot.isAvailable && !isReadOnly && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openScheduleDialog(slot)}
                          className="text-green-600 hover:text-green-700 hover:bg-green-100 gap-2 h-8"
                        >
                          <Plus size={14} />
                          Schedule
                        </Button>
                      )}

                      {!slot.appointment && !slot.isBlocked && !slot.isAvailable && (
                        <span className="text-xs text-muted-foreground">Unavailable</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}

      {/* Schedule Appointment Dialog */}
      <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Schedule Appointment</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleScheduleAppointment} className="space-y-4">
            <div>
              <Label>Date & Time</Label>
              <p className="text-sm text-muted-foreground mt-1">
                {selectedDate && formatDateDMY(selectedDate)} at {selectedSlot?.time}
              </p>
            </div>

            <div>
              <Label htmlFor="client">Client *</Label>
              <Select
                value={newAppt.client_id}
                onValueChange={(v) => setNewAppt({ ...newAppt, client_id: v })}
              >
                <SelectTrigger id="client" className="mt-1">
                  <SelectValue placeholder="Select client" />
                </SelectTrigger>
                <SelectContent>
                  {clients.map(client => (
                    <SelectItem key={client.id} value={client.id}>
                      {client.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Duration</Label>
              <p className="text-sm text-muted-foreground mt-1">
                {availability?.session_duration || 60} minutes
              </p>
            </div>

            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={newAppt.notes}
                onChange={(e) => setNewAppt({ ...newAppt, notes: e.target.value })}
                placeholder="Optional notes..."
                className="mt-1"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowScheduleDialog(false)} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" className="flex-1">
                Schedule
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Appointment Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Appointment</DialogTitle>
          </DialogHeader>
          {selectedAppointment && (
            <form onSubmit={handleEditAppointment} className="space-y-4">
              <div>
                <Label>Client</Label>
                <p className="text-sm font-medium mt-1">{selectedAppointment.client_name}</p>
              </div>

              <div>
                <Label>Time</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  {formatTime24(selectedAppointment.start_time)} - {formatTime24(selectedAppointment.end_time)}
                </p>
              </div>

              <div>
                <Label htmlFor="edit-status">Status</Label>
                <Select
                  value={selectedAppointment.status}
                  onValueChange={(v) => setSelectedAppointment({ ...selectedAppointment, status: v })}
                >
                  <SelectTrigger id="edit-status" className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="scheduled">Scheduled</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="edit-notes">Notes</Label>
                <Textarea
                  id="edit-notes"
                  value={selectedAppointment.notes || ''}
                  onChange={(e) => setSelectedAppointment({ ...selectedAppointment, notes: e.target.value })}
                  className="mt-1"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)} className="flex-1">
                  Cancel
                </Button>
                <Button type="submit" className="flex-1">
                  Save Changes
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Block Time Dialog */}
      <Dialog open={showBlockDialog} onOpenChange={setShowBlockDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Block Time</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleBlockTime} className="space-y-4">
            <div>
              <Label>Date</Label>
              <p className="text-sm text-muted-foreground mt-1">
                {selectedDate && formatDateDMY(selectedDate)}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="all-day"
                checked={newBlock.is_all_day}
                onChange={(e) => setNewBlock({ ...newBlock, is_all_day: e.target.checked })}
                className="rounded"
              />
              <Label htmlFor="all-day">Block entire day</Label>
            </div>

            {!newBlock.is_all_day && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="block-start">Start Time</Label>
                  <Input
                    id="block-start"
                    type="time"
                    value={newBlock.start_time}
                    onChange={(e) => setNewBlock({ ...newBlock, start_time: e.target.value })}
                    className="mt-1"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="block-end">End Time</Label>
                  <Input
                    id="block-end"
                    type="time"
                    value={newBlock.end_time}
                    onChange={(e) => setNewBlock({ ...newBlock, end_time: e.target.value })}
                    className="mt-1"
                    required
                  />
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="block-reason">Reason (optional)</Label>
              <Input
                id="block-reason"
                value={newBlock.reason}
                onChange={(e) => setNewBlock({ ...newBlock, reason: e.target.value })}
                placeholder="e.g., Personal time, Holiday"
                className="mt-1"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowBlockDialog(false)} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" className="flex-1">
                Block Time
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Jump to Date Dialog */}
      <Dialog open={showDatePicker} onOpenChange={setShowDatePicker}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Jump to Date</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="jump-date">Select Date</Label>
              <Input
                id="jump-date"
                type="date"
                value={jumpToDate}
                onChange={(e) => setJumpToDate(e.target.value)}
                className="mt-1"
              />
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setShowDatePicker(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleJumpToDate} className="flex-1">
                Go to Date
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TherapistSchedule;
