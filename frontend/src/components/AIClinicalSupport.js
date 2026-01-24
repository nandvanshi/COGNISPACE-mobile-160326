import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
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
  Library,
  FileSearch,
  Eye,
  Share2,
  Edit3,
  Trash2,
  Save,
  Printer
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
    include_notes: true,
    include_case_history: true,
    include_prev_assessments: true
  });
  const [assessmentSuggestions, setAssessmentSuggestions] = useState(null);
  const [loadingAssessment, setLoadingAssessment] = useState(false);

  // Protocol Builder State
  const [protocolRequest, setProtocolRequest] = useState({
    client_id: '',
    query: '',
    modality_preference: '',
    include_case_history: true,
    include_prev_assessments: true
  });
  const [generatedProtocol, setGeneratedProtocol] = useState(null);
  const [loadingProtocol, setLoadingProtocol] = useState(false);
  const [showProtocolDialog, setShowProtocolDialog] = useState(false);

  // Homework Generator State
  const [homeworkRequest, setHomeworkRequest] = useState({
    client_id: '',
    context: '',
    homework_type: 'exercise',
    include_case_history: true,
    include_prev_assessments: true
  });
  const [generatedHomework, setGeneratedHomework] = useState(null);
  const [loadingHomework, setLoadingHomework] = useState(false);
  const [showHomeworkDialog, setShowHomeworkDialog] = useState(false);

  // CogniVision Diagnostic Reports State
  const [diagnosticRequest, setDiagnosticRequest] = useState({
    client_id: '',
    assessment_ids: [],
    include_intake: true,
    include_session_history: true,
    include_case_history: true,
    therapist_notes: ''
  });
  const [completedAssessments, setCompletedAssessments] = useState([]);
  const [generatedReport, setGeneratedReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [savedReports, setSavedReports] = useState([]);
  const [showReportEditor, setShowReportEditor] = useState(false);
  const [editableReport, setEditableReport] = useState('');
  const [currentReportId, setCurrentReportId] = useState(null);
  const [showReportPreview, setShowReportPreview] = useState(false);
  const [previewReport, setPreviewReport] = useState(null);
  const reportEditorRef = useRef(null);

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
    fetchSavedReports();
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

  const fetchSavedReports = async () => {
    try {
      const response = await axios.get(`${API}/diagnostic-reports`);
      setSavedReports(response.data);
    } catch (error) {
      console.error('Failed to load reports:', error);
    }
  };

  const fetchClientAssessments = async (clientId) => {
    try {
      const response = await axios.get(`${API}/assessments?client_id=${clientId}&status=completed`);
      setCompletedAssessments(response.data);
    } catch (error) {
      console.error('Failed to load assessments:', error);
      setCompletedAssessments([]);
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

  // ============= COGNIVISION DIAGNOSTIC REPORTS =============
  const handleGenerateDiagnosticReport = async () => {
    if (!diagnosticRequest.client_id) {
      toast.error('Please select a client');
      return;
    }
    if (diagnosticRequest.assessment_ids.length === 0 && !diagnosticRequest.therapist_notes.trim()) {
      toast.error('Please select assessments or provide clinical observations');
      return;
    }

    setLoadingReport(true);
    try {
      const response = await axios.post(`${API}/ai/generate-diagnostic-report`, diagnosticRequest);
      setGeneratedReport(response.data);
      setEditableReport(response.data.raw_html);
      setShowReportEditor(true);
      toast.success('Diagnostic report generated by CogniVision');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate report');
    } finally {
      setLoadingReport(false);
    }
  };

  const handleSaveReport = async (status = 'draft') => {
    try {
      const reportData = {
        client_id: diagnosticRequest.client_id,
        assessment_ids: diagnosticRequest.assessment_ids,
        report_content: editableReport,
        status: status
      };

      if (currentReportId) {
        await axios.put(`${API}/diagnostic-reports/${currentReportId}`, { report_content: editableReport });
        toast.success('Report updated');
      } else {
        const response = await axios.post(`${API}/diagnostic-reports`, reportData);
        setCurrentReportId(response.data.id);
        toast.success('Report saved as draft');
      }
      fetchSavedReports();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save report');
    }
  };

  const handleApproveReport = async () => {
    if (!currentReportId) {
      await handleSaveReport('approved');
      return;
    }
    try {
      await axios.post(`${API}/diagnostic-reports/${currentReportId}/approve`);
      toast.success('Report approved');
      fetchSavedReports();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve report');
    }
  };

  const handleShareReport = async (reportId) => {
    try {
      await axios.post(`${API}/diagnostic-reports/${reportId}/share`);
      toast.success('Report shared with client');
      fetchSavedReports();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to share report');
    }
  };

  const handleDeleteReport = async (reportId) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await axios.delete(`${API}/diagnostic-reports/${reportId}`);
      toast.success('Report deleted');
      fetchSavedReports();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete report');
    }
  };

  const handleViewReport = async (report) => {
    setPreviewReport(report);
    setShowReportPreview(true);
  };

  const handleEditReport = (report) => {
    setCurrentReportId(report.id);
    setEditableReport(report.report_content);
    setShowReportEditor(true);
  };

  const handlePrintReport = () => {
    const printWindow = window.open('', '_blank');
    const reportContent = editableReport || previewReport?.report_content;
    
    // Get current date in DD/MM/YYYY format
    const today = new Date();
    const reportDate = `${today.getDate().toString().padStart(2, '0')}/${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getFullYear()}`;
    
    printWindow.document.write(`
<!DOCTYPE html>
<html>
<head>
  <title>Psychodiagnostic Evaluation Report</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    /* Print Settings - Remove ALL Browser Headers/Footers */
    @media print {
      @page { 
        margin: 2cm; 
        size: A4;
      }
      html, body {
        margin: 0 !important;
        padding: 0 !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
      .no-print { display: none !important; }
    }
    
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
      font-family: 'Inter', Arial, sans-serif;
      font-size: 11pt;
      color: #000;
      line-height: 1.6;
      background: #fff;
      padding: 0;
    }
    
    .clinical-report {
      max-width: 210mm;
      margin: 0 auto;
      padding: 0;
    }
    
    /* Therapist Header - Navy Blue #000080 */
    .therapist-header {
      margin-bottom: 25px;
      padding-bottom: 15px;
      border-bottom: 2px solid #000080;
    }
    .therapist-header h1 {
      font-size: 18pt;
      font-weight: 700;
      margin: 0 0 5px 0;
      color: #000080;
    }
    .therapist-header p {
      margin: 3px 0;
      font-size: 10pt;
      color: #333;
      display: block;
    }
    
    /* Report Title - Navy Blue #000080 */
    .report-title {
      text-align: center;
      font-size: 16pt;
      font-weight: 600;
      letter-spacing: 2px;
      margin: 25px 0;
      color: #000080;
    }
    .report-meta {
      text-align: center;
      font-size: 9pt;
      color: #333;
      margin-bottom: 25px;
    }
    .report-meta p { margin: 3px 0; display: block; }
    
    /* Sections with Grey Dividers - Navy Blue headings */
    .report-section {
      margin-bottom: 20px;
    }
    .section-divider {
      border: none;
      border-top: 1px solid #ccc;
      margin: 20px 0 15px 0;
    }
    .section-heading {
      font-size: 12pt;
      font-weight: 600;
      color: #000080;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    /* Patient Info - Label and Value on SAME LINE */
    .patient-info p {
      margin: 6px 0;
      display: block;
      font-size: 11pt;
    }
    .patient-info strong {
      font-weight: 600;
      color: #000;
    }
    .report-content p {
      margin-bottom: 8px;
      display: block;
      text-align: justify;
    }
    
    /* Assessment Items - Clear formatting */
    .assessment-item {
      margin-bottom: 18px;
      padding: 12px;
      background: #f9f9f9;
      border-left: 3px solid #000080;
      display: block;
    }
    .assessment-item strong {
      font-size: 11pt;
      color: #000080;
      display: block;
      margin-bottom: 5px;
    }
    .assessment-item em {
      font-style: normal;
      font-weight: 600;
    }
    
    /* Recommendation Items - Clear formatting */
    .recommendation-item {
      margin-bottom: 15px;
      padding: 10px 0;
      border-bottom: 1px solid #eee;
      display: block;
    }
    .recommendation-item strong {
      font-size: 11pt;
      color: #000080;
      display: block;
      margin-bottom: 5px;
    }
    
    /* Lists - Each item on NEW LINE */
    ul, ol {
      margin: 10px 0;
      padding-left: 20px;
      list-style-position: outside;
    }
    li {
      display: list-item;
      margin-bottom: 8px;
      text-align: justify;
      padding-left: 5px;
    }
    
    /* Disclaimer */
    .disclaimer-box {
      background: #f8f9fa;
      border: 1px solid #e9ecef;
      border-radius: 4px;
      padding: 12px;
      margin: 25px 0;
      font-size: 8pt;
      color: #333;
    }
    .disclaimer-box p { margin: 5px 0; text-align: justify; display: block; }
    
    /* Signature Block */
    .signature-section {
      margin-top: 40px;
    }
    .signature-space {
      height: 60px;
      border-bottom: 1px solid #000;
      width: 180px;
      margin: 15px 0 8px 0;
    }
    .signature-name {
      font-weight: 600;
      font-size: 11pt;
      margin: 5px 0 2px 0;
      color: #000;
    }
    .signature-details {
      font-size: 9pt;
      color: #333;
      margin: 2px 0;
      display: block;
    }
    
    /* Branded Footer */
    .branded-footer {
      margin-top: 40px;
      padding-top: 15px;
      border-top: 1px solid #ddd;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .footer-logo {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .footer-logo img { height: 50px; width: auto; }
  </style>
</head>
<body>
  ${reportContent}
  
  <!-- Branded Footer - Logo Only -->
  <div class="branded-footer">
    <div class="footer-logo">
      <img src="/logo-cognispace.png" alt="Cognispace" style="height: 50px;" onerror="this.outerHTML=''" />
    </div>
  </div>
</body>
</html>
    `);
    printWindow.document.close();
    
    // Wait for fonts to load then print
    setTimeout(() => {
      printWindow.focus();
      printWindow.print();
    }, 800);
  };

  const toggleAssessmentSelection = (assessmentId) => {
    setDiagnosticRequest(prev => ({
      ...prev,
      assessment_ids: prev.assessment_ids.includes(assessmentId)
        ? prev.assessment_ids.filter(id => id !== assessmentId)
        : [...prev.assessment_ids, assessmentId]
    }));
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
        <div className="flex items-center gap-3 mb-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Brain className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-4xl font-serif text-primary">TheraGenie ✨</h2>
            <p className="text-muted-foreground">Insight-Driven CI (Clinical Intelligence)</p>
          </div>
        </div>
        
        {/* Info Banner */}
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-4 mt-4">
          <div className="flex items-start gap-3">
            <Sparkles className="text-purple-500 mt-0.5 flex-shrink-0" size={20} />
            <div>
              <p className="text-sm font-medium text-purple-800 mb-1">How TheraGenie Works</p>
              <ul className="text-xs text-purple-700 space-y-1">
                <li>• Uses structured clinical data from <strong>Case History</strong>, <strong>Assessments</strong>, and <strong>Session Notes</strong></li>
                <li>• Provides <strong>decision-support suggestions</strong> for therapist reference only</li>
                <li>• <strong>All suggestions require therapist review and approval</strong></li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-6">
          <TabsTrigger value="assessments" className="flex items-center gap-2">
            <ClipboardCheck size={16} />
            <span className="hidden sm:inline">Assessments</span>
          </TabsTrigger>
          <TabsTrigger value="diagnostic" className="flex items-center gap-2">
            <FileSearch size={16} />
            <span className="hidden sm:inline">Diagnostic</span>
          </TabsTrigger>
          <TabsTrigger value="protocols" className="flex items-center gap-2">
            <BookOpen size={16} />
            <span className="hidden sm:inline">Protocols</span>
          </TabsTrigger>
          <TabsTrigger value="homework" className="flex items-center gap-2">
            <FileText size={16} />
            <span className="hidden sm:inline">Homework</span>
          </TabsTrigger>
          <TabsTrigger value="resources" className="flex items-center gap-2">
            <Library size={16} />
            <span className="hidden sm:inline">Resources</span>
          </TabsTrigger>
        </TabsList>

        {/* Assessment Suggestions Tab */}
        <TabsContent value="assessments" className="space-y-6">
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center gap-3 mb-4">
              <Sparkles className="text-purple-500" size={20} />
              <h3 className="text-lg font-semibold">Diagnostic Insight</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Get CI-powered suggestions for clinical assessments based on client data or your observations.
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
              
              {/* Data Source Checkboxes */}
              <div className="col-span-2 bg-slate-50 rounded-lg p-3 mt-2">
                <p className="text-xs font-medium text-muted-foreground mb-2">Include data from:</p>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={assessmentRequest.include_case_history}
                      onChange={(e) => setAssessmentRequest({...assessmentRequest, include_case_history: e.target.checked})}
                      className="rounded border-slate-300"
                    />
                    <span>Case History</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={assessmentRequest.include_prev_assessments}
                      onChange={(e) => setAssessmentRequest({...assessmentRequest, include_prev_assessments: e.target.checked})}
                      className="rounded border-slate-300"
                    />
                    <span>Previous Assessments</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={assessmentRequest.include_intake}
                      onChange={(e) => setAssessmentRequest({...assessmentRequest, include_intake: e.target.checked})}
                      className="rounded border-slate-300"
                    />
                    <span>Intake Notes</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={assessmentRequest.include_notes}
                      onChange={(e) => setAssessmentRequest({...assessmentRequest, include_notes: e.target.checked})}
                      className="rounded border-slate-300"
                    />
                    <span>Session Notes</span>
                  </label>
                </div>
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
                <><Sparkles className="mr-2" size={16} /> Get CI Suggestions</>
              )}
            </Button>
          </Card>

          {/* Assessment Results */}
          {assessmentSuggestions && (
            <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
              <h3 className="text-lg font-semibold mb-2">Clinical Analysis</h3>
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

        {/* CogniVision Diagnostic Reports Tab */}
        <TabsContent value="diagnostic" className="space-y-6">
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                <FileSearch className="text-white" size={20} />
              </div>
              <div>
                <h3 className="text-lg font-semibold">CogniVision Diagnostic Engine</h3>
                <p className="text-xs text-muted-foreground">Full-Scale Psychodiagnostic Evaluation Reports</p>
              </div>
            </div>
            
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 mb-4">
              <p className="text-xs text-emerald-700">
                <strong>Note:</strong> CogniVision synthesizes data from selected assessments, case history, and session notes 
                to generate comprehensive clinical reports following ICD-10/DSM-5 standards.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <Label>Select Client *</Label>
                <Select 
                  value={diagnosticRequest.client_id || undefined} 
                  onValueChange={(v) => {
                    setDiagnosticRequest({...diagnosticRequest, client_id: v, assessment_ids: []});
                    fetchClientAssessments(v);
                  }}
                >
                  <SelectTrigger data-testid="diagnostic-client-select">
                    <SelectValue placeholder="Choose a client" />
                  </SelectTrigger>
                  <SelectContent>
                    {clients.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.full_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs font-medium text-muted-foreground mb-2">Include data from:</p>
                <div className="flex flex-wrap gap-3">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={diagnosticRequest.include_case_history}
                      onChange={(e) => setDiagnosticRequest({...diagnosticRequest, include_case_history: e.target.checked})}
                      className="rounded border-slate-300"
                    />
                    <span>Case History</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={diagnosticRequest.include_intake}
                      onChange={(e) => setDiagnosticRequest({...diagnosticRequest, include_intake: e.target.checked})}
                      className="rounded border-slate-300"
                    />
                    <span>Intake Notes</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={diagnosticRequest.include_session_history}
                      onChange={(e) => setDiagnosticRequest({...diagnosticRequest, include_session_history: e.target.checked})}
                      className="rounded border-slate-300"
                    />
                    <span>Session History</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Assessment Selection */}
            {diagnosticRequest.client_id && (
              <div className="mb-4">
                <Label className="mb-2 block">Select Assessments for Report (optional)</Label>
                {completedAssessments.length === 0 ? (
                  <p className="text-sm text-muted-foreground bg-slate-50 p-3 rounded-lg">
                    No completed assessments found. You can still generate a report using clinical observations below.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto border rounded-lg p-3">
                    {completedAssessments.map(a => (
                      <label 
                        key={a.id} 
                        className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all ${
                          diagnosticRequest.assessment_ids.includes(a.id) 
                            ? 'bg-emerald-50 border border-emerald-300' 
                            : 'bg-white border border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <input 
                          type="checkbox" 
                          checked={diagnosticRequest.assessment_ids.includes(a.id)}
                          onChange={() => toggleAssessmentSelection(a.id)}
                          className="rounded border-slate-300"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{a.assessment_type}</p>
                          <p className="text-xs text-muted-foreground">Score: {a.score || 'N/A'}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
                {diagnosticRequest.assessment_ids.length > 0 && (
                  <p className="text-xs text-emerald-600 mt-2">
                    {diagnosticRequest.assessment_ids.length} assessment(s) selected
                  </p>
                )}
              </div>
            )}

            {/* Therapist Notes */}
            <div className="mb-4">
              <Label>Additional Clinical Observations or Assessment Details (optional)</Label>
              <Textarea
                placeholder="Add any offline assessment data, behavioral observations, clinical notes, or manual assessment details..."
                value={diagnosticRequest.therapist_notes}
                onChange={(e) => setDiagnosticRequest({...diagnosticRequest, therapist_notes: e.target.value})}
                rows={4}
              />
              <p className="text-xs text-muted-foreground mt-1">
                This field can be used as the sole source for report generation if no assessments are selected.
              </p>
            </div>

            <Button 
              onClick={handleGenerateDiagnosticReport} 
              disabled={loadingReport || isReadOnly || !diagnosticRequest.client_id || (diagnosticRequest.assessment_ids.length === 0 && !diagnosticRequest.therapist_notes.trim())}
              className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600"
              data-testid="generate-report-btn"
            >
              {loadingReport ? (
                <><Loader2 className="mr-2 animate-spin" size={16} /> Generating Report...</>
              ) : (
                <><FileSearch className="mr-2" size={16} /> Generate Diagnostic Report</>
              )}
            </Button>
          </Card>

          {/* Saved Reports */}
          {savedReports.length > 0 && (
            <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
              <h3 className="text-lg font-semibold mb-4">Saved Reports</h3>
              <div className="space-y-3">
                {savedReports.map(report => {
                  const client = clients.find(c => c.id === report.client_id);
                  return (
                    <div key={report.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div>
                        <p className="font-medium">{client?.full_name || 'Unknown Client'}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(report.created_at).toLocaleDateString('en-IN')} • 
                          <span className={`ml-1 px-2 py-0.5 rounded-full text-xs ${
                            report.status === 'shared' ? 'bg-green-100 text-green-700' :
                            report.status === 'approved' ? 'bg-blue-100 text-blue-700' :
                            'bg-amber-100 text-amber-700'
                          }`}>
                            {report.status}
                          </span>
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleViewReport(report)}>
                          <Eye size={14} />
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleEditReport(report)}>
                          <Edit3 size={14} />
                        </Button>
                        {report.status === 'approved' && (
                          <Button variant="outline" size="sm" onClick={() => handleShareReport(report.id)}>
                            <Share2 size={14} />
                          </Button>
                        )}
                        <Button variant="outline" size="sm" className="text-red-500" onClick={() => handleDeleteReport(report.id)}>
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </TabsContent>

        {/* Protocol Builder Tab */}
        <TabsContent value="protocols" className="space-y-6">
          <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="flex items-center gap-3 mb-4">
              <BookOpen className="text-blue-500" size={20} />
              <h3 className="text-lg font-semibold">Precision Protocol Engine</h3>
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
                    <SelectValue placeholder="Auto-select best fit" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto-select best fit</SelectItem>
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

            {/* Data Source Checkboxes for Protocol */}
            <div className="bg-slate-50 rounded-lg p-3 mb-4">
              <p className="text-xs font-medium text-muted-foreground mb-2">Include data from:</p>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={protocolRequest.include_case_history}
                    onChange={(e) => setProtocolRequest({...protocolRequest, include_case_history: e.target.checked})}
                    className="rounded border-slate-300"
                  />
                  <span>Case History</span>
                </label>
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={protocolRequest.include_prev_assessments}
                    onChange={(e) => setProtocolRequest({...protocolRequest, include_prev_assessments: e.target.checked})}
                    className="rounded border-slate-300"
                  />
                  <span>Previous Assessments</span>
                </label>
              </div>
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
              <h3 className="text-lg font-semibold">CI Homework Generator</h3>
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

            {/* Data Source Checkboxes for Homework */}
            <div className="bg-slate-50 rounded-lg p-3 mb-4">
              <p className="text-xs font-medium text-muted-foreground mb-2">Include data from:</p>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={homeworkRequest.include_case_history}
                    onChange={(e) => setHomeworkRequest({...homeworkRequest, include_case_history: e.target.checked})}
                    className="rounded border-slate-300"
                  />
                  <span>Case History</span>
                </label>
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={homeworkRequest.include_prev_assessments}
                    onChange={(e) => setHomeworkRequest({...homeworkRequest, include_prev_assessments: e.target.checked})}
                    className="rounded border-slate-300"
                  />
                  <span>Previous Assessments</span>
                </label>
              </div>
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

      {/* CogniVision Report Editor Dialog */}
      <Dialog open={showReportEditor} onOpenChange={setShowReportEditor}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileSearch className="text-teal-700" size={20} />
              CogniVision Diagnostic Report Editor
            </DialogTitle>
          </DialogHeader>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-2">
            <p className="text-xs text-amber-700">
              <strong>Review Required:</strong> Edit the report as needed. All content requires your approval before sharing with the client.
            </p>
          </div>

          {/* Editor Toolbar - Sticky at top */}
          {!isReadOnly && (
            <div className="sticky top-0 z-10 flex items-center gap-1 p-2 bg-gray-100 border border-gray-300 rounded-lg mb-2">
              <button
                type="button"
                onClick={() => document.execCommand('bold')}
                className="p-2 hover:bg-gray-200 rounded font-bold"
                title="Bold"
              >
                B
              </button>
              <button
                type="button"
                onClick={() => document.execCommand('italic')}
                className="p-2 hover:bg-gray-200 rounded italic"
                title="Italic"
              >
                I
              </button>
              <button
                type="button"
                onClick={() => document.execCommand('underline')}
                className="p-2 hover:bg-gray-200 rounded underline"
                title="Underline"
              >
                U
              </button>
              <div className="w-px h-6 bg-gray-300 mx-1"></div>
              <button
                type="button"
                onClick={() => document.execCommand('insertUnorderedList')}
                className="p-2 hover:bg-gray-200 rounded text-sm"
                title="Bullet List"
              >
                • List
              </button>
              <button
                type="button"
                onClick={() => document.execCommand('insertOrderedList')}
                className="p-2 hover:bg-gray-200 rounded text-sm"
                title="Numbered List"
              >
                1. List
              </button>
              <div className="w-px h-6 bg-gray-300 mx-1"></div>
              <button
                type="button"
                onClick={() => document.execCommand('undo')}
                className="p-2 hover:bg-gray-200 rounded text-sm"
                title="Undo"
              >
                ↩
              </button>
              <button
                type="button"
                onClick={() => document.execCommand('redo')}
                className="p-2 hover:bg-gray-200 rounded text-sm"
                title="Redo"
              >
                ↪
              </button>
              <div className="ml-auto text-xs text-gray-500">
                Click inside report to edit
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto">
            {/* Report Preview with Clinical CSS - Navy Blue */}
            <style>{`
              .clinical-report { font-family: 'Inter', Arial, sans-serif; color: #000; line-height: 1.6; }
              .therapist-header { margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #000080; }
              .therapist-header h1 { font-size: 18pt; margin: 0 0 5px 0; color: #000080; font-weight: 700; }
              .therapist-header p { margin: 3px 0; font-size: 10pt; color: #333; display: block; }
              .report-title { text-align: center; font-size: 16pt; font-weight: 600; letter-spacing: 2px; margin: 20px 0; color: #000080; }
              .report-meta { text-align: center; font-size: 9pt; color: #333; margin-bottom: 20px; }
              .report-meta p { margin: 3px 0; display: block; }
              .section-divider { border: none; border-top: 1px solid #ccc; margin: 20px 0 15px 0; }
              .report-section { margin-bottom: 18px; }
              .section-heading { font-size: 12pt; font-weight: 600; color: #000080; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
              .patient-info p { margin: 6px 0; display: block; font-size: 11pt; }
              .patient-info strong { font-weight: 600; color: #000; }
              .report-content p { margin-bottom: 8px; display: block; text-align: justify; }
              .assessment-item { margin-bottom: 18px; padding: 12px; background: #f9f9f9; border-left: 3px solid #000080; display: block; }
              .assessment-item strong { font-size: 11pt; color: #000080; display: block; margin-bottom: 5px; }
              .assessment-item em { font-style: normal; font-weight: 600; }
              .recommendation-item { margin-bottom: 15px; padding: 10px 0; border-bottom: 1px solid #eee; display: block; }
              .recommendation-item strong { font-size: 11pt; color: #000080; display: block; margin-bottom: 5px; }
              ul, ol { margin: 10px 0; padding-left: 20px; }
              li { display: list-item; margin-bottom: 6px; text-align: justify; }
              .disclaimer-box { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 12px; margin: 20px 0; font-size: 8pt; color: #333; }
              .disclaimer-box p { margin: 5px 0; text-align: justify; display: block; }
              .signature-section { margin-top: 30px; }
              .signature-space { height: 60px; border-bottom: 1px solid #000; width: 180px; margin: 15px 0 8px 0; }
              .signature-name { font-weight: 600; font-size: 11pt; margin: 5px 0 2px 0; color: #000; }
              .signature-details { font-size: 9pt; color: #333; margin: 2px 0; display: block; }
            `}</style>

            {/* Editor Toolbar */}
            {!isReadOnly && (
              <div className="flex items-center gap-1 p-2 bg-gray-100 rounded-t-lg border border-b-0 border-gray-300">
                <button
                  type="button"
                  onClick={() => document.execCommand('bold')}
                  className="p-2 hover:bg-gray-200 rounded font-bold"
                  title="Bold"
                >
                  B
                </button>
                <button
                  type="button"
                  onClick={() => document.execCommand('italic')}
                  className="p-2 hover:bg-gray-200 rounded italic"
                  title="Italic"
                >
                  I
                </button>
                <button
                  type="button"
                  onClick={() => document.execCommand('underline')}
                  className="p-2 hover:bg-gray-200 rounded underline"
                  title="Underline"
                >
                  U
                </button>
                <div className="w-px h-6 bg-gray-300 mx-1"></div>
                <button
                  type="button"
                  onClick={() => document.execCommand('insertUnorderedList')}
                  className="p-2 hover:bg-gray-200 rounded text-sm"
                  title="Bullet List"
                >
                  • List
                </button>
                <button
                  type="button"
                  onClick={() => document.execCommand('insertOrderedList')}
                  className="p-2 hover:bg-gray-200 rounded text-sm"
                  title="Numbered List"
                >
                  1. List
                </button>
                <div className="w-px h-6 bg-gray-300 mx-1"></div>
                <button
                  type="button"
                  onClick={() => document.execCommand('justifyLeft')}
                  className="p-2 hover:bg-gray-200 rounded text-sm"
                  title="Align Left"
                >
                  ≡
                </button>
                <button
                  type="button"
                  onClick={() => document.execCommand('justifyCenter')}
                  className="p-2 hover:bg-gray-200 rounded text-sm"
                  title="Align Center"
                >
                  ≡
                </button>
                <button
                  type="button"
                  onClick={() => document.execCommand('justifyRight')}
                  className="p-2 hover:bg-gray-200 rounded text-sm"
                  title="Align Right"
                >
                  ≡
                </button>
                <div className="w-px h-6 bg-gray-300 mx-1"></div>
                <button
                  type="button"
                  onClick={() => document.execCommand('undo')}
                  className="p-2 hover:bg-gray-200 rounded text-sm"
                  title="Undo"
                >
                  ↩
                </button>
                <button
                  type="button"
                  onClick={() => document.execCommand('redo')}
                  className="p-2 hover:bg-gray-200 rounded text-sm"
                  title="Redo"
                >
                  ↪
                </button>
                <div className="ml-auto text-xs text-gray-500">
                  Click inside report to edit • Changes auto-save on blur
                </div>
              </div>
            )}

            <div 
              ref={reportEditorRef}
              className={`min-h-[400px] border rounded-lg p-6 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 ${!isReadOnly ? 'rounded-t-none' : ''}`}
              contentEditable={!isReadOnly}
              dangerouslySetInnerHTML={{ __html: editableReport }}
              onBlur={(e) => setEditableReport(e.currentTarget.innerHTML)}
              onInput={(e) => setEditableReport(e.currentTarget.innerHTML)}
            />
          </div>

          <DialogFooter className="flex justify-between items-center pt-4 border-t">
            <div className="flex gap-2">
              <Button variant="outline" onClick={handlePrintReport}>
                <Printer size={16} className="mr-2" /> Print / PDF
              </Button>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowReportEditor(false)}>
                Cancel
              </Button>
              <Button variant="outline" onClick={() => handleSaveReport('draft')}>
                <Save size={16} className="mr-2" /> Save Draft
              </Button>
              <Button 
                onClick={handleApproveReport}
                className="bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600"
              >
                <CheckCircle2 size={16} className="mr-2" /> Approve Report
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Report Preview Dialog */}
      <Dialog open={showReportPreview} onOpenChange={setShowReportPreview}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Diagnostic Report Preview</DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto">
            {previewReport && (
              <div 
                className="prose prose-sm max-w-none p-6 bg-white border rounded-lg"
                dangerouslySetInnerHTML={{ __html: previewReport.report_content }}
              />
            )}
          </div>

          <DialogFooter className="pt-4 border-t">
            <Button variant="outline" onClick={handlePrintReport}>
              <Printer size={16} className="mr-2" /> Print / PDF
            </Button>
            <Button variant="outline" onClick={() => setShowReportPreview(false)}>
              Close
            </Button>
            {previewReport?.status === 'approved' && (
              <Button onClick={() => handleShareReport(previewReport.id)}>
                <Share2 size={16} className="mr-2" /> Share with Client
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AIClinicalSupport;
