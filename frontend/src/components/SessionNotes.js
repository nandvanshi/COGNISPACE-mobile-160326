import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Plus, FileText } from 'lucide-react';

const SessionNotes = () => {
  const [notes, setNotes] = useState([]);
  const [clients, setClients] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);
  const [newNote, setNewNote] = useState({
    client_id: '',
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
      const [notesRes, clientsRes] = await Promise.all([
        axios.get(`${API}/session-notes`),
        axios.get(`${API}/clients`),
      ]);
      setNotes(notesRes.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      setClients(clientsRes.data);
    } catch (error) {
      toast.error('Failed to load session notes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNote = async (e) => {
    e.preventDefault();

    if (!newNote.client_id) {
      toast.error('Please select a client');
      return;
    }

    try {
      await axios.post(`${API}/session-notes`, newNote);
      toast.success('Session note created');
      setShowDialog(false);
      setNewNote({
        client_id: '',
        template_type: 'SOAP',
        subjective: '',
        objective: '',
        assessment: '',
        plan: '',
        data: '',
      });
      fetchData();
    } catch (error) {
      toast.error('Failed to create session note');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading session notes...</div>;
  }

  return (
    <div data-testid="session-notes">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Session Notes</h2>
          <p className="text-muted-foreground">Document client sessions with SOAP or DAP templates</p>
        </div>
        <Button
          onClick={() => setShowDialog(true)}
          className="bg-primary hover:bg-primary-700 rounded-full"
          data-testid="create-note-button"
        >
          <Plus size={20} className="mr-2" />
          New Note
        </Button>
      </div>

      {/* Notes List */}
      <div className="space-y-4">
        {notes.map((note) => (
          <Card
            key={note.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setSelectedNote(note)}
            data-testid={`note-${note.id}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-medium text-lg text-foreground">{note.client_name}</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(note.created_at).toLocaleDateString()} at{' '}
                  {new Date(note.created_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
              <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                {note.template_type}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              {note.template_type === 'SOAP' && note.subjective && (
                <p className="line-clamp-2"><strong>S:</strong> {note.subjective}</p>
              )}
              {note.template_type === 'DAP' && note.data && (
                <p className="line-clamp-2"><strong>D:</strong> {note.data}</p>
              )}
            </div>
          </Card>
        ))}

        {notes.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No session notes yet</p>
          </div>
        )}
      </div>

      {/* Create Note Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="note-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">New Session Note</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateNote} className="space-y-4">
            <div>
              <Label htmlFor="note-client">Client</Label>
              <select
                id="note-client"
                data-testid="note-client-select"
                value={newNote.client_id}
                onChange={(e) => setNewNote({ ...newNote, client_id: e.target.value })}
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
              <Label htmlFor="template-type">Template</Label>
              <select
                id="template-type"
                data-testid="template-type-select"
                value={newNote.template_type}
                onChange={(e) => setNewNote({ ...newNote, template_type: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="SOAP">SOAP</option>
                <option value="DAP">DAP</option>
              </select>
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
                    placeholder="Client's reported symptoms, concerns, and experiences..."
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
                    placeholder="Observable behaviors, mental status, appearance..."
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
                    placeholder="Clinical impressions, progress, interpretations..."
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
                    placeholder="Treatment plan, interventions, homework, next steps..."
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
                    rows={3}
                    placeholder="Observations and information gathered..."
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
                    placeholder="Clinical impressions and interpretations..."
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
                    placeholder="Treatment plan and next steps..."
                    className="mt-1"
                  />
                </div>
              </>
            )}

            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="save-note-button">
                Save Note
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                data-testid="cancel-note-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Note Dialog */}
      {selectedNote && (
        <Dialog open={!!selectedNote} onOpenChange={() => setSelectedNote(null)}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="view-note-dialog">
            <DialogHeader>
              <DialogTitle className="text-2xl font-serif text-primary">
                Session Note - {selectedNote.client_name}
              </DialogTitle>
              <p className="text-sm text-muted-foreground">
                {new Date(selectedNote.created_at).toLocaleDateString()} • {selectedNote.template_type}
              </p>
            </DialogHeader>
            <div className="space-y-4">
              {selectedNote.template_type === 'SOAP' ? (
                <>
                  {selectedNote.subjective && (
                    <div>
                      <h4 className="font-medium text-primary mb-2">Subjective</h4>
                      <p className="text-sm text-foreground">{selectedNote.subjective}</p>
                    </div>
                  )}
                  {selectedNote.objective && (
                    <div>
                      <h4 className="font-medium text-primary mb-2">Objective</h4>
                      <p className="text-sm text-foreground">{selectedNote.objective}</p>
                    </div>
                  )}
                  {selectedNote.assessment && (
                    <div>
                      <h4 className="font-medium text-primary mb-2">Assessment</h4>
                      <p className="text-sm text-foreground">{selectedNote.assessment}</p>
                    </div>
                  )}
                  {selectedNote.plan && (
                    <div>
                      <h4 className="font-medium text-primary mb-2">Plan</h4>
                      <p className="text-sm text-foreground">{selectedNote.plan}</p>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {selectedNote.data && (
                    <div>
                      <h4 className="font-medium text-primary mb-2">Data</h4>
                      <p className="text-sm text-foreground">{selectedNote.data}</p>
                    </div>
                  )}
                  {selectedNote.assessment && (
                    <div>
                      <h4 className="font-medium text-primary mb-2">Assessment</h4>
                      <p className="text-sm text-foreground">{selectedNote.assessment}</p>
                    </div>
                  )}
                  {selectedNote.plan && (
                    <div>
                      <h4 className="font-medium text-primary mb-2">Plan</h4>
                      <p className="text-sm text-foreground">{selectedNote.plan}</p>
                    </div>
                  )}
                </>
              )}
            </div>
            <Button onClick={() => setSelectedNote(null)} className="w-full" data-testid="close-note-button">
              Close
            </Button>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default SessionNotes;
