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
  CalendarDays, Settings, AlertTriangle, CalendarPlus
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

// Get day name (lowercase)
const getDayName = (date) => {
  return new Date(date).toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
};

// Parse time string to minutes from midnight
const timeToMinutes = (timeStr) => {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
};

// Minutes to time string
const minutesToTime = (minutes) => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
};

const TherapistSchedule = ({ isReadOnly = false, isAssistant = false }) => {
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
  const [showAddAvailabilityDialog, setShowAddAvailabilityDialog] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  
  // Form states
  const [newAppt, setNewAppt] = useState({
    client_id: '',
    notes: ''
  });
  const [newBlock, setNewBlock] = useState({
    start_time: '',
    end_time: '',
    reason: '',
    is_all_day: false
  });
  const [newAvailability, setNewAvailability] = useState({
    start_time: '',
    end_time: ''
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
    const startDay = firstDay.getDay();
    
    const days = [];
    
    for (let i = 0; i < startDay; i++) {
      days.push(null);
    }
    
    for (let d = 1; d <= lastDay.getDate(); d++) {
      const date = new Date(year, month, d);
      const dateStr = date.toISOString().split('T')[0];
      
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

  // Generate dynamic schedule for selected day based on availability
  const daySchedule = useMemo(() => {
    if (!selectedDate || !availability) {
      return { availableSlots: [], bookedSessions: [], blockedPeriods: [], hasAvailability: false };
    }
    
    const dateStr = selectedDate.toISOString().split('T')[0];
    const dayName = getDayName(selectedDate);
    const dayAvailability = availability[dayName];
    
    // Get booked appointments for the day
    const dayAppts = appointments.filter(appt => {
      const apptDate = new Date(appt.start_time).toISOString().split('T')[0];
      return apptDate === dateStr && appt.status !== 'cancelled';
    }).sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
    
    // Get blocked times for the day
    const dayBlocks = blockedTimes.filter(block => {
      const blockDate = new Date(block.start_datetime).toISOString().split('T')[0];
      return blockDate === dateStr;
    });
    
    // Check if day is fully blocked
    const isFullDayBlocked = dayBlocks.some(b => b.is_all_day);
    
    if (!dayAvailability?.enabled || !dayAvailability.time_blocks?.length || isFullDayBlocked) {
      return { 
        availableSlots: [], 
        bookedSessions: dayAppts, 
        blockedPeriods: dayBlocks,
        hasAvailability: false,
        isFullDayBlocked 
      };
    }
    
    const sessionDuration = availability.session_duration || 60;
    const bufferTime = availability.buffer_time || 0;
    const slotDuration = sessionDuration + bufferTime;
    
    const availableSlots = [];
    
    // Process each availability time block
    dayAvailability.time_blocks.forEach(block => {
      const blockStartMinutes = timeToMinutes(block.start_time);
      const blockEndMinutes = timeToMinutes(block.end_time);
      
      // Generate slots within this block
      let currentSlotStart = blockStartMinutes;
      
      while (currentSlotStart + sessionDuration <= blockEndMinutes) {
        const slotStartTime = minutesToTime(currentSlotStart);
        const slotEndTime = minutesToTime(currentSlotStart + sessionDuration);
        
        const slotStartDate = new Date(`${dateStr}T${slotStartTime}:00`);
        const slotEndDate = new Date(`${dateStr}T${slotEndTime}:00`);
        
        // Check if this slot is blocked
        const isBlocked = dayBlocks.some(blocked => {
          if (blocked.is_all_day) return true;
          const blockedStart = new Date(blocked.start_datetime);
          const blockedEnd = new Date(blocked.end_datetime);
          return (slotStartDate < blockedEnd && slotEndDate > blockedStart);
        });
        
        // Check if this slot overlaps with any booked appointment
        const overlappingAppt = dayAppts.find(appt => {
          const apptStart = new Date(appt.start_time);
          const apptEnd = new Date(appt.end_time);
          return (slotStartDate < apptEnd && slotEndDate > apptStart);
        });
        
        if (!isBlocked && !overlappingAppt) {
          availableSlots.push({
            id: `slot-${slotStartTime}`,
            startTime: slotStartTime,
            endTime: slotEndTime,
            startDate: slotStartDate,
            endDate: slotEndDate,
            availabilityBlock: block
          });
        }
        
        // Move to next slot (include buffer time)
        currentSlotStart += slotDuration;
      }
    });
    
    return { 
      availableSlots, 
      bookedSessions: dayAppts, 
      blockedPeriods: dayBlocks,
      hasAvailability: true,
      timeBlocks: dayAvailability.time_blocks,
      sessionDuration,
      bufferTime
    };
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
      await axios.post(`${API}/appointments`, {
        client_id: newAppt.client_id,
        start_time: selectedSlot.startDate.toISOString(),
        end_time: selectedSlot.endDate.toISOString(),
        notes: newAppt.notes
      });

      toast.success('Appointment scheduled');
      setShowScheduleDialog(false);
      setNewAppt({ client_id: '', notes: '' });
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
        if (!newBlock.start_time || !newBlock.end_time) {
          toast.error('Please specify start and end time');
          return;
        }
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

  // Add availability for the day
  const handleAddAvailability = async (e) => {
    e.preventDefault();
    if (!selectedDate || !newAvailability.start_time || !newAvailability.end_time) {
      toast.error('Please specify start and end time');
      return;
    }

    try {
      const dayName = getDayName(selectedDate);
      const currentDayAvail = availability?.[dayName] || { enabled: false, time_blocks: [] };
      
      // Add new time block
      const newTimeBlocks = [
        ...(currentDayAvail.time_blocks || []),
        { start_time: newAvailability.start_time, end_time: newAvailability.end_time }
      ].sort((a, b) => timeToMinutes(a.start_time) - timeToMinutes(b.start_time));

      // Update availability for the day
      await axios.post(`${API}/availability`, {
        ...availability,
        [dayName]: {
          enabled: true,
          time_blocks: newTimeBlocks
        }
      });

      toast.success('Availability added');
      setShowAddAvailabilityDialog(false);
      setNewAvailability({ start_time: '', end_time: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add availability');
    }
  };

  // Remove availability block
  const handleRemoveAvailability = async (blockIndex) => {
    if (!selectedDate) return;
    
    try {
      const dayName = getDayName(selectedDate);
      const currentDayAvail = availability?.[dayName];
      if (!currentDayAvail) return;

      const newTimeBlocks = currentDayAvail.time_blocks.filter((_, idx) => idx !== blockIndex);

      await axios.post(`${API}/availability`, {
        ...availability,
        [dayName]: {
          enabled: newTimeBlocks.length > 0,
          time_blocks: newTimeBlocks
        }
      });

      toast.success('Availability removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove availability');
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
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-xs sm:text-sm font-medium text-muted-foreground py-2">
                {day}
              </div>
            ))}

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
                <span className="hidden sm:inline">Previous</span>
              </Button>
              <div className="text-center">
                <p className="font-semibold text-lg">{formatDateDMY(selectedDate)}</p>
                <p className="text-sm text-muted-foreground">
                  {selectedDate.toLocaleDateString('en-IN', { weekday: 'long' })}
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={goToNextDay} className="gap-1">
                <span className="hidden sm:inline">Next</span>
                <ChevronRight size={18} />
              </Button>
            </div>
          </Card>

          {/* Day Actions */}
          {!isReadOnly && (
            <div className="flex flex-wrap gap-2">
              <Button 
                variant="outline" 
                onClick={() => setShowAddAvailabilityDialog(true)}
                className="gap-2"
              >
                <Plus size={16} />
                Add Availability
              </Button>
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

          {/* Session Duration Info */}
          {daySchedule.hasAvailability && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground bg-muted/30 rounded-lg px-4 py-2">
              <span className="flex items-center gap-1">
                <Clock size={14} />
                Session: {daySchedule.sessionDuration} min
              </span>
              {daySchedule.bufferTime > 0 && (
                <span>Buffer: {daySchedule.bufferTime} min</span>
              )}
            </div>
          )}

          {/* Full Day Blocked Warning */}
          {daySchedule.isFullDayBlocked && (
            <Card className="p-4 bg-red-50 border-red-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-red-700">
                  <Ban size={20} />
                  <div>
                    <p className="font-medium">Day is Blocked</p>
                    <p className="text-sm opacity-80">
                      {daySchedule.blockedPeriods.find(b => b.is_all_day)?.reason || 'No availability for this day'}
                    </p>
                  </div>
                </div>
                {!isReadOnly && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const block = daySchedule.blockedPeriods.find(b => b.is_all_day);
                      if (block) handleRemoveBlock(block.id);
                    }}
                    className="text-red-700 border-red-300 hover:bg-red-100"
                  >
                    <X size={14} className="mr-1" /> Remove Block
                  </Button>
                )}
              </div>
            </Card>
          )}

          {/* Availability Time Blocks */}
          {daySchedule.hasAvailability && daySchedule.timeBlocks && (
            <Card className="overflow-hidden">
              <div className="p-4 bg-green-50 border-b border-green-100">
                <h3 className="font-semibold text-green-800 flex items-center gap-2">
                  <Clock size={18} />
                  Availability Blocks
                </h3>
              </div>
              <div className="p-4 space-y-2">
                {daySchedule.timeBlocks.map((block, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-green-50/50 rounded-lg border border-green-100">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-8 bg-green-500 rounded-full"></div>
                      <div>
                        <p className="font-medium text-green-800">
                          {block.start_time} – {block.end_time}
                        </p>
                        <p className="text-sm text-green-600">
                          {Math.floor((timeToMinutes(block.end_time) - timeToMinutes(block.start_time)) / 60)}h {(timeToMinutes(block.end_time) - timeToMinutes(block.start_time)) % 60}m
                        </p>
                      </div>
                    </div>
                    {!isReadOnly && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveAvailability(idx)}
                        className="text-green-700 hover:text-red-600 hover:bg-red-50"
                      >
                        <Trash2 size={14} />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* No Availability Warning */}
          {!daySchedule.hasAvailability && !daySchedule.isFullDayBlocked && (
            <Card className="p-6 text-center bg-amber-50 border-amber-200">
              <AlertTriangle size={32} className="mx-auto text-amber-500 mb-3" />
              <p className="font-medium text-amber-800 mb-2">No Availability Set</p>
              <p className="text-sm text-amber-600 mb-4">
                You haven't set any availability for {selectedDate.toLocaleDateString('en-IN', { weekday: 'long' })}s
              </p>
              {!isReadOnly && (
                <Button onClick={() => setShowAddAvailabilityDialog(true)} className="gap-2">
                  <Plus size={16} />
                  Add Availability
                </Button>
              )}
            </Card>
          )}

          {/* Blocked Time Periods (non-full-day) */}
          {daySchedule.blockedPeriods?.filter(b => !b.is_all_day).length > 0 && (
            <Card className="overflow-hidden">
              <div className="p-4 bg-red-50 border-b border-red-100">
                <h3 className="font-semibold text-red-800 flex items-center gap-2">
                  <Ban size={18} />
                  Blocked Times
                </h3>
              </div>
              <div className="p-4 space-y-2">
                {daySchedule.blockedPeriods.filter(b => !b.is_all_day).map((block) => (
                  <div key={block.id} className="flex items-center justify-between p-3 bg-red-50/50 rounded-lg border border-red-100">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-8 bg-red-500 rounded-full"></div>
                      <div>
                        <p className="font-medium text-red-800">
                          {formatTime24(block.start_datetime)} – {formatTime24(block.end_datetime)}
                        </p>
                        {block.reason && (
                          <p className="text-sm text-red-600">{block.reason}</p>
                        )}
                      </div>
                    </div>
                    {!isReadOnly && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveBlock(block.id)}
                        className="text-red-700 hover:bg-red-100"
                      >
                        <X size={14} />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Booked Sessions */}
          {daySchedule.bookedSessions.length > 0 && (
            <Card className="overflow-hidden">
              <div className="p-4 bg-primary/10 border-b border-primary/20">
                <h3 className="font-semibold text-primary flex items-center gap-2">
                  <User size={18} />
                  Booked Sessions ({daySchedule.bookedSessions.length})
                </h3>
              </div>
              <div className="p-4 space-y-3">
                {daySchedule.bookedSessions.map((appt) => (
                  <div 
                    key={appt.id} 
                    className={`p-4 rounded-xl border-2 ${
                      appt.status === 'completed' ? 'bg-green-50 border-green-200' :
                      appt.status === 'in_progress' ? 'bg-amber-50 border-amber-200' :
                      'bg-primary/5 border-primary/20'
                    }`}
                    data-testid={`booked-session-${appt.id}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-medium flex-shrink-0 ${
                          appt.status === 'completed' ? 'bg-green-200 text-green-800' :
                          appt.status === 'in_progress' ? 'bg-amber-200 text-amber-800' :
                          'bg-primary/20 text-primary'
                        }`}>
                          {appt.client_name?.charAt(0) || 'C'}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-semibold text-foreground truncate">{appt.client_name}</p>
                          <p className="text-sm text-muted-foreground font-medium">
                            {formatTime24(appt.start_time)} – {formatTime24(appt.end_time)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                          appt.status === 'completed' ? 'bg-green-200 text-green-800' :
                          appt.status === 'in_progress' ? 'bg-amber-200 text-amber-800 animate-pulse' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {appt.status === 'in_progress' ? 'In Progress' : appt.status}
                        </span>
                        {!isReadOnly && appt.status === 'scheduled' && (
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedAppointment(appt);
                                setShowEditDialog(true);
                              }}
                              className="h-8 w-8 p-0"
                            >
                              <Edit2 size={14} />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCancelAppointment(appt.id)}
                              className="h-8 w-8 p-0 text-red-600 hover:bg-red-50"
                            >
                              <Trash2 size={14} />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                    {appt.notes && (
                      <p className="text-sm text-muted-foreground mt-2 pl-15">
                        {appt.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Available Slots */}
          {daySchedule.availableSlots.length > 0 && (
            <Card className="overflow-hidden">
              <div className="p-4 bg-green-50 border-b border-green-100">
                <h3 className="font-semibold text-green-800 flex items-center gap-2">
                  <CalendarPlus size={18} />
                  Available Slots ({daySchedule.availableSlots.length})
                </h3>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                  {daySchedule.availableSlots.map((slot) => (
                    <Button
                      key={slot.id}
                      variant="outline"
                      onClick={() => openScheduleDialog(slot)}
                      disabled={isReadOnly}
                      className="h-auto py-3 flex flex-col items-center gap-1 border-green-200 hover:bg-green-50 hover:border-green-400"
                      data-testid={`available-slot-${slot.startTime}`}
                    >
                      <span className="font-semibold text-green-700">{slot.startTime}</span>
                      <span className="text-xs text-green-600">– {slot.endTime}</span>
                    </Button>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {/* Empty State - Has availability but no slots */}
          {daySchedule.hasAvailability && daySchedule.availableSlots.length === 0 && daySchedule.bookedSessions.length === 0 && !daySchedule.isFullDayBlocked && (
            <Card className="p-6 text-center">
              <CalendarDays size={32} className="mx-auto text-muted-foreground mb-3" />
              <p className="font-medium text-foreground mb-1">No Sessions Scheduled</p>
              <p className="text-sm text-muted-foreground">
                Your availability is set but no sessions are booked yet
              </p>
            </Card>
          )}
        </div>
      )}

      {/* Schedule Appointment Dialog */}
      <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Schedule Appointment</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleScheduleAppointment} className="space-y-4">
            <div className="p-3 bg-primary/10 rounded-lg">
              <p className="text-sm text-muted-foreground">Date & Time</p>
              <p className="font-semibold text-primary">
                {selectedDate && formatDateDMY(selectedDate)} • {selectedSlot?.startTime} – {selectedSlot?.endTime}
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
              <div className="p-3 bg-muted/50 rounded-lg">
                <p className="font-medium">{selectedAppointment.client_name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatTime24(selectedAppointment.start_time)} – {formatTime24(selectedAppointment.end_time)}
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
            <div className="p-3 bg-red-50 rounded-lg">
              <p className="text-sm text-red-600">Blocking time for</p>
              <p className="font-semibold text-red-800">
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
              <Button type="submit" variant="destructive" className="flex-1">
                Block Time
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Availability Dialog */}
      <Dialog open={showAddAvailabilityDialog} onOpenChange={setShowAddAvailabilityDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Availability</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddAvailability} className="space-y-4">
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600">Adding availability for</p>
              <p className="font-semibold text-green-800">
                {selectedDate && formatDateDMY(selectedDate)} ({selectedDate?.toLocaleDateString('en-IN', { weekday: 'long' })})
              </p>
              <p className="text-xs text-green-600 mt-1">
                This will apply to all {selectedDate?.toLocaleDateString('en-IN', { weekday: 'long' })}s
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="avail-start">Start Time *</Label>
                <Input
                  id="avail-start"
                  type="time"
                  value={newAvailability.start_time}
                  onChange={(e) => setNewAvailability({ ...newAvailability, start_time: e.target.value })}
                  className="mt-1"
                  required
                />
              </div>
              <div>
                <Label htmlFor="avail-end">End Time *</Label>
                <Input
                  id="avail-end"
                  type="time"
                  value={newAvailability.end_time}
                  onChange={(e) => setNewAvailability({ ...newAvailability, end_time: e.target.value })}
                  className="mt-1"
                  required
                />
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowAddAvailabilityDialog(false)} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" className="flex-1 bg-green-600 hover:bg-green-700">
                Add Availability
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
