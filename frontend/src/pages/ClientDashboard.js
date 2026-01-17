import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API } from '../App';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { LogOut, Calendar, MessageSquare, ClipboardCheck, Home, BookCheck } from 'lucide-react';
import { toast } from 'sonner';

const ClientDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState([]);
  const [homework, setHomework] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState('overview');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [apptsRes, hwRes, assessRes] = await Promise.all([
        axios.get(`${API}/appointments`),
        axios.get(`${API}/homework`),
        axios.get(`${API}/assessments`),
      ]);
      setAppointments(apptsRes.data);
      setHomework(hwRes.data);
      setAssessments(assessRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteHomework = async (hwId) => {
    const notes = prompt('Add your notes about this homework:');
    if (!notes) return;

    try {
      await axios.post(`${API}/homework/${hwId}/complete`, { client_notes: notes });
      toast.success('Homework marked as complete');
      fetchData();
    } catch (error) {
      toast.error('Failed to complete homework');
    }
  };

  const handleCompleteAssessment = async (assessment) => {
    if (assessment.status === 'completed') {
      toast.info('Assessment already completed');
      return;
    }

    const answers = [];
    for (const question of assessment.questions) {
      const answer = prompt(`${question.q}\n\nOptions: ${question.options.join(', ')}`);
      if (!answer) return;
      const optionIndex = question.options.indexOf(answer);
      answers.push({ question: question.q, answer, score: optionIndex >= 0 ? optionIndex : 0 });
    }

    try {
      await axios.post(`${API}/assessments/${assessment.id}/submit`, { answers });
      toast.success('Assessment submitted successfully');
      fetchData();
    } catch (error) {
      toast.error('Failed to submit assessment');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const upcomingAppointments = appointments
    .filter((a) => new Date(a.start_time) > new Date())
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
    .slice(0, 3);

  const pendingHomework = homework.filter((h) => h.status === 'assigned');
  const pendingAssessments = assessments.filter((a) => a.status === 'assigned');

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-surface border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-serif text-primary">Haven</h1>
            <p className="text-sm text-muted-foreground">Welcome, {user?.full_name}</p>
          </div>
          <Button
            onClick={handleLogout}
            variant="ghost"
            data-testid="client-logout-button"
          >
            <LogOut size={20} className="mr-2" />
            Logout
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6 md:p-12">
        <div className="mb-8">
          <h2 className="text-4xl font-serif text-primary mb-2">Your Dashboard</h2>
          <p className="text-muted-foreground">Manage your therapy journey</p>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Upcoming Appointments - Span 8 cols */}
          <Card className="md:col-span-8 p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="upcoming-appointments-card">
            <div className="flex items-center gap-3 mb-4">
              <Calendar className="text-primary" size={24} />
              <h3 className="text-2xl font-serif text-primary">Upcoming Appointments</h3>
            </div>
            {upcomingAppointments.length === 0 ? (
              <p className="text-muted-foreground">No upcoming appointments</p>
            ) : (
              <div className="space-y-3">
                {upcomingAppointments.map((appt) => (
                  <div
                    key={appt.id}
                    className="p-4 bg-surface rounded-lg border border-border"
                    data-testid={`appointment-${appt.id}`}
                  >
                    <p className="font-medium">
                      {new Date(appt.start_time).toLocaleDateString()} at{' '}
                      {new Date(appt.start_time).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                    {appt.notes && <p className="text-sm text-muted-foreground mt-1">{appt.notes}</p>}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Pending Assessments - Span 4 cols */}
          <Card className="md:col-span-4 p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="pending-assessments-card">
            <div className="flex items-center gap-3 mb-4">
              <ClipboardCheck className="text-secondary" size={24} />
              <h3 className="text-xl font-serif text-primary">Assessments</h3>
            </div>
            {pendingAssessments.length === 0 ? (
              <p className="text-sm text-muted-foreground">No pending assessments</p>
            ) : (
              <div className="space-y-2">
                {pendingAssessments.map((assess) => (
                  <div key={assess.id} className="p-3 bg-surface rounded-lg">
                    <p className="font-medium text-sm">{assess.assessment_type}</p>
                    <Button
                      onClick={() => handleCompleteAssessment(assess)}
                      size="sm"
                      className="mt-2 w-full"
                      data-testid={`complete-assessment-${assess.id}`}
                    >
                      Complete
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Homework - Span 6 cols */}
          <Card className="md:col-span-6 p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="homework-card">
            <div className="flex items-center gap-3 mb-4">
              <BookCheck className="text-info" size={24} />
              <h3 className="text-2xl font-serif text-primary">Homework</h3>
            </div>
            {pendingHomework.length === 0 ? (
              <p className="text-muted-foreground">No pending homework</p>
            ) : (
              <div className="space-y-3">
                {pendingHomework.map((hw) => (
                  <div key={hw.id} className="p-4 bg-surface rounded-lg border border-border">
                    <h4 className="font-medium">{hw.title}</h4>
                    <p className="text-sm text-muted-foreground mt-1">{hw.description}</p>
                    {hw.due_date && (
                      <p className="text-xs text-warning mt-2">
                        Due: {new Date(hw.due_date).toLocaleDateString()}
                      </p>
                    )}
                    <Button
                      onClick={() => handleCompleteHomework(hw.id)}
                      size="sm"
                      className="mt-3"
                      data-testid={`complete-homework-${hw.id}`}
                    >
                      Mark Complete
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Messages - Span 6 cols */}
          <Card className="md:col-span-6 p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl shadow-lg" data-testid="messages-card">
            <div className="flex items-center gap-3 mb-4">
              <MessageSquare className="text-success" size={24} />
              <h3 className="text-2xl font-serif text-primary">Messages</h3>
            </div>
            <p className="text-muted-foreground mb-4">Secure messaging with your therapist</p>
            <Button className="w-full" data-testid="view-messages-button">
              View Messages
            </Button>
          </Card>
        </div>

        {/* Disclaimer */}
        <div className="mt-12 p-6 bg-info/10 border border-info/20 rounded-xl">
          <p className="text-sm text-info">
            <strong>Clinical Support Only:</strong> This platform provides tools to support your therapy journey.
            All clinical decisions and treatment plans are made by your licensed therapist.
          </p>
        </div>
      </main>
    </div>
  );
};

export default ClientDashboard;
