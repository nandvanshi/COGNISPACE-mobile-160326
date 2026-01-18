import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { Plus, Calendar as CalendarIcon, Clock, User, Edit, Check, X, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';

const AppointmentCalendar = ({ isReadOnly = false }) => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [clients, setClients] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'calendar'
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [filterStatus, setFilterStatus] = useState('all');
  const [newAppt, setNewAppt] = useState({
    client_id: '',
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [apptsRes, clientsRes] = await Promise.all([
        axios.get(`${API}/appointments`),
        axios.get(`${API}/clients`),
      ]);
      setAppointments(apptsRes.data.sort((a, b) => new Date(a.start_time) - new Date(b.start_time)));
      setClients(clientsRes.data);
    } catch (error) {
      toast.error('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAppointment = async (e) => {
    e.preventDefault();

    if (!newAppt.client_id || !newAppt.start_time || !newAppt.end_time) {
      toast.error('Please fill in all required fields');
      return;
    }

    const startTime = new Date(newAppt.start_time);
    const endTime = new Date(newAppt.end_time);
    
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
      setNewAppt({ client_id: '', start_time: '', end_time: '', notes: '' });
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

    // Validate times
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
    const date = new Date(dateStr);
    return date.toISOString().slice(0, 16);
  };

  const groupAppointmentsByDate = () => {
    const grouped = {};
    const filteredAppts = filterStatus === 'all' 
      ? appointments 
      : appointments.filter(a => a.status === filterStatus);
    
    filteredAppts.forEach((appt) => {
      const date = new Date(appt.start_time).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(appt);
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

  const groupedAppointments = groupAppointmentsByDate();
  const upcomingAppointments = getUpcomingAppointments();
  const todaysAppointments = getTodaysAppointments();

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
        {!isReadOnly && (
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="create-appointment-button"
          >
            <Plus size={20} className="mr-2" />
            New Appointment
          </Button>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
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
      </div>

      {/* Filter */}
      <div className="mb-6 flex items-center gap-4">
        <Label className="text-sm font-medium">Filter by status:</Label>
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

      {/* Appointments List */}
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
                            {new Date(appt.start_time).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}{' '}
                            -{' '}
                            {new Date(appt.end_time).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
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
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCompleteAppointment(appt.id)}
                            className="h-8 w-8 p-0 text-success hover:text-success hover:bg-success/10"
                            data-testid={`complete-appointment-${appt.id}`}
                          >
                            <Check size={14} />
                          </Button>
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
                      
                      {!isReadOnly && appt.status !== 'scheduled' && (
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

      {/* Create Appointment Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent data-testid="create-appointment-dialog">
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
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start-time">Start Time *</Label>
                <Input
                  id="start-time"
                  type="datetime-local"
                  data-testid="appointment-start-input"
                  value={newAppt.start_time}
                  onChange={(e) => setNewAppt({ ...newAppt, start_time: e.target.value })}
                  required
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
                  required
                  className="mt-1"
                />
              </div>
            </div>
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
                onClick={() => setShowCreateDialog(false)}
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
    </div>
  );
};

export default AppointmentCalendar;
