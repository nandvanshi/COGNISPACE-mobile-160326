import React, { useState, useEffect } from 'react';
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
import { Plus, Calendar as CalendarIcon, Clock, User, Edit, Check, X, Trash2, ChevronLeft, ChevronRight, Settings, Ban, AlertTriangle } from 'lucide-react';
import { formatDate, formatTime, formatTimeRange, formatGroupDate, getTodayInputFormat, isoToInputFormat } from '../utils/formatUtils';

const AppointmentCalendar = ({ isReadOnly = false }) => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [blockedTimes, setBlockedTimes] = useState([]);
  const [clients, setClients] = useState([]);
  const [availability, setAvailability] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showBlockDialog, setShowBlockDialog] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [viewMode, setViewMode] = useState('appointments'); // 'appointments' or 'blocked'
  const [bookingMode, setBookingMode] = useState('slots');
  const [newAppt, setNewAppt] = useState({
    client_id: '',
    selected_slot: null,
    start_time: '',
    end_time: '',
    notes: '',
  });
  const [editAppt, setEditAppt] = useState({
    start_time: '',
    end_time: '',
    notes: '',
    status: '',
  });
  const [newBlock, setNewBlock] = useState({
    is_all_day: false,
    date: '',
    start_time: '',
    end_time: '',
    reason: '',
  });
  const [loading, setLoading] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedDate && user) {
      fetchAvailableSlots(selectedDate);
    }
  }, [selectedDate]);

  const fetchData = async () => {
    try {
      const [apptsRes, clientsRes, availRes, blockedRes] = await Promise.all([
        axios.get(`${API}/appointments`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/availability`).catch(() => ({ data: null })),
        axios.get(`${API}/blocked-times`).catch(() => ({ data: [] })),
      ]);
      setAppointments(apptsRes.data.sort((a, b) => new Date(a.start_time) - new Date(b.start_time)));
      setClients(clientsRes.data);
      setAvailability(availRes.data);
      setBlockedTimes(blockedRes.data || []);
    } catch (error) {
      toast.error('Failed to load calendar data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableSlots = async (date) => {
    if (!user?.id) return;
    setLoadingSlots(true);
    try {
      // For assistants, use the therapist_id
      const therapistId = user.role === 'assistant' ? user.therapist_id : user.id;
      const response = await axios.get(`${API}/available-slots/${therapistId}?date=${date}`);
      setAvailableSlots(response.data);
    } catch (error) {
      console.error('Failed to fetch available slots:', error);
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleCreateAppointment = async (e) => {
    e.preventDefault();

    if (!newAppt.client_id) {
      toast.error('Please select a client');
      return;
    }

    let startTime, endTime;

    if (bookingMode === 'slots' && newAppt.selected_slot) {
      startTime = new Date(newAppt.selected_slot.start_time);
      endTime = new Date(newAppt.selected_slot.end_time);
    } else if (bookingMode === 'manual' && newAppt.start_time && newAppt.end_time) {
      startTime = new Date(newAppt.start_time);
      endTime = new Date(newAppt.end_time);
    } else {
      toast.error('Please select a time slot or enter times manually');
      return;
    }

    if (endTime <= startTime) {
      toast.error('End time must be after start time');
      return;
    }

    try {
      await axios.post(`${API}/appointments`, {
        client_id: newAppt.client_id,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        notes: newAppt.notes,
      });
      toast.success('Appointment scheduled successfully');
      setShowCreateDialog(false);
      setNewAppt({ client_id: '', selected_slot: null, start_time: '', end_time: '', notes: '' });
      setSelectedDate('');
      setAvailableSlots([]);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create appointment');
    }
  };

  const handleEditAppointment = async (e) => {
    e.preventDefault();

    if (!selectedAppointment) return;

    const updateData = {};
    
    if (editAppt.start_time) {
      updateData.start_time = new Date(editAppt.start_time).toISOString();
    }
    if (editAppt.end_time) {
      updateData.end_time = new Date(editAppt.end_time).toISOString();
    }
    if (editAppt.notes !== undefined) {
      updateData.notes = editAppt.notes;
    }
    if (editAppt.status && editAppt.status !== selectedAppointment.status) {
      updateData.status = editAppt.status;
    }

    const newStart = editAppt.start_time ? new Date(editAppt.start_time) : new Date(selectedAppointment.start_time);
    const newEnd = editAppt.end_time ? new Date(editAppt.end_time) : new Date(selectedAppointment.end_time);
    
    if (newEnd <= newStart) {
      toast.error('End time must be after start time');
      return;
    }

    try {
      await axios.put(`${API}/appointments/${selectedAppointment.id}`, updateData);
      toast.success('Appointment updated successfully');
      setShowEditDialog(false);
      setSelectedAppointment(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update appointment');
    }
  };

  const handleCompleteAppointment = async (appointmentId) => {
    try {
      await axios.post(`${API}/appointments/${appointmentId}/complete`);
      toast.success('Appointment marked as completed');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete appointment');
    }
  };

  const handleCancelAppointment = async (appointmentId) => {
    if (!window.confirm('Are you sure you want to cancel this appointment?')) return;
    
    try {
      await axios.post(`${API}/appointments/${appointmentId}/cancel`);
      toast.success('Appointment cancelled');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel appointment');
    }
  };

  const handleDeleteAppointment = async (appointmentId) => {
    if (!window.confirm('Are you sure you want to delete this appointment? This action cannot be undone.')) return;
    
    try {
      await axios.delete(`${API}/appointments/${appointmentId}`);
      toast.success('Appointment deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete appointment');
    }
  };

  // Calendar Blocking Functions
  const handleBlockTime = async (e) => {
    e.preventDefault();

    if (!newBlock.date) {
      toast.error('Please select a date');
      return;
    }

    let startDatetime, endDatetime;

    if (newBlock.is_all_day) {
      // Full day block
      startDatetime = new Date(`${newBlock.date}T00:00:00`);
      endDatetime = new Date(`${newBlock.date}T23:59:59`);
    } else {
      if (!newBlock.start_time || !newBlock.end_time) {
        toast.error('Please enter start and end times');
        return;
      }
      startDatetime = new Date(`${newBlock.date}T${newBlock.start_time}`);
      endDatetime = new Date(`${newBlock.date}T${newBlock.end_time}`);
      
      if (endDatetime <= startDatetime) {
        toast.error('End time must be after start time');
        return;
      }
    }

    // Check for conflicting appointments
    const conflictingAppts = appointments.filter(appt => {
      if (appt.status === 'cancelled') return false;
      const apptStart = new Date(appt.start_time);
      const apptEnd = new Date(appt.end_time);
      return apptStart < endDatetime && apptEnd > startDatetime;
    });

    if (conflictingAppts.length > 0) {
      toast.error(`Cannot block this time: ${conflictingAppts.length} existing appointment(s) would be affected. Please cancel or reschedule them first.`);
      return;
    }

    try {
      await axios.post(`${API}/blocked-times`, {
        start_datetime: startDatetime.toISOString(),
        end_datetime: endDatetime.toISOString(),
        reason: newBlock.reason || 'Blocked',
        is_all_day: newBlock.is_all_day,
      });
      toast.success('Time blocked successfully');
      setShowBlockDialog(false);
      setNewBlock({ is_all_day: false, date: '', start_time: '', end_time: '', reason: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to block time');
    }
  };

  const handleUnblockTime = async (blockId) => {
    if (!window.confirm('Are you sure you want to remove this time block?')) return;
    
    try {
      await axios.delete(`${API}/blocked-times/${blockId}`);
      toast.success('Time block removed');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove block');
    }
  };

  const openEditDialog = (appt) => {
    setSelectedAppointment(appt);
    setEditAppt({
      start_time: formatDateTimeLocal(appt.start_time),
      end_time: formatDateTimeLocal(appt.end_time),
      notes: appt.notes || '',
      status: appt.status,
    });
    setShowEditDialog(true);
  };

  const formatDateTimeLocal = (dateStr) => {
    return isoToInputFormat(dateStr);
  };

  const groupAppointmentsByDate = () => {
    const grouped = {};
    const filteredAppts = filterStatus === 'all' 
      ? appointments 
      : appointments.filter(a => a.status === filterStatus);
    
    filteredAppts.forEach((appt) => {
      const date = formatGroupDate(appt.start_time);
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(appt);
    });
    return grouped;
  };

  const groupBlockedTimesByDate = () => {
    const grouped = {};
    blockedTimes.forEach((block) => {
      const date = formatGroupDate(block.start_datetime);
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(block);
    });
    return grouped;
  };

  const getStatusBadge = (status) => {
    const styles = {
      scheduled: 'bg-info/10 text-info border-info/20',
      completed: 'bg-success/10 text-success border-success/20',
      cancelled: 'bg-error/10 text-error border-error/20',
    };
    return styles[status] || styles.scheduled;
  };

  const getUpcomingAppointments = () => {
    const now = new Date();
    return appointments
      .filter(a => new Date(a.start_time) >= now && a.status === 'scheduled')
      .slice(0, 5);
  };

  const getTodaysAppointments = () => {
    const today = new Date().toDateString();
    return appointments.filter(a => new Date(a.start_time).toDateString() === today);
  };

  const getUpcomingBlockedTimes = () => {
    const now = new Date();
    return blockedTimes.filter(b => new Date(b.end_datetime) >= now);
  };

  const hasAvailabilitySetup = () => {
    if (!availability) return false;
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    return days.some(day => availability[day]?.enabled && availability[day]?.time_blocks?.length > 0);
  };

  const groupedAppointments = groupAppointmentsByDate();
  const groupedBlockedTimes = groupBlockedTimesByDate();
  const upcomingAppointments = getUpcomingAppointments();
  const todaysAppointments = getTodaysAppointments();
  const upcomingBlocks = getUpcomingBlockedTimes();

  if (loading) {
    return <div className="text-center py-12">Loading appointments...</div>;
  }

  return (
    <div data-testid="appointment-calendar">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Appointments</h2>
          <p className="text-muted-foreground">Schedule and manage client sessions</p>
        </div>
        <div className="flex gap-2">
          {!isReadOnly && (
            <>
              <Button
                onClick={() => setShowBlockDialog(true)}
                variant="outline"
                className="border-warning text-warning hover:bg-warning/10"
                data-testid="block-time-button"
              >
                <Ban size={20} className="mr-2" />
                Block Time
              </Button>
              <Button
                onClick={() => setShowCreateDialog(true)}
                className="bg-primary hover:bg-primary-700 rounded-full"
                data-testid="create-appointment-button"
              >
                <Plus size={20} className="mr-2" />
                New Appointment
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Availability Setup Notice */}
      {!hasAvailabilitySetup() && !isReadOnly && user?.role === 'therapist' && (
        <Card className="p-4 mb-6 bg-warning/10 border-warning/30">
          <div className="flex items-center gap-3">
            <Settings size={20} className="text-warning" />
            <div className="flex-1">
              <p className="font-medium text-foreground">Set up your availability</p>
              <p className="text-sm text-muted-foreground">
                Define your working hours to enable slot-based booking. Go to Availability settings.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-info/10 flex items-center justify-center">
              <CalendarIcon size={20} className="text-info" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{todaysAppointments.length}</p>
              <p className="text-sm text-muted-foreground">Today's Sessions</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-success/10 flex items-center justify-center">
              <Check size={20} className="text-success" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {appointments.filter(a => a.status === 'completed').length}
              </p>
              <p className="text-sm text-muted-foreground">Completed</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-warning/10 flex items-center justify-center">
              <Clock size={20} className="text-warning" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{upcomingAppointments.length}</p>
              <p className="text-sm text-muted-foreground">Upcoming</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-error/10 flex items-center justify-center">
              <Ban size={20} className="text-error" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{upcomingBlocks.length}</p>
              <p className="text-sm text-muted-foreground">Blocked Times</p>
            </div>
          </div>
        </Card>
      </div>

      {/* View Toggle & Filter */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-4">
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'appointments' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('appointments')}
            data-testid="view-appointments-btn"
          >
            <CalendarIcon size={16} className="mr-2" />
            Appointments
          </Button>
          <Button
            variant={viewMode === 'blocked' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('blocked')}
            data-testid="view-blocked-btn"
          >
            <Ban size={16} className="mr-2" />
            Blocked Times ({blockedTimes.length})
          </Button>
        </div>
        
        {viewMode === 'appointments' && (
          <div className="flex items-center gap-4">
            <Label className="text-sm font-medium">Filter:</Label>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40" data-testid="filter-status-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Appointments View */}
      {viewMode === 'appointments' && (
        <div className="space-y-8">
          {Object.entries(groupedAppointments).map(([date, appts]) => (
            <div key={date}>
              <h3 className="text-xl font-serif text-primary mb-4 flex items-center gap-2">
                <CalendarIcon size={20} />
                {date}
              </h3>
              <div className="space-y-3">
                {appts.map((appt) => (
                  <Card
                    key={appt.id}
                    className={`p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl transition-all hover:shadow-md ${
                      appt.status === 'cancelled' ? 'opacity-60' : ''
                    }`}
                    data-testid={`appointment-${appt.id}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <User size={18} className="text-primary" />
                          </div>
                          <div>
                            <p className="font-medium text-lg text-foreground">{appt.client_name}</p>
                            <p className="text-sm text-muted-foreground flex items-center gap-1">
                              <Clock size={14} />
                              {formatTimeRange(appt.start_time, appt.end_time)}
                            </p>
                          </div>
                        </div>
                        {appt.notes && (
                          <p className="text-sm text-muted-foreground mt-2 pl-13 ml-13">{appt.notes}</p>
                        )}
                      </div>
                      
                      <div className="flex flex-col items-end gap-2">
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${getStatusBadge(appt.status)}`}
                          data-testid={`appointment-status-${appt.id}`}
                        >
                          {appt.status.charAt(0).toUpperCase() + appt.status.slice(1)}
                        </span>
                        
                        {!isReadOnly && appt.status === 'scheduled' && (
                          <div className="flex gap-1 mt-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditDialog(appt)}
                              className="h-8 w-8 p-0"
                              data-testid={`edit-appointment-${appt.id}`}
                            >
                              <Edit size={14} />
                            </Button>
                            {user?.role === 'therapist' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleCompleteAppointment(appt.id)}
                                className="h-8 w-8 p-0 text-success hover:text-success hover:bg-success/10"
                                data-testid={`complete-appointment-${appt.id}`}
                              >
                                <Check size={14} />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCancelAppointment(appt.id)}
                              className="h-8 w-8 p-0 text-error hover:text-error hover:bg-error/10"
                              data-testid={`cancel-appointment-${appt.id}`}
                            >
                              <X size={14} />
                            </Button>
                          </div>
                        )}
                        
                        {!isReadOnly && appt.status !== 'scheduled' && user?.role === 'therapist' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteAppointment(appt.id)}
                            className="h-8 w-8 p-0 text-muted-foreground hover:text-error"
                            data-testid={`delete-appointment-${appt.id}`}
                          >
                            <Trash2 size={14} />
                          </Button>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ))}

          {Object.keys(groupedAppointments).length === 0 && (
            <div className="text-center py-12">
              <CalendarIcon size={48} className="mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">
                {filterStatus === 'all' ? 'No appointments scheduled' : `No ${filterStatus} appointments`}
              </p>
              {!isReadOnly && filterStatus === 'all' && (
                <Button
                  onClick={() => setShowCreateDialog(true)}
                  variant="outline"
                  className="mt-4"
                >
                  Schedule your first appointment
                </Button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Blocked Times View */}
      {viewMode === 'blocked' && (
        <div className="space-y-8">
          {/* Info Banner */}
          <Card className="p-4 bg-error/5 border-error/20">
            <div className="flex items-center gap-3">
              <AlertTriangle size={20} className="text-error" />
              <div>
                <p className="font-medium">Blocked times prevent new bookings</p>
                <p className="text-sm text-muted-foreground">
                  Use this for holidays, leave, personal time, or offline bookings.
                </p>
              </div>
            </div>
          </Card>

          {Object.entries(groupedBlockedTimes).length > 0 ? (
            Object.entries(groupedBlockedTimes).map(([date, blocks]) => (
              <div key={date}>
                <h3 className="text-xl font-serif text-primary mb-4 flex items-center gap-2">
                  <Ban size={20} />
                  {date}
                </h3>
                <div className="space-y-3">
                  {blocks.map((block) => (
                    <Card
                      key={block.id}
                      className="p-6 bg-error/5 border-error/20 rounded-xl"
                      data-testid={`blocked-time-${block.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-error/10 flex items-center justify-center">
                            <Ban size={18} className="text-error" />
                          </div>
                          <div>
                            <p className="font-medium text-lg">
                              {block.is_all_day ? (
                                <span className="text-error">Full Day Blocked</span>
                              ) : (
                                <>{formatTimeRange(block.start_datetime, block.end_datetime)}</>
                              )}
                            </p>
                            {block.reason && (
                              <p className="text-sm text-muted-foreground">
                                Reason: {block.reason}
                              </p>
                            )}
                          </div>
                        </div>
                        
                        {!isReadOnly && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleUnblockTime(block.id)}
                            className="text-error hover:bg-error/10"
                            data-testid={`unblock-${block.id}`}
                          >
                            <Trash2 size={16} className="mr-2" />
                            Remove
                          </Button>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-12">
              <Ban size={48} className="mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">No blocked times</p>
              {!isReadOnly && (
                <Button
                  onClick={() => setShowBlockDialog(true)}
                  variant="outline"
                  className="mt-4"
                >
                  Block your first time slot
                </Button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Create Appointment Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-lg" data-testid="create-appointment-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">
              Schedule Appointment
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateAppointment} className="space-y-4">
            <div>
              <Label htmlFor="client">Client *</Label>
              <Select
                value={newAppt.client_id}
                onValueChange={(value) => setNewAppt({ ...newAppt, client_id: value })}
              >
                <SelectTrigger className="mt-1" data-testid="appointment-client-select">
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

            {/* Booking Mode Toggle */}
            {hasAvailabilitySetup() && (
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={bookingMode === 'slots' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setBookingMode('slots')}
                  data-testid="booking-mode-slots"
                >
                  <Clock size={14} className="mr-1" />
                  Available Slots
                </Button>
                <Button
                  type="button"
                  variant={bookingMode === 'manual' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setBookingMode('manual')}
                  data-testid="booking-mode-manual"
                >
                  <CalendarIcon size={14} className="mr-1" />
                  Manual Entry
                </Button>
              </div>
            )}

            {/* Slot-based booking */}
            {(bookingMode === 'slots' && hasAvailabilitySetup()) ? (
              <div className="space-y-3">
                <div>
                  <Label htmlFor="slot-date">Select Date *</Label>
                  <Input
                    id="slot-date"
                    type="date"
                    min={getTodayInputFormat()}
                    value={selectedDate}
                    onChange={(e) => {
                      setSelectedDate(e.target.value);
                      setNewAppt({ ...newAppt, selected_slot: null });
                    }}
                    className="mt-1"
                    data-testid="slot-date-input"
                  />
                </div>

                {selectedDate && (
                  <div>
                    <Label>Available Time Slots</Label>
                    <div className="mt-2 max-h-48 overflow-y-auto space-y-2">
                      {loadingSlots ? (
                        <p className="text-sm text-muted-foreground py-4 text-center">Loading slots...</p>
                      ) : availableSlots.length > 0 ? (
                        availableSlots.map((slot, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => setNewAppt({ ...newAppt, selected_slot: slot })}
                            className={`w-full p-3 rounded-lg border text-left transition-all ${
                              newAppt.selected_slot?.start_time === slot.start_time
                                ? 'border-primary bg-primary/10 ring-2 ring-primary'
                                : 'border-border hover:border-primary/50 hover:bg-surface'
                            }`}
                            data-testid={`time-slot-${idx}`}
                          >
                            <div className="flex items-center gap-2">
                              <Clock size={14} className="text-muted-foreground" />
                              <span className="font-medium">
                                {formatTimeRange(slot.start_time, slot.end_time)}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                ({slot.duration_minutes} min)
                              </span>
                            </div>
                          </button>
                        ))
                      ) : (
                        <div className="text-center py-4">
                          <p className="text-sm text-muted-foreground">No available slots for this date</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Try another date or use manual entry
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {newAppt.selected_slot && (
                  <div className="p-3 bg-success/10 border border-success/30 rounded-lg">
                    <p className="text-sm font-medium text-success">Selected slot:</p>
                    <p className="text-sm">
                      {formatDate(newAppt.selected_slot.start_time)} at {formatTime(newAppt.selected_slot.start_time)}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              /* Manual time entry */
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="start-time">Start Time *</Label>
                  <Input
                    id="start-time"
                    type="datetime-local"
                    data-testid="appointment-start-input"
                    value={newAppt.start_time}
                    onChange={(e) => setNewAppt({ ...newAppt, start_time: e.target.value })}
                    required={bookingMode === 'manual'}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="end-time">End Time *</Label>
                  <Input
                    id="end-time"
                    type="datetime-local"
                    data-testid="appointment-end-input"
                    value={newAppt.end_time}
                    onChange={(e) => setNewAppt({ ...newAppt, end_time: e.target.value })}
                    required={bookingMode === 'manual'}
                    className="mt-1"
                  />
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="notes">Notes (optional)</Label>
              <Input
                id="notes"
                data-testid="appointment-notes-input"
                value={newAppt.notes}
                onChange={(e) => setNewAppt({ ...newAppt, notes: e.target.value })}
                placeholder="Session focus, reminders, or special instructions..."
                className="mt-1"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1" data-testid="save-appointment-button">
                Schedule Appointment
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateDialog(false);
                  setSelectedDate('');
                  setAvailableSlots([]);
                }}
                data-testid="cancel-create-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Appointment Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent data-testid="edit-appointment-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">
              Edit Appointment
            </DialogTitle>
          </DialogHeader>
          {selectedAppointment && (
            <form onSubmit={handleEditAppointment} className="space-y-4">
              <div className="p-3 bg-surface rounded-lg">
                <p className="text-sm text-muted-foreground">Client</p>
                <p className="font-medium">{selectedAppointment.client_name}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="edit-start-time">Start Time</Label>
                  <Input
                    id="edit-start-time"
                    type="datetime-local"
                    data-testid="edit-start-input"
                    value={editAppt.start_time}
                    onChange={(e) => setEditAppt({ ...editAppt, start_time: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="edit-end-time">End Time</Label>
                  <Input
                    id="edit-end-time"
                    type="datetime-local"
                    data-testid="edit-end-input"
                    value={editAppt.end_time}
                    onChange={(e) => setEditAppt({ ...editAppt, end_time: e.target.value })}
                    className="mt-1"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="edit-notes">Notes</Label>
                <Input
                  id="edit-notes"
                  data-testid="edit-notes-input"
                  value={editAppt.notes}
                  onChange={(e) => setEditAppt({ ...editAppt, notes: e.target.value })}
                  placeholder="Session focus, reminders, or special instructions..."
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Status</Label>
                <Select value={editAppt.status} onValueChange={(value) => setEditAppt({ ...editAppt, status: value })}>
                  <SelectTrigger className="mt-1" data-testid="edit-status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="scheduled">Scheduled</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-3 pt-2">
                <Button type="submit" className="flex-1" data-testid="update-appointment-button">
                  Update Appointment
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowEditDialog(false)}
                  data-testid="cancel-edit-button"
                >
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Block Time Dialog */}
      <Dialog open={showBlockDialog} onOpenChange={setShowBlockDialog}>
        <DialogContent data-testid="block-time-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary flex items-center gap-2">
              <Ban size={24} />
              Block Calendar Time
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleBlockTime} className="space-y-4">
            <div className="p-4 bg-warning/10 border border-warning/30 rounded-lg">
              <p className="text-sm text-warning-foreground">
                Blocked time will prevent new appointments from being scheduled during this period. 
                Existing appointments will not be affected.
              </p>
            </div>

            <div>
              <Label htmlFor="block-date">Date *</Label>
              <Input
                id="block-date"
                type="date"
                min={getTodayInputFormat()}
                value={newBlock.date}
                onChange={(e) => setNewBlock({ ...newBlock, date: e.target.value })}
                required
                className="mt-1"
                data-testid="block-date-input"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is-all-day"
                checked={newBlock.is_all_day}
                onChange={(e) => setNewBlock({ ...newBlock, is_all_day: e.target.checked })}
                className="w-4 h-4 rounded border-border"
                data-testid="block-all-day-checkbox"
              />
              <Label htmlFor="is-all-day" className="cursor-pointer">
                Block entire day (holiday/leave)
              </Label>
            </div>

            {!newBlock.is_all_day && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="block-start">Start Time *</Label>
                  <Input
                    id="block-start"
                    type="time"
                    value={newBlock.start_time}
                    onChange={(e) => setNewBlock({ ...newBlock, start_time: e.target.value })}
                    required={!newBlock.is_all_day}
                    className="mt-1"
                    data-testid="block-start-input"
                  />
                </div>
                <div>
                  <Label htmlFor="block-end">End Time *</Label>
                  <Input
                    id="block-end"
                    type="time"
                    value={newBlock.end_time}
                    onChange={(e) => setNewBlock({ ...newBlock, end_time: e.target.value })}
                    required={!newBlock.is_all_day}
                    className="mt-1"
                    data-testid="block-end-input"
                  />
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="block-reason">Reason (optional)</Label>
              <Select
                value={newBlock.reason}
                onValueChange={(value) => setNewBlock({ ...newBlock, reason: value })}
              >
                <SelectTrigger className="mt-1" data-testid="block-reason-select">
                  <SelectValue placeholder="Select a reason" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Leave">Leave</SelectItem>
                  <SelectItem value="Holiday">Holiday</SelectItem>
                  <SelectItem value="Personal">Personal</SelectItem>
                  <SelectItem value="Offline Booking">Offline Booking</SelectItem>
                  <SelectItem value="Training">Training</SelectItem>
                  <SelectItem value="Meeting">Meeting</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1 bg-warning hover:bg-warning/90" data-testid="confirm-block-button">
                <Ban size={16} className="mr-2" />
                Block Time
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowBlockDialog(false);
                  setNewBlock({ is_all_day: false, date: '', start_time: '', end_time: '', reason: '' });
                }}
                data-testid="cancel-block-button"
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

export default AppointmentCalendar;
