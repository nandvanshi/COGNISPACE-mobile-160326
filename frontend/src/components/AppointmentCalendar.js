import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Plus, Calendar as CalendarIcon } from 'lucide-react';

const AppointmentCalendar = () => {
  const [appointments, setAppointments] = useState([]);
  const [clients, setClients] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [newAppt, setNewAppt] = useState({
    client_id: '',
    start_time: '',
    end_time: '',
    notes: '',
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
      setAppointments(apptsRes.data.sort((a, b) => new Date(b.start_time) - new Date(a.start_time)));
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

    try {
      await axios.post(`${API}/appointments`, {
        client_id: newAppt.client_id,
        start_time: new Date(newAppt.start_time).toISOString(),
        end_time: new Date(newAppt.end_time).toISOString(),
        notes: newAppt.notes,
      });
      toast.success('Appointment scheduled');
      setShowDialog(false);
      setNewAppt({ client_id: '', start_time: '', end_time: '', notes: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create appointment');
    }
  };

  const groupAppointmentsByDate = () => {
    const grouped = {};
    appointments.forEach((appt) => {
      const date = new Date(appt.start_time).toLocaleDateString();
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(appt);
    });
    return grouped;
  };

  const groupedAppointments = groupAppointmentsByDate();

  if (loading) {
    return <div className="text-center py-12">Loading appointments...</div>;
  }

  return (
    <div data-testid="appointment-calendar">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Appointments</h2>
          <p className="text-muted-foreground">Schedule and manage client sessions</p>
        </div>
        <Button
          onClick={() => setShowDialog(true)}
          className="bg-primary hover:bg-primary-700 rounded-full"
          data-testid="create-appointment-button"
        >
          <Plus size={20} className="mr-2" />
          New Appointment
        </Button>
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
                  className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
                  data-testid={`appointment-${appt.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-lg text-foreground">{appt.client_name}</p>
                      <p className="text-sm text-muted-foreground">
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
                      {appt.notes && (
                        <p className="text-sm text-muted-foreground mt-2">{appt.notes}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                          appt.status === 'scheduled'
                            ? 'bg-info/10 text-info'
                            : 'bg-success/10 text-success'
                        }`}
                      >
                        {appt.status}
                      </span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ))}

        {appointments.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No appointments scheduled</p>
          </div>
        )}
      </div>

      {/* Create Appointment Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="appointment-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">
              Schedule Appointment
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateAppointment} className="space-y-4">
            <div>
              <Label htmlFor="client">Client</Label>
              <select
                id="client"
                data-testid="appointment-client-select"
                value={newAppt.client_id}
                onChange={(e) => setNewAppt({ ...newAppt, client_id: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
                required
              >
                <option value="">Select a client</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="start-time">Start Time</Label>
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
              <Label htmlFor="end-time">End Time</Label>
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
            <div>
              <Label htmlFor="notes">Notes (optional)</Label>
              <Input
                id="notes"
                data-testid="appointment-notes-input"
                value={newAppt.notes}
                onChange={(e) => setNewAppt({ ...newAppt, notes: e.target.value })}
                placeholder="Session focus or reminders..."
                className="mt-1"
              />
            </div>
            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="save-appointment-button">
                Schedule
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                data-testid="cancel-appointment-button"
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
