import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Plus, ClipboardCheck, Lightbulb } from 'lucide-react';

const Assessments = () => {
  const [assessments, setAssessments] = useState([]);
  const [clients, setClients] = useState([]);
  const [library, setLibrary] = useState({});
  const [customAssessments, setCustomAssessments] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);
  const [showCreateCustom, setShowCreateCustom] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [newAssignment, setNewAssignment] = useState({
    client_id: '',
    assessment_type: '',
    is_custom: false,
  });
  const [newCustomAssessment, setNewCustomAssessment] = useState({
    name: '',
    description: '',
    questions: [{ q: '', options: ['', ''] }],
  });
  const [loading, setLoading] = useState(true);

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
      // Custom assessment
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
      };
    } else {
      // Standard library assessment
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
      };
    }

    try {
      await axios.post(`${API}/assessments`, assessmentData);
      toast.success('Assessment assigned');
      setShowDialog(false);
      setNewAssignment({ client_id: '', assessment_type: '', is_custom: false });
      fetchData();
    } catch (error) {
      toast.error('Failed to assign assessment');
    }
  };

  const handleCreateCustomAssessment = async (e) => {
    e.preventDefault();

    // Validate
    if (!newCustomAssessment.name || !newCustomAssessment.description) {
      toast.error('Name and description are required');
      return;
    }

    // Validate questions
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

  if (loading) {
    return <div className="text-center py-12">Loading assessments...</div>;
  }

  return (
    <div data-testid="assessments">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Clinical Assessments</h2>
          <p className="text-muted-foreground">Assign and track standardized assessments</p>
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => setShowLibrary(true)}
            variant="outline"
            data-testid="view-library-button"
          >
            <Lightbulb size={20} className="mr-2" />
            View Library
          </Button>
          <Button
            onClick={() => setShowDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="assign-assessment-button"
          >
            <Plus size={20} className="mr-2" />
            Assign Assessment
          </Button>
        </div>
      </div>

      {/* Assessments List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {assessments.map((assess) => (
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
              <span
                className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                  assess.status === 'completed'
                    ? 'bg-success/10 text-success'
                    : 'bg-warning/10 text-warning'
                }`}
              >
                {assess.status}
              </span>
            </div>
            {assess.status === 'completed' && assess.score !== null && (
              <div className="mt-3 p-3 bg-surface rounded-lg">
                <p className="text-sm text-muted-foreground">Score: <span className="font-medium text-foreground">{assess.score}</span></p>
                <p className="text-xs text-muted-foreground mt-1">
                  Completed: {new Date(assess.completed_at).toLocaleDateString()}
                </p>
              </div>
            )}
          </Card>
        ))}

        {assessments.length === 0 && (
          <div className="col-span-full text-center py-12">
            <p className="text-muted-foreground">No assessments assigned yet</p>
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
              <Label htmlFor="assessment-type">Assessment</Label>
              <select
                id="assessment-type"
                data-testid="assessment-type-select"
                value={newAssignment.assessment_type}
                onChange={(e) => setNewAssignment({ ...newAssignment, assessment_type: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
                required
              >
                <option value="">Select an assessment</option>
                {Object.entries(library).map(([key, value]) => (
                  <option key={key} value={key}>
                    {key} - {value.name}
                  </option>
                ))}
              </select>
            </div>
            {newAssignment.assessment_type && library[newAssignment.assessment_type] && (
              <div className="p-4 bg-surface rounded-lg">
                <p className="text-sm text-muted-foreground">
                  {library[newAssignment.assessment_type].description}
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
          <div className="mt-4 p-4 bg-warning/10 border border-warning/20 rounded-lg">
            <p className="text-sm text-warning">
              <strong>Therapist Approval Required:</strong> Client will complete this assessment, but results
              require your clinical interpretation.
            </p>
          </div>
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
                <h4 className="font-medium text-lg text-primary mb-1">{key}</h4>
                <p className="text-sm text-foreground mb-2">{value.name}</p>
                <p className="text-sm text-muted-foreground mb-3">{value.description}</p>
                <p className="text-xs text-muted-foreground">
                  {value.questions.length} questions
                </p>
              </Card>
            ))}
          </div>
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
