import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { Plus, FileText, Edit, Trash2, Calendar, Clock, Link, User } from 'lucide-react';

const SessionNotes = ({ isReadOnly = false }) => {
  const [notes, setNotes] = useState([]);
  const [clients, setClients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);
  const [filterClient, setFilterClient] = useState('all');
  const [newNote, setNewNote] = useState({
    client_id: '',
    appointment_id: '',
    template_type: 'SOAP',
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
    data: '',
  });
  const [editNote, setEditNote] = useState({
    template_type: 'SOAP',
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
    data: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [notesRes, clientsRes, apptsRes] = await Promise.all([
        axios.get(`${API}/session-notes`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/appointments`),
      ]);
      setNotes(notesRes.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      setClients(clientsRes.data);
      // Only show completed appointments for linking
      setAppointments(apptsRes.data.filter(a => a.status === 'completed' || a.status === 'scheduled'));
    } catch (error) {
      toast.error('Failed to load session notes');
    } finally {
      setLoading(false);
    }
  };

  const getClientAppointments = (clientId) => {
    if (!clientId) return [];
    return appointments.filter(a => a.client_id === clientId);
  };

  const handleCreateNote = async (e) => {
    e.preventDefault();

    if (!newNote.client_id) {
      toast.error('Please select a client');
      return;
    }

    // Validate that at least one field has content
    const hasContent = newNote.template_type === 'SOAP'
      ? (newNote.subjective || newNote.objective || newNote.assessment || newNote.plan)
      : (newNote.data || newNote.assessment || newNote.plan);
    
    if (!hasContent) {
      toast.error('Please fill in at least one field');
      return;
    }

    try {
      await axios.post(`${API}/session-notes`, {
        client_id: newNote.client_id,
        appointment_id: newNote.appointment_id || null,
        template_type: newNote.template_type,
        subjective: newNote.subjective,
        objective: newNote.objective,
        assessment: newNote.assessment,
        plan: newNote.plan,
        data: newNote.data,
      });
      toast.success('Session note created');
      setShowCreateDialog(false);
      resetNewNote();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create session note');
    }
  };

  const handleEditNote = async (e) => {
    e.preventDefault();

    if (!selectedNote) return;

    try {
      await axios.put(`${API}/session-notes/${selectedNote.id}`, {
        template_type: editNote.template_type,
        subjective: editNote.subjective,
        objective: editNote.objective,
        assessment: editNote.assessment,
        plan: editNote.plan,
        data: editNote.data,
      });
      toast.success('Session note updated');
      setShowEditDialog(false);
      setSelectedNote(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update session note');
    }
  };

  const handleDeleteNote = async (noteId) => {
    if (!window.confirm('Are you sure you want to delete this session note? This action cannot be undone.')) return;

    try {
      await axios.delete(`${API}/session-notes/${noteId}`);
      toast.success('Session note deleted');
      setShowViewDialog(false);
      setSelectedNote(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete session note');
    }
  };

  const openEditDialog = (note) => {
    setSelectedNote(note);
    setEditNote({
      template_type: note.template_type,
      subjective: note.subjective || '',
      objective: note.objective || '',
      assessment: note.assessment || '',
      plan: note.plan || '',
      data: note.data || '',
    });
    setShowViewDialog(false);
    setShowEditDialog(true);
  };

  const openViewDialog = (note) => {
    setSelectedNote(note);
    setShowViewDialog(true);
  };

  const resetNewNote = () => {
    setNewNote({
      client_id: '',
      appointment_id: '',
      template_type: 'SOAP',
      subjective: '',
      objective: '',
      assessment: '',
      plan: '',
      data: '',
    });
  };

  const filteredNotes = filterClient === 'all' 
    ? notes 
    : notes.filter(n => n.client_id === filterClient);

  const formatAppointmentDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return <div className="text-center py-12">Loading session notes...</div>;
  }

  return (
    <div data-testid="session-notes">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Session Notes</h2>
          <p className="text-muted-foreground">Document client sessions with SOAP or DAP templates</p>
        </div>
        {!isReadOnly && (
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="create-note-button"
          >
            <Plus size={20} className="mr-2" />
            New Note
          </Button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <FileText size={20} className="text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{notes.length}</p>
              <p className="text-sm text-muted-foreground">Total Notes</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-info/10 flex items-center justify-center">
              <span className="text-info font-bold text-sm">S</span>
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {notes.filter(n => n.template_type === 'SOAP').length}
              </p>
              <p className="text-sm text-muted-foreground">SOAP Notes</p>
            </div>
          </div>
        </Card>
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-success/10 flex items-center justify-center">
              <span className="text-success font-bold text-sm">D</span>
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {notes.filter(n => n.template_type === 'DAP').length}
              </p>
              <p className="text-sm text-muted-foreground">DAP Notes</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filter */}
      <div className="mb-6 flex items-center gap-4">
        <Label className="text-sm font-medium">Filter by client:</Label>
        <Select value={filterClient} onValueChange={setFilterClient}>
          <SelectTrigger className="w-56" data-testid="filter-client-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Clients</SelectItem>
            {clients.map((client) => (
              <SelectItem key={client.id} value={client.id}>
                {client.full_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Notes List */}
      <div className="space-y-4">
        {filteredNotes.map((note) => (
          <Card
            key={note.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl cursor-pointer hover:shadow-lg transition-all"
            onClick={() => openViewDialog(note)}
            data-testid={`note-${note.id}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <User size={18} className="text-primary" />
                </div>
                <div>
                  <p className="font-medium text-lg text-foreground">{note.client_name}</p>
                  <p className="text-sm text-muted-foreground flex items-center gap-2">
                    <Calendar size={14} />
                    {new Date(note.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                    <Clock size={14} className="ml-2" />
                    {new Date(note.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {note.appointment_id && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-success/10 text-success border border-success/20">
                    <Link size={12} />
                    Linked
                  </span>
                )}
                <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                  {note.template_type}
                </span>
              </div>
            </div>
            <div className="text-sm text-muted-foreground line-clamp-2">
              {note.template_type === 'SOAP' && note.subjective && (
                <p><strong>S:</strong> {note.subjective}</p>
              )}
              {note.template_type === 'DAP' && note.data && (
                <p><strong>D:</strong> {note.data}</p>
              )}
              {!note.subjective && !note.data && note.assessment && (
                <p><strong>A:</strong> {note.assessment}</p>
              )}
            </div>
          </Card>
        ))}

        {filteredNotes.length === 0 && (
          <div className="text-center py-12">
            <FileText size={48} className="mx-auto text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground">
              {filterClient === 'all' ? 'No session notes yet' : 'No notes for this client'}
            </p>
            {!isReadOnly && filterClient === 'all' && (
              <Button
                onClick={() => setShowCreateDialog(true)}
                variant="outline"
                className="mt-4"
              >
                Create your first note
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Create Note Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="create-note-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">New Session Note</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateNote} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Client *</Label>
                <Select
                  value={newNote.client_id}
                  onValueChange={(value) => setNewNote({ ...newNote, client_id: value, appointment_id: '' })}
                >
                  <SelectTrigger className="mt-1" data-testid="note-client-select">
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
                <Label>Link to Appointment (optional)</Label>
                <Select
                  value={newNote.appointment_id}
                  onValueChange={(value) => setNewNote({ ...newNote, appointment_id: value })}
                  disabled={!newNote.client_id}
                >
                  <SelectTrigger className="mt-1" data-testid="note-appointment-select">
                    <SelectValue placeholder={newNote.client_id ? "Select appointment" : "Select client first"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">No appointment link</SelectItem>
                    {getClientAppointments(newNote.client_id).map((appt) => (
                      <SelectItem key={appt.id} value={appt.id}>
                        {formatAppointmentDate(appt.start_time)} - {appt.status}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label>Template</Label>
              <Select
                value={newNote.template_type}
                onValueChange={(value) => setNewNote({ ...newNote, template_type: value })}
              >
                <SelectTrigger className="mt-1" data-testid="template-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SOAP">SOAP (Subjective, Objective, Assessment, Plan)</SelectItem>
                  <SelectItem value="DAP">DAP (Data, Assessment, Plan)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {newNote.template_type === 'SOAP' ? (
              <>
                <div>
                  <Label htmlFor="subjective">Subjective</Label>
                  <Textarea
                    id="subjective"
                    data-testid="subjective-input"
                    value={newNote.subjective}
                    onChange={(e) => setNewNote({ ...newNote, subjective: e.target.value })}
                    rows={3}
                    placeholder="Client's reported symptoms, concerns, feelings, and experiences in their own words..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="objective">Objective</Label>
                  <Textarea
                    id="objective"
                    data-testid="objective-input"
                    value={newNote.objective}
                    onChange={(e) => setNewNote({ ...newNote, objective: e.target.value })}
                    rows={3}
                    placeholder="Observable behaviors, mental status, appearance, affect, speech patterns..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="assessment">Assessment</Label>
                  <Textarea
                    id="assessment"
                    data-testid="assessment-input"
                    value={newNote.assessment}
                    onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })}
                    rows={3}
                    placeholder="Clinical impressions, progress toward goals, diagnosis considerations..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="plan">Plan</Label>
                  <Textarea
                    id="plan"
                    data-testid="plan-input"
                    value={newNote.plan}
                    onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })}
                    rows={3}
                    placeholder="Treatment plan, interventions, homework assignments, next session focus..."
                    className="mt-1"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <Label htmlFor="data">Data</Label>
                  <Textarea
                    id="data"
                    data-testid="data-input"
                    value={newNote.data}
                    onChange={(e) => setNewNote({ ...newNote, data: e.target.value })}
                    rows={4}
                    placeholder="Observations, information gathered, what happened during the session..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="assessment-dap">Assessment</Label>
                  <Textarea
                    id="assessment-dap"
                    data-testid="assessment-dap-input"
                    value={newNote.assessment}
                    onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })}
                    rows={3}
                    placeholder="Clinical impressions, interpretations, progress evaluation..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="plan-dap">Plan</Label>
                  <Textarea
                    id="plan-dap"
                    data-testid="plan-dap-input"
                    value={newNote.plan}
                    onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })}
                    rows={3}
                    placeholder="Treatment plan, next steps, homework..."
                    className="mt-1"
                  />
                </div>
              </>
            )}

            <div className="flex gap-3 pt-2">
              <Button type="submit" className="flex-1" data-testid="save-note-button">
                Save Note
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowCreateDialog(false);
                  resetNewNote();
                }}
                data-testid="cancel-note-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Note Dialog */}
      <Dialog open={showViewDialog} onOpenChange={setShowViewDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="view-note-dialog">
          {selectedNote && (
            <>
              <DialogHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <DialogTitle className="text-2xl font-serif text-primary">
                      Session Note - {selectedNote.client_name}
                    </DialogTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {new Date(selectedNote.created_at).toLocaleDateString('en-US', {
                        weekday: 'long',
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                      {' • '}
                      {selectedNote.template_type}
                    </p>
                    {selectedNote.appointment_date && (
                      <p className="text-sm text-success mt-1 flex items-center gap-1">
                        <Link size={14} />
                        Linked to appointment: {formatAppointmentDate(selectedNote.appointment_date)}
                      </p>
                    )}
                    {selectedNote.updated_at !== selectedNote.created_at && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Last updated: {new Date(selectedNote.updated_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                    {selectedNote.template_type}
                  </span>
                </div>
              </DialogHeader>

              <div className="space-y-4 mt-4">
                {selectedNote.template_type === 'SOAP' ? (
                  <>
                    {selectedNote.subjective && (
                      <div className="p-4 bg-surface rounded-lg">
                        <h4 className="font-medium text-primary mb-2 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm">S</span>
                          Subjective
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{selectedNote.subjective}</p>
                      </div>
                    )}
                    {selectedNote.objective && (
                      <div className="p-4 bg-surface rounded-lg">
                        <h4 className="font-medium text-primary mb-2 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm">O</span>
                          Objective
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{selectedNote.objective}</p>
                      </div>
                    )}
                    {selectedNote.assessment && (
                      <div className="p-4 bg-surface rounded-lg">
                        <h4 className="font-medium text-primary mb-2 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm">A</span>
                          Assessment
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{selectedNote.assessment}</p>
                      </div>
                    )}
                    {selectedNote.plan && (
                      <div className="p-4 bg-surface rounded-lg">
                        <h4 className="font-medium text-primary mb-2 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm">P</span>
                          Plan
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{selectedNote.plan}</p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    {selectedNote.data && (
                      <div className="p-4 bg-surface rounded-lg">
                        <h4 className="font-medium text-primary mb-2 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm">D</span>
                          Data
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{selectedNote.data}</p>
                      </div>
                    )}
                    {selectedNote.assessment && (
                      <div className="p-4 bg-surface rounded-lg">
                        <h4 className="font-medium text-primary mb-2 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm">A</span>
                          Assessment
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{selectedNote.assessment}</p>
                      </div>
                    )}
                    {selectedNote.plan && (
                      <div className="p-4 bg-surface rounded-lg">
                        <h4 className="font-medium text-primary mb-2 flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-sm">P</span>
                          Plan
                        </h4>
                        <p className="text-sm text-foreground whitespace-pre-wrap">{selectedNote.plan}</p>
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                {!isReadOnly && (
                  <>
                    <Button
                      onClick={() => openEditDialog(selectedNote)}
                      variant="outline"
                      className="flex-1"
                      data-testid="edit-note-button"
                    >
                      <Edit size={16} className="mr-2" />
                      Edit
                    </Button>
                    <Button
                      onClick={() => handleDeleteNote(selectedNote.id)}
                      variant="outline"
                      className="text-error hover:text-error hover:bg-error/10"
                      data-testid="delete-note-button"
                    >
                      <Trash2 size={16} />
                    </Button>
                  </>
                )}
                <Button
                  onClick={() => {
                    setShowViewDialog(false);
                    setSelectedNote(null);
                  }}
                  className={isReadOnly ? 'w-full' : ''}
                  data-testid="close-note-button"
                >
                  Close
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Note Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="edit-note-dialog">
          {selectedNote && (
            <>
              <DialogHeader>
                <DialogTitle className="text-2xl font-serif text-primary">
                  Edit Session Note - {selectedNote.client_name}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleEditNote} className="space-y-4">
                <div>
                  <Label>Template</Label>
                  <Select
                    value={editNote.template_type}
                    onValueChange={(value) => setEditNote({ ...editNote, template_type: value })}
                  >
                    <SelectTrigger className="mt-1" data-testid="edit-template-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="SOAP">SOAP</SelectItem>
                      <SelectItem value="DAP">DAP</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {editNote.template_type === 'SOAP' ? (
                  <>
                    <div>
                      <Label htmlFor="edit-subjective">Subjective</Label>
                      <Textarea
                        id="edit-subjective"
                        data-testid="edit-subjective-input"
                        value={editNote.subjective}
                        onChange={(e) => setEditNote({ ...editNote, subjective: e.target.value })}
                        rows={3}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-objective">Objective</Label>
                      <Textarea
                        id="edit-objective"
                        data-testid="edit-objective-input"
                        value={editNote.objective}
                        onChange={(e) => setEditNote({ ...editNote, objective: e.target.value })}
                        rows={3}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-assessment">Assessment</Label>
                      <Textarea
                        id="edit-assessment"
                        data-testid="edit-assessment-input"
                        value={editNote.assessment}
                        onChange={(e) => setEditNote({ ...editNote, assessment: e.target.value })}
                        rows={3}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-plan">Plan</Label>
                      <Textarea
                        id="edit-plan"
                        data-testid="edit-plan-input"
                        value={editNote.plan}
                        onChange={(e) => setEditNote({ ...editNote, plan: e.target.value })}
                        rows={3}
                        className="mt-1"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <Label htmlFor="edit-data">Data</Label>
                      <Textarea
                        id="edit-data"
                        data-testid="edit-data-input"
                        value={editNote.data}
                        onChange={(e) => setEditNote({ ...editNote, data: e.target.value })}
                        rows={4}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-assessment-dap">Assessment</Label>
                      <Textarea
                        id="edit-assessment-dap"
                        data-testid="edit-assessment-dap-input"
                        value={editNote.assessment}
                        onChange={(e) => setEditNote({ ...editNote, assessment: e.target.value })}
                        rows={3}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-plan-dap">Plan</Label>
                      <Textarea
                        id="edit-plan-dap"
                        data-testid="edit-plan-dap-input"
                        value={editNote.plan}
                        onChange={(e) => setEditNote({ ...editNote, plan: e.target.value })}
                        rows={3}
                        className="mt-1"
                      />
                    </div>
                  </>
                )}

                <div className="flex gap-3 pt-2">
                  <Button type="submit" className="flex-1" data-testid="update-note-button">
                    Update Note
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowEditDialog(false);
                      setSelectedNote(null);
                    }}
                    data-testid="cancel-edit-button"
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SessionNotes;
