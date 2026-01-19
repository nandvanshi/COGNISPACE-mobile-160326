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
import { Plus, FileText, Edit, Trash2, Calendar, Clock, Link, User, Zap, BookmarkPlus, Settings, AlertTriangle, ClipboardList } from 'lucide-react';
import { formatDate, formatTime, formatDateLong } from '../utils/formatUtils';
import CaseHistoryWizard from './CaseHistoryWizard';

const TEMPLATE_CATEGORIES = [
  { value: 'subjective', label: 'Subjective (S)', color: 'bg-blue-100 text-blue-700' },
  { value: 'objective', label: 'Objective (O)', color: 'bg-green-100 text-green-700' },
  { value: 'assessment', label: 'Assessment (A)', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'plan', label: 'Plan (P)', color: 'bg-purple-100 text-purple-700' },
  { value: 'data', label: 'Data (D)', color: 'bg-teal-100 text-teal-700' },
  { value: 'general', label: 'General', color: 'bg-gray-100 text-gray-700' },
];

const SessionNotes = ({ isReadOnly = false }) => {
  const [notes, setNotes] = useState([]);
  const [clients, setClients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [showManageTemplatesDialog, setShowManageTemplatesDialog] = useState(false);
  const [showCaseHistoryDialog, setShowCaseHistoryDialog] = useState(false);
  const [selectedClientForCaseHistory, setSelectedClientForCaseHistory] = useState(null);
  const [caseHistoryStatus, setCaseHistoryStatus] = useState({});  // {clientId: {exists, is_complete}}
  const [selectedNote, setSelectedNote] = useState(null);
  const [filterClient, setFilterClient] = useState('all');
  const [activeField, setActiveField] = useState(null);
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
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    category: 'general',
    content: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [notesRes, clientsRes, apptsRes, templatesRes] = await Promise.all([
        axios.get(`${API}/session-notes`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/appointments`),
        axios.get(`${API}/note-templates`).catch(() => ({ data: [] })),
      ]);
      setNotes(notesRes.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      setClients(clientsRes.data);
      setAppointments(apptsRes.data.filter(a => a.status === 'completed' || a.status === 'scheduled'));
      setTemplates(templatesRes.data);
      
      // Check case history status for all clients
      const statusPromises = clientsRes.data.map(async (client) => {
        try {
          const res = await axios.get(`${API}/case-history/check/${client.id}`);
          return { clientId: client.id, ...res.data };
        } catch {
          return { clientId: client.id, exists: false, is_complete: false };
        }
      });
      const statuses = await Promise.all(statusPromises);
      const statusMap = {};
      statuses.forEach(s => { statusMap[s.clientId] = s; });
      setCaseHistoryStatus(statusMap);
    } catch (error) {
      toast.error('Failed to load session notes');
    } finally {
      setLoading(false);
    }
  };

  const checkCaseHistory = async (clientId) => {
    try {
      const res = await axios.get(`${API}/case-history/check/${clientId}`);
      setCaseHistoryStatus(prev => ({ ...prev, [clientId]: res.data }));
      return res.data;
    } catch {
      return { exists: false, is_complete: false };
    }
  };

  const handleOpenCreateDialog = async () => {
    setShowCreateDialog(true);
  };

  const handleClientSelect = async (clientId) => {
    setNewNote(prev => ({ ...prev, client_id: clientId, appointment_id: '' }));
    
    // Check case history status for this client
    if (clientId) {
      await checkCaseHistory(clientId);
    }
  };

  const openCaseHistory = (client) => {
    setSelectedClientForCaseHistory(client);
    setShowCaseHistoryDialog(true);
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

    // Check case history is complete before allowing note creation
    const status = caseHistoryStatus[newNote.client_id];
    if (!status?.is_complete) {
      const client = clients.find(c => c.id === newNote.client_id);
      toast.error('Case history must be completed before creating session notes');
      openCaseHistory(client);
      return;
    }

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
    if (!window.confirm('Are you sure you want to delete this session note?')) return;

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

  const handleCreateTemplate = async (e) => {
    e.preventDefault();

    if (!newTemplate.name || !newTemplate.content) {
      toast.error('Please fill in name and content');
      return;
    }

    try {
      await axios.post(`${API}/note-templates`, newTemplate);
      toast.success('Template created');
      setNewTemplate({ name: '', category: 'general', content: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create template');
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Delete this template?')) return;

    try {
      await axios.delete(`${API}/note-templates/${templateId}`);
      toast.success('Template deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const insertTemplate = async (template, targetField, isEditing = false) => {
    // Record usage
    try {
      await axios.post(`${API}/note-templates/${template.id}/use`);
    } catch (e) {
      // Ignore usage tracking errors
    }

    if (isEditing) {
      setEditNote(prev => ({
        ...prev,
        [targetField]: prev[targetField] ? `${prev[targetField]}\n${template.content}` : template.content
      }));
    } else {
      setNewNote(prev => ({
        ...prev,
        [targetField]: prev[targetField] ? `${prev[targetField]}\n${template.content}` : template.content
      }));
    }
    setShowTemplateDialog(false);
    toast.success('Template inserted');
  };

  const openTemplateSelector = (field) => {
    setActiveField(field);
    setShowTemplateDialog(true);
  };

  const getTemplatesForField = (field) => {
    const categoryMap = {
      subjective: 'subjective',
      objective: 'objective',
      assessment: 'assessment',
      plan: 'plan',
      data: 'data',
    };
    const category = categoryMap[field];
    return templates.filter(t => t.category === category || t.category === 'general');
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
    return `${formatDate(dateStr)} ${formatTime(dateStr)}`;
  };

  const getCategoryBadge = (category) => {
    const cat = TEMPLATE_CATEGORIES.find(c => c.value === category);
    return cat ? cat.color : 'bg-gray-100 text-gray-700';
  };

  // Render template insert button for a field
  const renderTemplateButton = (field, isEditing = false) => {
    const fieldTemplates = getTemplatesForField(field);
    if (fieldTemplates.length === 0) return null;
    
    return (
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => openTemplateSelector(field)}
        className="h-6 px-2 text-xs text-muted-foreground hover:text-primary"
        data-testid={`template-btn-${field}`}
      >
        <Zap size={12} className="mr-1" />
        Quick Insert ({fieldTemplates.length})
      </Button>
    );
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
        <div className="flex gap-2">
          {!isReadOnly && (
            <>
              <Button
                variant="outline"
                onClick={() => setShowManageTemplatesDialog(true)}
                data-testid="manage-templates-button"
              >
                <Settings size={16} className="mr-2" />
                Templates ({templates.length})
              </Button>
              <Button
                onClick={() => setShowCreateDialog(true)}
                className="bg-primary hover:bg-primary-700 rounded-full"
                data-testid="create-note-button"
              >
                <Plus size={20} className="mr-2" />
                New Note
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
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
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-warning/10 flex items-center justify-center">
              <Zap size={20} className="text-warning" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{templates.length}</p>
              <p className="text-sm text-muted-foreground">Quick Templates</p>
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
                    {formatDate(note.created_at)}
                    <Clock size={14} className="ml-2" />
                    {formatTime(note.created_at)}
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
                  value={newNote.appointment_id || "none"}
                  onValueChange={(value) => setNewNote({ ...newNote, appointment_id: value === "none" ? "" : value })}
                  disabled={!newNote.client_id}
                >
                  <SelectTrigger className="mt-1" data-testid="note-appointment-select">
                    <SelectValue placeholder={newNote.client_id ? "Select appointment" : "Select client first"} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No appointment link</SelectItem>
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
                  <div className="flex items-center justify-between">
                    <Label htmlFor="subjective">Subjective</Label>
                    {renderTemplateButton('subjective')}
                  </div>
                  <Textarea
                    id="subjective"
                    data-testid="subjective-input"
                    value={newNote.subjective}
                    onChange={(e) => setNewNote({ ...newNote, subjective: e.target.value })}
                    rows={3}
                    placeholder="Client's reported symptoms, concerns, feelings, and experiences..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="objective">Objective</Label>
                    {renderTemplateButton('objective')}
                  </div>
                  <Textarea
                    id="objective"
                    data-testid="objective-input"
                    value={newNote.objective}
                    onChange={(e) => setNewNote({ ...newNote, objective: e.target.value })}
                    rows={3}
                    placeholder="Observable behaviors, mental status, appearance, affect..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="assessment">Assessment</Label>
                    {renderTemplateButton('assessment')}
                  </div>
                  <Textarea
                    id="assessment"
                    data-testid="assessment-input"
                    value={newNote.assessment}
                    onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })}
                    rows={3}
                    placeholder="Clinical impressions, progress toward goals..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="plan">Plan</Label>
                    {renderTemplateButton('plan')}
                  </div>
                  <Textarea
                    id="plan"
                    data-testid="plan-input"
                    value={newNote.plan}
                    onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })}
                    rows={3}
                    placeholder="Treatment plan, interventions, homework..."
                    className="mt-1"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="data">Data</Label>
                    {renderTemplateButton('data')}
                  </div>
                  <Textarea
                    id="data"
                    data-testid="data-input"
                    value={newNote.data}
                    onChange={(e) => setNewNote({ ...newNote, data: e.target.value })}
                    rows={4}
                    placeholder="Observations, information gathered..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="assessment-dap">Assessment</Label>
                    {renderTemplateButton('assessment')}
                  </div>
                  <Textarea
                    id="assessment-dap"
                    data-testid="assessment-dap-input"
                    value={newNote.assessment}
                    onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })}
                    rows={3}
                    placeholder="Clinical impressions, interpretations..."
                    className="mt-1"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="plan-dap">Plan</Label>
                    {renderTemplateButton('plan')}
                  </div>
                  <Textarea
                    id="plan-dap"
                    data-testid="plan-dap-input"
                    value={newNote.plan}
                    onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })}
                    rows={3}
                    placeholder="Treatment plan, next steps..."
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
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Template Selector Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="max-w-md" data-testid="template-selector-dialog">
          <DialogHeader>
            <DialogTitle className="text-xl font-serif text-primary">
              Quick Insert - {activeField?.charAt(0).toUpperCase() + activeField?.slice(1)}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {activeField && getTemplatesForField(activeField).map((template) => (
              <button
                key={template.id}
                onClick={() => insertTemplate(template, activeField, showEditDialog)}
                className="w-full p-3 text-left rounded-lg border border-border hover:border-primary hover:bg-primary/5 transition-all"
                data-testid={`template-option-${template.id}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{template.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${getCategoryBadge(template.category)}`}>
                    {template.category}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">{template.content}</p>
              </button>
            ))}
            {activeField && getTemplatesForField(activeField).length === 0 && (
              <p className="text-center text-muted-foreground py-4">
                No templates for this field. Create one in Template Manager.
              </p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Manage Templates Dialog */}
      <Dialog open={showManageTemplatesDialog} onOpenChange={setShowManageTemplatesDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="manage-templates-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Manage Quick Templates</DialogTitle>
          </DialogHeader>
          
          {/* Create new template */}
          <form onSubmit={handleCreateTemplate} className="space-y-3 p-4 bg-surface rounded-lg">
            <h4 className="font-medium flex items-center gap-2">
              <BookmarkPlus size={16} />
              Create New Template
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Name</Label>
                <Input
                  value={newTemplate.name}
                  onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                  placeholder="e.g., Anxious presentation"
                  className="mt-1"
                  data-testid="new-template-name"
                />
              </div>
              <div>
                <Label>Category</Label>
                <Select
                  value={newTemplate.category}
                  onValueChange={(value) => setNewTemplate({ ...newTemplate, category: value })}
                >
                  <SelectTrigger className="mt-1" data-testid="new-template-category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TEMPLATE_CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>Content</Label>
              <Textarea
                value={newTemplate.content}
                onChange={(e) => setNewTemplate({ ...newTemplate, content: e.target.value })}
                placeholder="Template text to insert..."
                rows={2}
                className="mt-1"
                data-testid="new-template-content"
              />
            </div>
            <Button type="submit" size="sm" data-testid="save-new-template">
              <Plus size={14} className="mr-1" />
              Add Template
            </Button>
          </form>

          {/* Existing templates */}
          <div className="space-y-2 mt-4">
            <h4 className="font-medium">Your Templates ({templates.length})</h4>
            {templates.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No templates yet. Create one above to speed up note-taking.
              </p>
            ) : (
              templates.map((template) => (
                <div
                  key={template.id}
                  className="p-3 border border-border rounded-lg flex items-start justify-between gap-3"
                  data-testid={`template-item-${template.id}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{template.name}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${getCategoryBadge(template.category)}`}>
                        {template.category}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Used {template.usage_count}x
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">{template.content}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteTemplate(template.id)}
                    className="text-error hover:text-error hover:bg-error/10 shrink-0"
                    data-testid={`delete-template-${template.id}`}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              ))
            )}
          </div>
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
                      {formatDateLong(selectedNote.created_at)}
                      {' • '}
                      {selectedNote.template_type}
                    </p>
                    {selectedNote.appointment_date && (
                      <p className="text-sm text-success mt-1 flex items-center gap-1">
                        <Link size={14} />
                        Linked to appointment: {formatAppointmentDate(selectedNote.appointment_date)}
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
                    <SelectTrigger className="mt-1">
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
                      <div className="flex items-center justify-between">
                        <Label>Subjective</Label>
                        {renderTemplateButton('subjective', true)}
                      </div>
                      <Textarea
                        value={editNote.subjective}
                        onChange={(e) => setEditNote({ ...editNote, subjective: e.target.value })}
                        rows={3}
                        className="mt-1"
                        data-testid="edit-subjective-input"
                      />
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <Label>Objective</Label>
                        {renderTemplateButton('objective', true)}
                      </div>
                      <Textarea
                        value={editNote.objective}
                        onChange={(e) => setEditNote({ ...editNote, objective: e.target.value })}
                        rows={3}
                        className="mt-1"
                        data-testid="edit-objective-input"
                      />
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <Label>Assessment</Label>
                        {renderTemplateButton('assessment', true)}
                      </div>
                      <Textarea
                        value={editNote.assessment}
                        onChange={(e) => setEditNote({ ...editNote, assessment: e.target.value })}
                        rows={3}
                        className="mt-1"
                        data-testid="edit-assessment-input"
                      />
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <Label>Plan</Label>
                        {renderTemplateButton('plan', true)}
                      </div>
                      <Textarea
                        value={editNote.plan}
                        onChange={(e) => setEditNote({ ...editNote, plan: e.target.value })}
                        rows={3}
                        className="mt-1"
                        data-testid="edit-plan-input"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <div className="flex items-center justify-between">
                        <Label>Data</Label>
                        {renderTemplateButton('data', true)}
                      </div>
                      <Textarea
                        value={editNote.data}
                        onChange={(e) => setEditNote({ ...editNote, data: e.target.value })}
                        rows={4}
                        className="mt-1"
                        data-testid="edit-data-input"
                      />
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <Label>Assessment</Label>
                        {renderTemplateButton('assessment', true)}
                      </div>
                      <Textarea
                        value={editNote.assessment}
                        onChange={(e) => setEditNote({ ...editNote, assessment: e.target.value })}
                        rows={3}
                        className="mt-1"
                        data-testid="edit-assessment-dap-input"
                      />
                    </div>
                    <div>
                      <div className="flex items-center justify-between">
                        <Label>Plan</Label>
                        {renderTemplateButton('plan', true)}
                      </div>
                      <Textarea
                        value={editNote.plan}
                        onChange={(e) => setEditNote({ ...editNote, plan: e.target.value })}
                        rows={3}
                        className="mt-1"
                        data-testid="edit-plan-dap-input"
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
