import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Input } from './ui/input';
import { VoiceTextarea as Textarea } from './VoiceTextarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { Plus, ClipboardCheck, Lightbulb, Eye, Share2, Lock, Calendar, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { formatDate } from '../utils/formatUtils';

const Assessments = ({ isReadOnly = false }) => {
  const [assessments, setAssessments] = useState([]);
  const [clients, setClients] = useState([]);
  const [library, setLibrary] = useState({});
  const [customAssessments, setCustomAssessments] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);
  const [showCreateCustom, setShowCreateCustom] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [newAssignment, setNewAssignment] = useState({
    client_id: '',
    assessment_type: '',
    is_custom: false,
    due_date: ''
  });
  const [newCustomAssessment, setNewCustomAssessment] = useState({
    name: '',
    description: '',
    questions: [{ q: '', options: ['', ''] }],
  });
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterClient, setFilterClient] = useState('');
  const [expandedCard, setExpandedCard] = useState(null);
  const [therapistNotes, setTherapistNotes] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [assessRes, clientsRes, libraryRes, customRes] = await Promise.all([
        axios.get(`${API}/assessments`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/assessments/library`),
        axios.get(`${API}/assessments/custom`),
      ]);
      setAssessments(assessRes.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      setClients(clientsRes.data);
      setLibrary(libraryRes.data);
      setCustomAssessments(customRes.data);
    } catch (error) {
      toast.error('Failed to load assessments');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignAssessment = async (e) => {
    e.preventDefault();

    if (!newAssignment.client_id || !newAssignment.assessment_type) {
      toast.error('Please select a client and assessment');
      return;
    }

    let assessmentData;
    let questions;
    
    if (newAssignment.is_custom) {
      const customAssess = customAssessments.find(a => a.id === newAssignment.assessment_type);
      if (!customAssess) {
        toast.error('Invalid custom assessment');
        return;
      }
      questions = customAssess.questions;
      assessmentData = {
        client_id: newAssignment.client_id,
        assessment_type: customAssess.name,
        questions: questions,
        is_custom: true,
        custom_assessment_id: customAssess.id,
        due_date: newAssignment.due_date || null
      };
    } else {
      const standardAssess = library[newAssignment.assessment_type];
      if (!standardAssess) {
        toast.error('Invalid assessment type');
        return;
      }
      questions = standardAssess.questions;
      assessmentData = {
        client_id: newAssignment.client_id,
        assessment_type: newAssignment.assessment_type,
        questions: questions,
        is_custom: false,
        due_date: newAssignment.due_date || null
      };
    }

    try {
      await axios.post(`${API}/assessments`, assessmentData);
      toast.success('Assessment assigned');
      setShowDialog(false);
      setNewAssignment({ client_id: '', assessment_type: '', is_custom: false, due_date: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign assessment');
    }
  };

  const handleCreateCustomAssessment = async (e) => {
    e.preventDefault();

    if (!newCustomAssessment.name || !newCustomAssessment.description) {
      toast.error('Name and description are required');
      return;
    }

    const validQuestions = newCustomAssessment.questions.filter(
      (q) => q.q.trim() && q.options.filter((o) => o.trim()).length >= 2
    );

    if (validQuestions.length === 0) {
      toast.error('Add at least one question with 2+ options');
      return;
    }

    try {
      await axios.post(`${API}/assessments/custom`, {
        name: newCustomAssessment.name,
        description: newCustomAssessment.description,
        questions: validQuestions,
      });
      toast.success('Custom assessment created');
      setShowCreateCustom(false);
      setNewCustomAssessment({
        name: '',
        description: '',
        questions: [{ q: '', options: ['', ''] }],
      });
      fetchData();
    } catch (error) {
      toast.error('Failed to create custom assessment');
    }
  };

  const handleViewResults = async (assessment) => {
    try {
      const res = await axios.get(`${API}/assessments/${assessment.id}/results`);
      setSelectedResult(res.data);
      setTherapistNotes(res.data.therapist_notes || '');
      setShowResults(true);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load results');
    }
  };

  const handleShareReport = async () => {
    if (!selectedResult) return;
    try {
      await axios.post(`${API}/assessments/${selectedResult.id}/share-report`);
      toast.success('Report shared with client');
      setSelectedResult({ ...selectedResult, report_shared_with_client: true });
      fetchData();
    } catch (error) {
      toast.error('Failed to share report');
    }
  };

  const handleUnshareReport = async () => {
    if (!selectedResult) return;
    try {
      await axios.post(`${API}/assessments/${selectedResult.id}/unshare-report`);
      toast.success('Report access removed');
      setSelectedResult({ ...selectedResult, report_shared_with_client: false });
      fetchData();
    } catch (error) {
      toast.error('Failed to remove access');
    }
  };

  const handleSaveNotes = async () => {
    if (!selectedResult) return;
    try {
      await axios.put(`${API}/assessments/${selectedResult.id}/therapist-notes`, {
        notes: therapistNotes
      });
      toast.success('Notes saved');
    } catch (error) {
      toast.error('Failed to save notes');
    }
  };

  const addQuestion = () => {
    setNewCustomAssessment({
      ...newCustomAssessment,
      questions: [...newCustomAssessment.questions, { q: '', options: ['', ''] }],
    });
  };

  const removeQuestion = (index) => {
    setNewCustomAssessment({
      ...newCustomAssessment,
      questions: newCustomAssessment.questions.filter((_, i) => i !== index),
    });
  };

  const updateQuestion = (index, field, value) => {
    const updatedQuestions = [...newCustomAssessment.questions];
    updatedQuestions[index][field] = value;
    setNewCustomAssessment({ ...newCustomAssessment, questions: updatedQuestions });
  };

  const addOption = (questionIndex) => {
    const updatedQuestions = [...newCustomAssessment.questions];
    updatedQuestions[questionIndex].options.push('');
    setNewCustomAssessment({ ...newCustomAssessment, questions: updatedQuestions });
  };

  const removeOption = (questionIndex, optionIndex) => {
    const updatedQuestions = [...newCustomAssessment.questions];
    updatedQuestions[questionIndex].options = updatedQuestions[questionIndex].options.filter(
      (_, i) => i !== optionIndex
    );
    setNewCustomAssessment({ ...newCustomAssessment, questions: updatedQuestions });
  };

  const updateOption = (questionIndex, optionIndex, value) => {
    const updatedQuestions = [...newCustomAssessment.questions];
    updatedQuestions[questionIndex].options[optionIndex] = value;
    setNewCustomAssessment({ ...newCustomAssessment, questions: updatedQuestions });
  };

  // Helper to get severity color
  const getSeverityColor = (severity) => {
    if (!severity) return 'bg-gray-100 text-gray-800';
    const color = severity.color?.toLowerCase();
    switch (color) {
      case 'green': return 'bg-success/10 text-success';
      case 'yellow': return 'bg-warning/10 text-warning';
      case 'orange': return 'bg-orange-100 text-orange-800';
      case 'red': return 'bg-destructive/10 text-destructive';
      case 'darkred': return 'bg-red-900/10 text-red-900';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Filter assessments
  const filteredAssessments = assessments.filter(a => {
    if (filterStatus !== 'all' && a.status !== filterStatus) return false;
    if (filterClient && a.client_id !== filterClient) return false;
    return true;
  });

  // Stats
  const totalAssessments = assessments.length;
  const pendingCount = assessments.filter(a => a.status === 'assigned').length;
  const completedCount = assessments.filter(a => a.status === 'completed').length;

  if (loading) {
    return <div className="text-center py-12">Loading assessments...</div>;
  }

  return (
    <div data-testid="assessments">
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl sm:text-4xl font-serif text-primary mb-2">Clinical Assessments</h2>
          <p className="text-muted-foreground">Assign and track standardized assessments</p>
        </div>
        {!isReadOnly && (
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={() => setShowLibrary(true)}
              variant="outline"
              data-testid="view-library-button"
            >
              <Lightbulb size={20} className="mr-2" />
              Library
            </Button>
            <Button
              onClick={() => setShowCreateCustom(true)}
              variant="outline"
              data-testid="create-custom-button"
            >
              <Plus size={20} className="mr-2" />
              Custom
            </Button>
            <Button
              onClick={() => setShowDialog(true)}
              className="bg-primary hover:bg-primary-700 rounded-full"
              data-testid="assign-assessment-button"
            >
              <Plus size={20} className="mr-2" />
              Assign
            </Button>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <p className="text-2xl font-bold text-primary">{totalAssessments}</p>
          <p className="text-sm text-muted-foreground">Total</p>
        </Card>
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <p className="text-2xl font-bold text-warning">{pendingCount}</p>
          <p className="text-sm text-muted-foreground">Pending</p>
        </Card>
        <Card className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
          <p className="text-2xl font-bold text-success">{completedCount}</p>
          <p className="text-sm text-muted-foreground">Completed</p>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="h-10 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring text-sm"
        >
          <option value="all">All Status</option>
          <option value="assigned">Pending</option>
          <option value="completed">Completed</option>
        </select>
        <select
          value={filterClient}
          onChange={(e) => setFilterClient(e.target.value)}
          className="h-10 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring text-sm"
        >
          <option value="">All Clients</option>
          {clients.map((client) => (
            <option key={client.id} value={client.id}>
              {client.full_name}
            </option>
          ))}
        </select>
      </div>

      {/* Assessments List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredAssessments.map((assess) => (
          <Card
            key={assess.id}
            className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl"
            data-testid={`assessment-${assess.id}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-medium text-lg text-foreground">{assess.client_name}</p>
                <p className="text-sm text-muted-foreground">{assess.assessment_type}</p>
              </div>
              <div className="flex items-center gap-2">
                {assess.report_shared_with_client && (
                  <Badge variant="outline" className="text-xs bg-blue-50">
                    <Share2 className="w-3 h-3 mr-1" /> Shared
                  </Badge>
                )}
                <Badge className={assess.status === 'completed' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}>
                  {assess.status}
                </Badge>
              </div>
            </div>

            {/* Due Date */}
            {assess.due_date && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                <Calendar className="w-4 h-4" />
                Due: {formatDate(assess.due_date)}
              </div>
            )}

            {/* Score Preview for Completed */}
            {assess.status === 'completed' && assess.score !== null && (
              <div className="mt-3 p-3 bg-surface rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Score: <span className="font-medium text-foreground">{assess.score}</span>
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Completed: {formatDate(assess.completed_at)}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleViewResults(assess)}
                    data-testid={`view-results-${assess.id}`}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Results
                  </Button>
                </div>
              </div>
            )}

            {/* Pending Status */}
            {assess.status === 'assigned' && (
              <div className="mt-3 p-3 bg-warning/5 rounded-lg">
                <p className="text-sm text-warning">Waiting for client to complete</p>
              </div>
            )}
          </Card>
        ))}

        {filteredAssessments.length === 0 && (
          <div className="col-span-full text-center py-12">
            <p className="text-muted-foreground">No assessments found</p>
          </div>
        )}
      </div>

      {/* Assign Assessment Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="assign-assessment-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Assign Assessment</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAssignAssessment} className="space-y-4">
            <div>
              <Label htmlFor="assess-client">Client</Label>
              <select
                id="assess-client"
                data-testid="assess-client-select"
                value={newAssignment.client_id}
                onChange={(e) => setNewAssignment({ ...newAssignment, client_id: e.target.value })}
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
              <Label htmlFor="assessment-source">Assessment Source</Label>
              <select
                id="assessment-source"
                data-testid="assessment-source-select"
                value={newAssignment.is_custom ? 'custom' : 'standard'}
                onChange={(e) =>
                  setNewAssignment({ ...newAssignment, is_custom: e.target.value === 'custom', assessment_type: '' })
                }
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="standard">Standard Library</option>
                <option value="custom">My Custom Assessments</option>
              </select>
            </div>
            <div>
              <Label htmlFor="assessment-type">
                {newAssignment.is_custom ? 'Custom Assessment' : 'Standard Assessment'}
              </Label>
              <select
                id="assessment-type"
                data-testid="assessment-type-select"
                value={newAssignment.assessment_type}
                onChange={(e) => setNewAssignment({ ...newAssignment, assessment_type: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
                required
              >
                <option value="">Select an assessment</option>
                {newAssignment.is_custom
                  ? customAssessments.map((assess) => (
                      <option key={assess.id} value={assess.id}>
                        {assess.name}
                      </option>
                    ))
                  : Object.entries(library).map(([key, value]) => (
                      <option key={key} value={key}>
                        {key} - {value.name}
                      </option>
                    ))}
              </select>
            </div>
            <div>
              <Label htmlFor="due-date">Due Date (Optional)</Label>
              <Input
                id="due-date"
                type="date"
                data-testid="due-date-input"
                value={newAssignment.due_date}
                onChange={(e) => setNewAssignment({ ...newAssignment, due_date: e.target.value })}
                className="mt-1"
              />
            </div>
            {newAssignment.assessment_type && !newAssignment.is_custom && (
              <div className="p-4 bg-surface rounded-lg">
                <p className="text-sm text-muted-foreground">
                  {library[newAssignment.assessment_type]?.description}
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  {library[newAssignment.assessment_type]?.questions?.length} questions • {library[newAssignment.assessment_type]?.time_estimate}
                </p>
              </div>
            )}
            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="confirm-assign-button">
                Assign
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                data-testid="cancel-assign-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Create Custom Assessment Dialog */}
      <Dialog open={showCreateCustom} onOpenChange={setShowCreateCustom}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" data-testid="create-custom-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Create Custom Assessment</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateCustomAssessment} className="space-y-4">
            <div>
              <Label htmlFor="custom-name">Assessment Name *</Label>
              <Input
                id="custom-name"
                data-testid="custom-name-input"
                value={newCustomAssessment.name}
                onChange={(e) => setNewCustomAssessment({ ...newCustomAssessment, name: e.target.value })}
                required
                className="mt-1"
                placeholder="e.g., Daily Mood Check-in"
              />
            </div>
            <div>
              <Label htmlFor="custom-description">Description *</Label>
              <Input
                id="custom-description"
                data-testid="custom-description-input"
                value={newCustomAssessment.description}
                onChange={(e) => setNewCustomAssessment({ ...newCustomAssessment, description: e.target.value })}
                required
                className="mt-1"
                placeholder="Brief description of this assessment"
              />
            </div>

            <div className="border-t pt-4">
              <div className="flex justify-between items-center mb-4">
                <Label className="text-lg">Questions</Label>
                <Button type="button" onClick={addQuestion} size="sm" data-testid="add-question-button">
                  <Plus size={16} className="mr-1" />
                  Add Question
                </Button>
              </div>

              {newCustomAssessment.questions.map((question, qIndex) => (
                <Card key={qIndex} className="p-4 mb-4 bg-surface" data-testid={`question-${qIndex}`}>
                  <div className="flex justify-between items-start mb-3">
                    <Label>Question {qIndex + 1}</Label>
                    {newCustomAssessment.questions.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeQuestion(qIndex)}
                        data-testid={`remove-question-${qIndex}`}
                      >
                        Remove
                      </Button>
                    )}
                  </div>
                  <Input
                    value={question.q}
                    onChange={(e) => updateQuestion(qIndex, 'q', e.target.value)}
                    placeholder="Enter question text"
                    className="mb-3"
                    data-testid={`question-text-${qIndex}`}
                  />

                  <Label className="text-sm mb-2 block">Answer Options</Label>
                  {question.options.map((option, oIndex) => (
                    <div key={oIndex} className="flex gap-2 mb-2">
                      <Input
                        value={option}
                        onChange={(e) => updateOption(qIndex, oIndex, e.target.value)}
                        placeholder={`Option ${oIndex + 1}`}
                        data-testid={`option-${qIndex}-${oIndex}`}
                      />
                      {question.options.length > 2 && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeOption(qIndex, oIndex)}
                          data-testid={`remove-option-${qIndex}-${oIndex}`}
                        >
                          Remove
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => addOption(qIndex)}
                    className="mt-2"
                    data-testid={`add-option-${qIndex}`}
                  >
                    <Plus size={16} className="mr-1" />
                    Add Option
                  </Button>
                </Card>
              ))}
            </div>

            <div className="flex gap-3">
              <Button type="submit" className="flex-1" data-testid="save-custom-assessment-button">
                Create Assessment
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateCustom(false)}
                data-testid="cancel-custom-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Assessment Library Dialog */}
      <Dialog open={showLibrary} onOpenChange={setShowLibrary}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="library-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Assessment Library</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {Object.entries(library).map(([key, value]) => (
              <Card key={key} className="p-4 bg-surface" data-testid={`library-item-${key}`}>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-medium text-lg text-primary">{key}</h4>
                    <p className="text-sm text-foreground">{value.name}</p>
                  </div>
                  <Badge variant="outline">{value.category}</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{value.description}</p>
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span>{value.questions?.length} questions</span>
                  <span>{value.time_estimate}</span>
                  <span>Max: {value.max_score}</span>
                </div>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Assessment Results Dialog */}
      <Dialog open={showResults} onOpenChange={setShowResults}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" data-testid="results-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Assessment Results</DialogTitle>
          </DialogHeader>
          {selectedResult && (
            <div className="space-y-6">
              {/* Client & Assessment Info */}
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium text-lg">{selectedResult.client_name}</p>
                  <p className="text-sm text-muted-foreground">{selectedResult.assessment_type}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Completed: {formatDate(selectedResult.completed_at)}
                  </p>
                </div>
                {!isReadOnly && (
                  <div className="flex gap-2">
                    {selectedResult.report_shared_with_client ? (
                      <Button variant="outline" size="sm" onClick={handleUnshareReport} data-testid="unshare-btn">
                        <Lock className="w-4 h-4 mr-1" />
                        Revoke Access
                      </Button>
                    ) : (
                      <Button size="sm" onClick={handleShareReport} data-testid="share-btn">
                        <Share2 className="w-4 h-4 mr-1" />
                        Share with Client
                      </Button>
                    )}
                  </div>
                )}
              </div>

              {/* Score Summary */}
              <Card className="p-4 bg-surface">
                <div className="flex flex-wrap gap-6">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Score</p>
                    <p className="text-3xl font-bold text-primary">{selectedResult.score}</p>
                    {selectedResult.score_details?.max_score && (
                      <p className="text-xs text-muted-foreground">out of {selectedResult.score_details.max_score}</p>
                    )}
                  </div>
                  {selectedResult.score_details?.severity && (
                    <div>
                      <p className="text-sm text-muted-foreground">Severity</p>
                      <Badge className={`text-base mt-1 ${getSeverityColor(selectedResult.score_details.severity)}`}>
                        {selectedResult.score_details.severity.label}
                      </Badge>
                    </div>
                  )}
                  {/* Subscores for multi-scale assessments */}
                  {selectedResult.score_details?.subscores && Object.keys(selectedResult.score_details.subscores).length > 0 && (
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground mb-2">Subscales</p>
                      <div className="flex flex-wrap gap-3">
                        {Object.entries(selectedResult.score_details.subscores).map(([scale, data]) => (
                          <div key={scale} className="text-center">
                            <p className="text-xs text-muted-foreground capitalize">{scale}</p>
                            <p className="font-medium">{data.score}</p>
                            {data.severity && (
                              <Badge variant="outline" className={`text-xs ${getSeverityColor(data.severity)}`}>
                                {data.severity.label}
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              {/* Detailed Responses */}
              <div>
                <h4 className="font-medium mb-3">Responses</h4>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {selectedResult.questions?.map((q, idx) => {
                    const answer = selectedResult.answers?.[idx];
                    return (
                      <div key={idx} className="p-3 bg-surface rounded-lg">
                        <p className="text-sm font-medium mb-1">{idx + 1}. {q.text}</p>
                        <p className="text-sm text-primary">
                          {answer?.label || 'Not answered'} 
                          {answer?.value !== undefined && <span className="text-muted-foreground ml-2">({answer.value})</span>}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Therapist Notes */}
              {!isReadOnly && (
                <div>
                  <Label className="mb-2 block">Clinical Notes</Label>
                  <Textarea
                    value={therapistNotes}
                    onChange={(e) => setTherapistNotes(e.target.value)}
                    placeholder="Add your clinical observations and interpretations..."
                    rows={4}
                    data-testid="therapist-notes-input"
                  />
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="mt-2"
                    onClick={handleSaveNotes}
                    data-testid="save-notes-btn"
                  >
                    <FileText className="w-4 h-4 mr-1" />
                    Save Notes
                  </Button>
                </div>
              )}

              {/* Sharing Status */}
              <div className={`p-4 rounded-lg ${selectedResult.report_shared_with_client ? 'bg-blue-50 border border-blue-200' : 'bg-amber-50 border border-amber-200'}`}>
                <p className="text-sm">
                  {selectedResult.report_shared_with_client ? (
                    <>
                      <Share2 className="w-4 h-4 inline mr-2 text-blue-600" />
                      <span className="text-blue-800">This report is visible to the client.</span>
                    </>
                  ) : (
                    <>
                      <Lock className="w-4 h-4 inline mr-2 text-amber-600" />
                      <span className="text-amber-800">This report is private. Client cannot see the results.</span>
                    </>
                  )}
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Clinical Notice */}
      <div className="mt-8 p-6 bg-info/10 border border-info/20 rounded-xl">
        <p className="text-sm text-info">
          <strong>Clinical Tool:</strong> Assessments are screening tools only. All diagnoses and treatment
          decisions must be made by the licensed therapist based on comprehensive clinical evaluation.
        </p>
      </div>
    </div>
  );
};

export default Assessments;
