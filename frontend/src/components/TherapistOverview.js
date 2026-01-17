import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Calendar, Users, FileText, DollarSign } from 'lucide-react';
import { toast } from 'sonner';

const TherapistOverview = () => {
  const [stats, setStats] = useState({
    clients: 0,
    todayAppointments: 0,
    pendingNotes: 0,
    monthlyRevenue: 0,
  });
  const [todayAppointments, setTodayAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverviewData();
  }, []);

  const fetchOverviewData = async () => {
    try {
      const [clientsRes, apptsRes, paymentsRes] = await Promise.all([
        axios.get(`${API}/clients`),
        axios.get(`${API}/appointments`),
        axios.get(`${API}/payments`),
      ]);

      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);

      const todayAppts = apptsRes.data.filter((appt) => {
        const apptDate = new Date(appt.start_time);
        return apptDate >= today && apptDate < tomorrow;
      });

      const thisMonth = new Date();
      thisMonth.setDate(1);
      thisMonth.setHours(0, 0, 0, 0);
      const monthlyPayments = paymentsRes.data.filter(
        (p) => new Date(p.created_at) >= thisMonth
      );
      const revenue = monthlyPayments.reduce((sum, p) => sum + p.amount, 0);

      setStats({
        clients: clientsRes.data.length,
        todayAppointments: todayAppts.length,
        pendingNotes: 0,
        monthlyRevenue: revenue,
      });

      setTodayAppointments(todayAppts.sort((a, b) => new Date(a.start_time) - new Date(b.start_time)));
    } catch (error) {
      toast.error('Failed to load overview data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div data-testid="therapist-overview">
      <div className="mb-8">
        <h2 className="text-4xl font-serif text-primary mb-2">Dashboard</h2>
        <p className="text-muted-foreground">Welcome back to your practice</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="stat-clients">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Users className="text-primary" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-primary">{stats.clients}</p>
              <p className="text-sm text-muted-foreground">Total Clients</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="stat-appointments">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-secondary/10 rounded-lg">
              <Calendar className="text-secondary" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-primary">{stats.todayAppointments}</p>
              <p className="text-sm text-muted-foreground">Today's Sessions</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="stat-notes">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-info/10 rounded-lg">
              <FileText className="text-info" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-primary">{stats.pendingNotes}</p>
              <p className="text-sm text-muted-foreground">Pending Notes</p>
            </div>
          </div>
        </Card>

        <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="stat-revenue">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-success/10 rounded-lg">
              <DollarSign className="text-success" size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-primary">${stats.monthlyRevenue.toFixed(0)}</p>
              <p className="text-sm text-muted-foreground">This Month</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Today's Appointments */}
      <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="today-appointments">
        <h3 className="text-2xl font-serif text-primary mb-4">Today's Schedule</h3>
        {todayAppointments.length === 0 ? (
          <p className="text-muted-foreground">No appointments scheduled for today</p>
        ) : (
          <div className="space-y-3">
            {todayAppointments.map((appt) => (
              <div
                key={appt.id}
                className="p-4 bg-surface rounded-lg border border-border flex items-center justify-between"
                data-testid={`appointment-${appt.id}`}
              >
                <div>
                  <p className="font-medium text-foreground">{appt.client_name}</p>
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
                </div>
                {appt.notes && (
                  <p className="text-sm text-muted-foreground max-w-md">{appt.notes}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Clinical Disclaimer */}
      <div className="mt-8 p-6 bg-info/10 border border-info/20 rounded-xl">
        <p className="text-sm text-info">
          <strong>Clinical Support Tool:</strong> This platform provides decision support. All clinical
          judgments and treatment decisions remain with the licensed therapist.
        </p>
      </div>
    </div>
  );
};

export default TherapistOverview;
