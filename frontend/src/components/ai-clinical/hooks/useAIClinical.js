import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { toast } from 'sonner';

/**
 * Custom hook for all AI Clinical Support functionality
 * Manages state and API calls for assessments, protocols, homework, diagnostics, and resources
 */
export const useAIClinical = () => {
  // Shared State
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const reportEditorRef = useRef(null);

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

  // Resources State
  const [resources, setResources] = useState([]);
  const [showResourceDialog, setShowResourceDialog] = useState(false);
  const [newResource, setNewResource] = useState({
    title: '',
    category: 'worksheet',
    content: '',
    tags: []
  });

  // ============= FETCH FUNCTIONS =============
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
    
    printWindow.document.write(`
<!DOCTYPE html>
<html>
<head>
  <title>Psychodiagnostic Evaluation Report</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    @media print {
      @page { margin: 2cm; size: A4; }
      html, body { margin: 0 !important; padding: 0 !important; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      .no-print { display: none !important; }
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; font-size: 11pt; color: #000; line-height: 1.6; background: #fff; padding: 0; }
    .clinical-report { max-width: 210mm; margin: 0 auto; padding: 0; }
    .therapist-header { margin-bottom: 25px; padding-bottom: 15px; border-bottom: 2px solid #000080; }
    .therapist-header h1 { font-size: 18pt; font-weight: 700; margin: 0 0 5px 0; color: #000080; }
    .therapist-header p { margin: 3px 0; font-size: 10pt; color: #333; display: block; }
    .report-title { text-align: center; font-size: 16pt; font-weight: 600; letter-spacing: 2px; margin: 25px 0; color: #000080; }
    .report-meta { text-align: center; font-size: 9pt; color: #333; margin-bottom: 25px; }
    .report-meta p { margin: 3px 0; display: block; }
    .report-section { margin-bottom: 20px; }
    .section-divider { border: none; border-top: 1px solid #ccc; margin: 20px 0 15px 0; }
    .section-heading { font-size: 12pt; font-weight: 600; color: #000080; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
    .patient-info p { margin: 6px 0; display: block; font-size: 11pt; }
    .patient-info strong { font-weight: 600; color: #000; }
    .report-content p { margin-bottom: 8px; display: block; text-align: justify; }
    .assessment-item { margin-bottom: 18px; padding: 12px; background: #f9f9f9; border-left: 3px solid #000080; display: block; }
    .assessment-item strong { font-size: 11pt; color: #000080; display: block; margin-bottom: 5px; }
    .assessment-item em { font-style: normal; font-weight: 600; }
    .recommendation-item { margin-bottom: 15px; padding: 10px 0; border-bottom: 1px solid #eee; display: block; }
    .recommendation-item strong { font-size: 11pt; color: #000080; display: block; margin-bottom: 5px; }
    ul, ol { margin: 10px 0; padding-left: 20px; list-style-position: outside; }
    li { display: list-item; margin-bottom: 8px; text-align: justify; padding-left: 5px; }
    .disclaimer-box { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 12px; margin: 25px 0; font-size: 8pt; color: #333; }
    .disclaimer-box p { margin: 5px 0; text-align: justify; display: block; }
    .signature-section { margin-top: 40px; }
    .signature-space { height: 60px; border-bottom: 1px solid #000; width: 180px; margin: 15px 0 8px 0; }
    .signature-name { font-weight: 600; font-size: 11pt; margin: 5px 0 2px 0; color: #000; }
    .signature-details { font-size: 9pt; color: #333; margin: 2px 0; display: block; }
    .branded-footer { margin-top: 40px; padding-top: 15px; border-top: 1px solid #ddd; display: flex; justify-content: center; align-items: center; }
    .footer-logo { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .footer-logo span { font-size: 10pt; color: #666; margin-bottom: 5px; }
    .footer-logo img { height: 100px; width: auto; }
  </style>
</head>
<body>
  ${reportContent}
  <div class="branded-footer">
    <div class="footer-logo">
      <span>Powered by</span>
      <img src="/logo-cognispace.png" alt="Cognispace" style="height: 100px;" onerror="this.outerHTML=''" />
    </div>
  </div>
</body>
</html>
    `);
    printWindow.document.close();
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

  // ============= UTILITY FUNCTIONS =============
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-error/10 text-error border-error/30';
      case 'medium': return 'bg-warning/10 text-warning border-warning/30';
      case 'low': return 'bg-info/10 text-info border-info/30';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  return {
    // Shared
    clients,
    loading,
    reportEditorRef,
    getPriorityColor,

    // Assessment
    assessmentRequest,
    setAssessmentRequest,
    assessmentSuggestions,
    loadingAssessment,
    handleSuggestAssessments,

    // Protocol
    protocolRequest,
    setProtocolRequest,
    generatedProtocol,
    loadingProtocol,
    showProtocolDialog,
    setShowProtocolDialog,
    handleGenerateProtocol,
    handleSaveProtocol,

    // Homework
    homeworkRequest,
    setHomeworkRequest,
    generatedHomework,
    loadingHomework,
    showHomeworkDialog,
    setShowHomeworkDialog,
    handleGenerateHomework,
    handleAssignHomework,

    // Diagnostic
    diagnosticRequest,
    setDiagnosticRequest,
    completedAssessments,
    generatedReport,
    loadingReport,
    savedReports,
    showReportEditor,
    setShowReportEditor,
    editableReport,
    setEditableReport,
    currentReportId,
    showReportPreview,
    setShowReportPreview,
    previewReport,
    fetchClientAssessments,
    handleGenerateDiagnosticReport,
    handleSaveReport,
    handleApproveReport,
    handleShareReport,
    handleDeleteReport,
    handleViewReport,
    handleEditReport,
    handlePrintReport,
    toggleAssessmentSelection,

    // Resources
    resources,
    showResourceDialog,
    setShowResourceDialog,
    newResource,
    setNewResource,
    handleCreateResource,
    handleAssignResource,
  };
};

export default useAIClinical;
