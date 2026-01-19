import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { toast } from 'sonner';
import { 
  Brain, 
  ClipboardCheck, 
  BookOpen, 
  FileText, 
  Sparkles, 
  Loader2, 
  ChevronRight,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle2,
  Plus,
  Send,
  Download,
  Library
} from 'lucide-react';

const AIClinicalSupport = ({ isReadOnly = false }) => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('assessments');
  
  // Assessment Suggestion State
  const [assessmentRequest, setAssessmentRequest] = useState({
    client_id: '',
    query: '',
    include_intake: true,
    include_notes: true
  });
  const [assessmentSuggestions, setAssessmentSuggestions] = useState(null);
  const [loadingAssessment, setLoadingAssessment] = useState(false);

  // Protocol Builder State
  const [protocolRequest, setProtocolRequest] = useState({
    client_id: '',
    query: '',
    modality_preference: ''
  });
  const [generatedProtocol, setGeneratedProtocol] = useState(null);
  const [loadingProtocol, setLoadingProtocol] = useState(false);
  const [showProtocolDialog, setShowProtocolDialog] = useState(false);

  // Homework Generator State
  const [homeworkRequest, setHomeworkRequest] = useState({
    client_id: '',
    context: '',
    homework_type: 'exercise'
  });
  const [generatedHomework, setGeneratedHomework] = useState(null);
  const [loadingHomework, setLoadingHomework] = useState(false);
  const [showHomeworkDialog, setShowHomeworkDialog] = useState(false);

  // Resources State
  const [resources, setResources] = useState([]);
  const [showResourceDialog, setShowResourceDialog] = useState(false);
  const [newResource, setNewResource] = useState({
    title: '',
    category: 'worksheet',
    content: '',
    tags: []
  });

  useEffect(() => {
    fetchClients();
    fetchResources();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
    } catch (error) {
      toast.error('Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const fetchResources = async () => {
    try {
      const response = await axios.get(`${API}/resources`);
      setResources(response.data);
    } catch (error) {
      console.error('Failed to load resources:', error);
    }
  };

  // ============= ASSESSMENT SUGGESTIONS =============
  const handleSuggestAssessments = async () => {
    if (!assessmentRequest.client_id && !assessmentRequest.query) {
      toast.error('Please select a client or enter a query');
      return;
    }

    setLoadingAssessment(true);
    try {
      const response = await axios.post(`${API}/ai/suggest-assessments`, assessmentRequest);
      setAssessmentSuggestions(response.data);
      toast.success('Assessment suggestions generated');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate suggestions');
    } finally {
      setLoadingAssessment(false);
    }
  };

  // ============= PROTOCOL BUILDER =============
  const handleGenerateProtocol = async () => {
    if (!protocolRequest.client_id && !protocolRequest.query) {
      toast.error('Please select a client or describe the situation');
      return;
    }

    setLoadingProtocol(true);
    try {
      const response = await axios.post(`${API}/ai/generate-protocol`, protocolRequest);
      setGeneratedProtocol(response.data);
      setShowProtocolDialog(true);
      toast.success('Protocol generated successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate protocol');
    } finally {
      setLoadingProtocol(false);
    }
  };

  const handleSaveProtocol = async () => {
    if (!generatedProtocol || !protocolRequest.client_id) {
      toast.error('Please select a client to save the protocol');
      return;
    }

    try {
      await axios.post(`${API}/protocols`, {
        client_id: protocolRequest.client_id,
        modality: generatedProtocol.recommended_modality,
        condition: generatedProtocol.target_condition,
        sessions: generatedProtocol.sessions.map(s => ({
          number: s.session_number,
          title: s.title,
          objectives: s.objectives,
          interventions: s.interventions,
          homework: s.homework,
          status: 'pending'
        }))
      });
      toast.success('Protocol saved to client profile');
      setShowProtocolDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save protocol');
    }
  };

  // ============= HOMEWORK GENERATOR =============
  const handleGenerateHomework = async () => {
    if (!homeworkRequest.client_id) {
      toast.error('Please select a client');
      return;
    }

    setLoadingHomework(true);
    try {
      const response = await axios.post(`${API}/ai/generate-homework`, homeworkRequest);
      setGeneratedHomework(response.data);
      setShowHomeworkDialog(true);
      toast.success('Homework generated successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate homework');
    } finally {
      setLoadingHomework(false);
    }
  };

  const handleAssignHomework = async () => {
    if (!generatedHomework || !homeworkRequest.client_id) return;

    try {
      await axios.post(`${API}/homework`, {
        client_id: homeworkRequest.client_id,
        title: generatedHomework.title,
        description: `${generatedHomework.description}\n\n${generatedHomework.instructions}\n\nExercises:\n${generatedHomework.exercises.map(e => `• ${e.name}: ${e.description}`).join('\n')}\n\nEstimated time: ${generatedHomework.estimated_time_minutes} minutes`
      });
      toast.success('Homework assigned to client');
      setShowHomeworkDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign homework');
    }
  };

  // ============= RESOURCES =============
  const handleCreateResource = async () => {
    if (!newResource.title || !newResource.content) {
      toast.error('Please fill in title and content');
      return;
    }

    try {
      await axios.post(`${API}/resources`, newResource);
      toast.success('Resource created');
      setShowResourceDialog(false);
      setNewResource({ title: '', category: 'worksheet', content: '', tags: [] });
      fetchResources();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create resource');
    }
  };

  const handleAssignResource = async (resourceId, clientId) => {
    try {
      await axios.post(`${API}/resources/${resourceId}/assign?client_id=${clientId}`);
      toast.success('Resource assigned to client');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign resource');
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-error/10 text-error border-error/30';
      case 'medium': return 'bg-warning/10 text-warning border-warning/30';
      case 'low': return 'bg-info/10 text-info border-info/30';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div data-testid="ai-clinical-support" className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Brain className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-4xl font-serif text-primary">AI Clinical Support</h2>
            <p className="text-muted-foreground">Powered by Gemini 3 Flash</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 mb-6">
          <TabsTrigger value="assessments" className="flex items-center gap-2">
            <ClipboardCheck size={16} />
            Assessments
          </TabsTrigger>
          <TabsTrigger value="protocols" className="flex items-center gap-2">
            <BookOpen size={16} />
            Protocols
          </TabsTrigger>
          <TabsTrigger value="homework" className="flex items-center gap-2">
            <FileText size={16} />
            Homework
          </TabsTrigger>
          <TabsTrigger value="resources" className="flex items-center gap-2">
            <Library size={16} />
            Resources
          </TabsTrigger>
        </TabsList>

        {/* Assessment Suggestions Tab */}
        <TabsContent value="assessments" className="space-y-6">
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center gap-3 mb-4">
              <Sparkles className="text-purple-500" size={20} />
              <h3 className="text-lg font-semibold">AI Assessment Suggestions</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Get AI-powered suggestions for clinical assessments based on client data or your observations.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <Label>Select Client (optional)</Label>
                <Select 
                  value={assessmentRequest.client_id || "none"} 
                  onValueChange={(v) => setAssessmentRequest({...assessmentRequest, client_id: v === "none" ? "" : v})}
                >
                  <SelectTrigger data-testid="assessment-client-select">
                    <SelectValue placeholder="Choose a client" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    {clients.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.full_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input 
                    type="checkbox" 
                    checked={assessmentRequest.include_intake}
                    onChange={(e) => setAssessmentRequest({...assessmentRequest, include_intake: e.target.checked})}
                    className="rounded"
                  />
                  Include Intake
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input 
                    type="checkbox" 
                    checked={assessmentRequest.include_notes}
                    onChange={(e) => setAssessmentRequest({...assessmentRequest, include_notes: e.target.checked})}
                    className="rounded"
                  />
                  Include Notes
                </label>
              </div>
            </div>

            <div className="mb-4">
              <Label>Your Observations / Query</Label>
              <Textarea
                placeholder="Describe the client's presenting concerns, symptoms, or what you'd like to assess..."
                value={assessmentRequest.query}
                onChange={(e) => setAssessmentRequest({...assessmentRequest, query: e.target.value})}
                rows={3}
                data-testid="assessment-query-input"
              />
            </div>

            <Button 
              onClick={handleSuggestAssessments} 
              disabled={loadingAssessment || isReadOnly}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              data-testid="suggest-assessments-btn"
            >
              {loadingAssessment ? (
                <><Loader2 className="mr-2 animate-spin" size={16} /> Analyzing...</>
              ) : (
                <><Sparkles className="mr-2" size={16} /> Get AI Suggestions</>
              )}
            </Button>
          </Card>

          {/* Assessment Results */}
          {assessmentSuggestions && (
            <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
              <h3 className="text-lg font-semibold mb-2">AI Analysis</h3>
              <p className="text-muted-foreground mb-4">{assessmentSuggestions.analysis_summary}</p>
              <p className="text-xs text-muted-foreground mb-4">
                Data sources: {assessmentSuggestions.data_sources_used.join(', ')}
              </p>

              <h4 className="font-medium mb-3">Suggested Assessments</h4>
              <div className="space-y-3">
                {assessmentSuggestions.suggestions.map((s, idx) => (
                  <Card key={idx} className={`p-4 border ${getPriorityColor(s.priority)}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold">{s.assessment_type}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getPriorityColor(s.priority)}`}>
                            {s.priority} priority
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground">{s.assessment_name}</p>
                        <p className="text-sm mt-2">{s.reason}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {s.relevant_symptoms.map((symptom, i) => (
                            <span key={i} className="text-xs bg-muted px-2 py-0.5 rounded-full">
                              {symptom}
                            </span>
                          ))}
                        </div>
                      </div>
                      <Button variant="outline" size="sm" disabled={isReadOnly}>
                        Assign
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Protocol Builder Tab */}
        <TabsContent value="protocols" className="space-y-6">
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center gap-3 mb-4">
              <BookOpen className="text-blue-500" size={20} />
              <h3 className="text-lg font-semibold">AI Protocol Builder</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Generate evidence-based therapy protocols tailored to your client's needs.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <Label>Select Client</Label>
                <Select 
                  value={protocolRequest.client_id || undefined} 
                  onValueChange={(v) => setProtocolRequest({...protocolRequest, client_id: v})}
                >
                  <SelectTrigger data-testid="protocol-client-select">
                    <SelectValue placeholder="Choose a client" />
                  </SelectTrigger>
                  <SelectContent>
                    {clients.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.full_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Preferred Modality (optional)</Label>
                <Select 
                  value={protocolRequest.modality_preference || "auto"} 
                  onValueChange={(v) => setProtocolRequest({...protocolRequest, modality_preference: v === "auto" ? "" : v})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Let AI decide" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Let AI decide</SelectItem>
                    <SelectItem value="CBT">CBT (Cognitive Behavioral)</SelectItem>
                    <SelectItem value="DBT">DBT (Dialectical Behavior)</SelectItem>
                    <SelectItem value="ACT">ACT (Acceptance & Commitment)</SelectItem>
                    <SelectItem value="EMDR">EMDR</SelectItem>
                    <SelectItem value="Psychodynamic">Psychodynamic</SelectItem>
                    <SelectItem value="Mindfulness">Mindfulness-Based</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="mb-4">
              <Label>Describe the Situation</Label>
              <Textarea
                placeholder="Describe the client's condition, assessment results, treatment goals..."
                value={protocolRequest.query}
                onChange={(e) => setProtocolRequest({...protocolRequest, query: e.target.value})}
                rows={4}
                data-testid="protocol-query-input"
              />
            </div>

            <Button 
              onClick={handleGenerateProtocol} 
              disabled={loadingProtocol || isReadOnly}
              className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
              data-testid="generate-protocol-btn"
            >
              {loadingProtocol ? (
                <><Loader2 className="mr-2 animate-spin" size={16} /> Generating...</>
              ) : (
                <><Sparkles className="mr-2" size={16} /> Generate Protocol</>
              )}
            </Button>
          </Card>
        </TabsContent>

        {/* Homework Tab */}
        <TabsContent value="homework" className="space-y-6">
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="text-green-500" size={20} />
              <h3 className="text-lg font-semibold">AI Homework Generator</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Create personalized therapeutic homework and exercises for your clients.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <Label>Select Client *</Label>
                <Select 
                  value={homeworkRequest.client_id || undefined} 
                  onValueChange={(v) => setHomeworkRequest({...homeworkRequest, client_id: v})}
                >
                  <SelectTrigger data-testid="homework-client-select">
                    <SelectValue placeholder="Choose a client" />
                  </SelectTrigger>
                  <SelectContent>
                    {clients.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.full_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Homework Type</Label>
                <Select 
                  value={homeworkRequest.homework_type || "exercise"} 
                  onValueChange={(v) => setHomeworkRequest({...homeworkRequest, homework_type: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="worksheet">Worksheet</SelectItem>
                    <SelectItem value="exercise">Behavioral Exercise</SelectItem>
                    <SelectItem value="reflection">Reflection/Journaling</SelectItem>
                    <SelectItem value="reading">Psychoeducation</SelectItem>
                    <SelectItem value="meditation">Mindfulness/Meditation</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="mb-4">
              <Label>Session Context (optional)</Label>
              <Textarea
                placeholder="What was discussed in the session? What skills should the homework reinforce?"
                value={homeworkRequest.context}
                onChange={(e) => setHomeworkRequest({...homeworkRequest, context: e.target.value})}
                rows={3}
                data-testid="homework-context-input"
              />
            </div>

            <Button 
              onClick={handleGenerateHomework} 
              disabled={loadingHomework || isReadOnly || !homeworkRequest.client_id}
              className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
              data-testid="generate-homework-btn"
            >
              {loadingHomework ? (
                <><Loader2 className="mr-2 animate-spin" size={16} /> Generating...</>
              ) : (
                <><Sparkles className="mr-2" size={16} /> Generate Homework</>
              )}
            </Button>
          </Card>
        </TabsContent>

        {/* Resources Tab */}
        <TabsContent value="resources" className="space-y-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-semibold">Resource Library</h3>
              <p className="text-sm text-muted-foreground">Worksheets, exercises, and psychoeducation materials</p>
            </div>
            {!isReadOnly && (
              <Button onClick={() => setShowResourceDialog(true)} data-testid="create-resource-btn">
                <Plus size={16} className="mr-2" /> Add Resource
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {resources.map(resource => (
              <Card key={resource.id} className="p-4 bg-white/70 backdrop-blur-xl border border-border/40">
                <div className="flex items-start justify-between mb-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    resource.category === 'worksheet' ? 'bg-purple-100 text-purple-700' :
                    resource.category === 'exercise' ? 'bg-green-100 text-green-700' :
                    resource.category === 'psychoeducation' ? 'bg-blue-100 text-blue-700' :
                    resource.category === 'meditation' ? 'bg-pink-100 text-pink-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {resource.category}
                  </span>
                  <span className="text-xs text-muted-foreground">Used {resource.usage_count}x</span>
                </div>
                <h4 className="font-medium mb-2">{resource.title}</h4>
                <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
                  {resource.content.substring(0, 150)}...
                </p>
                <div className="flex gap-2">
                  <Select onValueChange={(clientId) => handleAssignResource(resource.id, clientId)}>
                    <SelectTrigger className="flex-1" disabled={isReadOnly}>
                      <SelectValue placeholder="Assign to..." />
                    </SelectTrigger>
                    <SelectContent>
                      {clients.map(c => (
                        <SelectItem key={c.id} value={c.id}>{c.full_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </Card>
            ))}
          </div>

          {resources.length === 0 && (
            <Card className="p-8 text-center bg-white/70 backdrop-blur-xl border border-border/40">
              <Library className="mx-auto text-muted-foreground mb-4" size={48} />
              <h3 className="font-medium mb-2">No Resources Yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create worksheets, exercises, and educational materials for your clients.
              </p>
              {!isReadOnly && (
                <Button onClick={() => setShowResourceDialog(true)}>
                  <Plus size={16} className="mr-2" /> Create First Resource
                </Button>
              )}
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Protocol Dialog */}
      <Dialog open={showProtocolDialog} onOpenChange={setShowProtocolDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <BookOpen className="text-blue-500" size={20} />
              Generated Treatment Protocol
            </DialogTitle>
          </DialogHeader>

          {generatedProtocol && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">Protocol Name</Label>
                  <p className="font-medium">{generatedProtocol.protocol_name}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Target Condition</Label>
                  <p className="font-medium">{generatedProtocol.target_condition}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Modality</Label>
                  <p className="font-medium">{generatedProtocol.recommended_modality}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">Estimated Sessions</Label>
                  <p className="font-medium">{generatedProtocol.estimated_sessions}</p>
                </div>
              </div>

              <div>
                <Label className="text-muted-foreground">Rationale</Label>
                <p className="text-sm mt-1">{generatedProtocol.rationale}</p>
              </div>

              {generatedProtocol.contraindications?.length > 0 && (
                <div className="p-3 bg-warning/10 rounded-lg border border-warning/30">
                  <div className="flex items-center gap-2 text-warning mb-2">
                    <AlertTriangle size={16} />
                    <span className="font-medium">Contraindications</span>
                  </div>
                  <ul className="text-sm list-disc pl-5">
                    {generatedProtocol.contraindications.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div>
                <Label className="text-muted-foreground mb-2 block">Session Plan</Label>
                <div className="space-y-3">
                  {generatedProtocol.sessions.map((session, idx) => (
                    <Card key={idx} className="p-4 border">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-medium">
                          {session.session_number}
                        </span>
                        <span className="font-medium">{session.title}</span>
                        <span className="text-xs text-muted-foreground ml-auto">
                          <Clock size={12} className="inline mr-1" />
                          {session.duration_minutes} min
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground mb-1">Objectives:</p>
                          <ul className="list-disc pl-4">
                            {session.objectives.map((o, i) => <li key={i}>{o}</li>)}
                          </ul>
                        </div>
                        <div>
                          <p className="text-muted-foreground mb-1">Interventions:</p>
                          <ul className="list-disc pl-4">
                            {session.interventions.map((i, idx) => <li key={idx}>{i}</li>)}
                          </ul>
                        </div>
                      </div>

                      {session.homework && (
                        <div className="mt-2 p-2 bg-muted/50 rounded text-sm">
                          <span className="font-medium">Homework:</span> {session.homework}
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-muted-foreground">Progress Markers</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {generatedProtocol.progress_markers.map((m, i) => (
                    <span key={i} className="flex items-center gap-1 text-sm bg-success/10 text-success px-2 py-1 rounded-full">
                      <CheckCircle2 size={12} /> {m}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setShowProtocolDialog(false)}>
                  Close
                </Button>
                <Button onClick={handleSaveProtocol} disabled={!protocolRequest.client_id || isReadOnly}>
                  <CheckCircle2 size={16} className="mr-2" /> Save to Client
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Homework Dialog */}
      <Dialog open={showHomeworkDialog} onOpenChange={setShowHomeworkDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="text-green-500" size={20} />
              Generated Homework
            </DialogTitle>
          </DialogHeader>

          {generatedHomework && (
            <div className="space-y-4">
              <div>
                <Label className="text-muted-foreground">Title</Label>
                <p className="font-medium text-lg">{generatedHomework.title}</p>
              </div>

              <div>
                <Label className="text-muted-foreground">Description</Label>
                <p className="text-sm">{generatedHomework.description}</p>
              </div>

              <div>
                <Label className="text-muted-foreground">Instructions</Label>
                <p className="text-sm whitespace-pre-wrap bg-muted/50 p-3 rounded">
                  {generatedHomework.instructions}
                </p>
              </div>

              <div>
                <Label className="text-muted-foreground">Exercises</Label>
                <div className="space-y-3 mt-2">
                  {generatedHomework.exercises.map((ex, idx) => (
                    <Card key={idx} className="p-3 border">
                      <p className="font-medium">{ex.name}</p>
                      <p className="text-sm text-muted-foreground mb-2">{ex.description}</p>
                      {ex.steps && (
                        <ol className="list-decimal pl-5 text-sm">
                          {ex.steps.map((step, i) => <li key={i}>{step}</li>)}
                        </ol>
                      )}
                    </Card>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-muted/50 rounded">
                <span className="text-sm">
                  <Clock size={14} className="inline mr-1" />
                  Estimated time: {generatedHomework.estimated_time_minutes} minutes
                </span>
              </div>

              <div className="p-3 bg-info/10 rounded border border-info/30">
                <p className="text-sm"><strong>Therapeutic Rationale:</strong> {generatedHomework.therapeutic_rationale}</p>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setShowHomeworkDialog(false)}>
                  Close
                </Button>
                <Button onClick={handleAssignHomework} disabled={isReadOnly}>
                  <Send size={16} className="mr-2" /> Assign to Client
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Resource Dialog */}
      <Dialog open={showResourceDialog} onOpenChange={setShowResourceDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Create New Resource</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label>Title *</Label>
              <Input
                value={newResource.title}
                onChange={(e) => setNewResource({...newResource, title: e.target.value})}
                placeholder="e.g., Anxiety Thought Record"
                data-testid="resource-title-input"
              />
            </div>

            <div>
              <Label>Category *</Label>
              <Select 
                value={newResource.category} 
                onValueChange={(v) => setNewResource({...newResource, category: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="worksheet">Worksheet</SelectItem>
                  <SelectItem value="exercise">Exercise</SelectItem>
                  <SelectItem value="psychoeducation">Psychoeducation</SelectItem>
                  <SelectItem value="reading">Reading Material</SelectItem>
                  <SelectItem value="meditation">Meditation/Mindfulness</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Content *</Label>
              <Textarea
                value={newResource.content}
                onChange={(e) => setNewResource({...newResource, content: e.target.value})}
                placeholder="Enter the full content of the resource..."
                rows={10}
                data-testid="resource-content-input"
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowResourceDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateResource} data-testid="save-resource-btn">
                Create Resource
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AIClinicalSupport;
