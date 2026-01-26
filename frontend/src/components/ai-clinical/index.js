import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Brain, ClipboardCheck, BookOpen, FileText, FileSearch, Library, Sparkles } from 'lucide-react';

// Hook
import { useAIClinical } from './hooks/useAIClinical';

// Tab Components
import AssessmentsTab from './AssessmentsTab';
import DiagnosticTab from './DiagnosticTab';
import ProtocolsTab from './ProtocolsTab';
import HomeworkTab from './HomeworkTab';
import ResourcesTab from './ResourcesTab';

// Dialog Components
import ProtocolDialog from './dialogs/ProtocolDialog';
import HomeworkDialog from './dialogs/HomeworkDialog';
import ResourceDialog from './dialogs/ResourceDialog';
import ReportEditorDialog from './dialogs/ReportEditorDialog';
import ReportPreviewDialog from './dialogs/ReportPreviewDialog';

const AIClinicalSupport = ({ isReadOnly = false }) => {
  const [activeTab, setActiveTab] = useState('assessments');
  
  const {
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
    loadingReport,
    savedReports,
    showReportEditor,
    setShowReportEditor,
    editableReport,
    setEditableReport,
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
  } = useAIClinical();

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

        {/* Tab Contents */}
        <TabsContent value="assessments">
          <AssessmentsTab
            clients={clients}
            assessmentRequest={assessmentRequest}
            setAssessmentRequest={setAssessmentRequest}
            assessmentSuggestions={assessmentSuggestions}
            loadingAssessment={loadingAssessment}
            handleSuggestAssessments={handleSuggestAssessments}
            getPriorityColor={getPriorityColor}
            isReadOnly={isReadOnly}
          />
        </TabsContent>

        <TabsContent value="diagnostic">
          <DiagnosticTab
            clients={clients}
            diagnosticRequest={diagnosticRequest}
            setDiagnosticRequest={setDiagnosticRequest}
            completedAssessments={completedAssessments}
            loadingReport={loadingReport}
            savedReports={savedReports}
            fetchClientAssessments={fetchClientAssessments}
            handleGenerateDiagnosticReport={handleGenerateDiagnosticReport}
            handleViewReport={handleViewReport}
            handleEditReport={handleEditReport}
            handleShareReport={handleShareReport}
            handleDeleteReport={handleDeleteReport}
            toggleAssessmentSelection={toggleAssessmentSelection}
            isReadOnly={isReadOnly}
          />
        </TabsContent>

        <TabsContent value="protocols">
          <ProtocolsTab
            clients={clients}
            protocolRequest={protocolRequest}
            setProtocolRequest={setProtocolRequest}
            loadingProtocol={loadingProtocol}
            handleGenerateProtocol={handleGenerateProtocol}
            isReadOnly={isReadOnly}
          />
        </TabsContent>

        <TabsContent value="homework">
          <HomeworkTab
            clients={clients}
            homeworkRequest={homeworkRequest}
            setHomeworkRequest={setHomeworkRequest}
            loadingHomework={loadingHomework}
            handleGenerateHomework={handleGenerateHomework}
            isReadOnly={isReadOnly}
          />
        </TabsContent>

        <TabsContent value="resources">
          <ResourcesTab
            clients={clients}
            resources={resources}
            setShowResourceDialog={setShowResourceDialog}
            handleAssignResource={handleAssignResource}
            isReadOnly={isReadOnly}
          />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <ProtocolDialog
        open={showProtocolDialog}
        onOpenChange={setShowProtocolDialog}
        generatedProtocol={generatedProtocol}
        protocolRequest={protocolRequest}
        handleSaveProtocol={handleSaveProtocol}
        isReadOnly={isReadOnly}
      />

      <HomeworkDialog
        open={showHomeworkDialog}
        onOpenChange={setShowHomeworkDialog}
        generatedHomework={generatedHomework}
        handleAssignHomework={handleAssignHomework}
        isReadOnly={isReadOnly}
      />

      <ResourceDialog
        open={showResourceDialog}
        onOpenChange={setShowResourceDialog}
        newResource={newResource}
        setNewResource={setNewResource}
        handleCreateResource={handleCreateResource}
      />

      <ReportEditorDialog
        open={showReportEditor}
        onOpenChange={setShowReportEditor}
        editableReport={editableReport}
        setEditableReport={setEditableReport}
        reportEditorRef={reportEditorRef}
        handlePrintReport={handlePrintReport}
        handleSaveReport={handleSaveReport}
        handleApproveReport={handleApproveReport}
        isReadOnly={isReadOnly}
      />

      <ReportPreviewDialog
        open={showReportPreview}
        onOpenChange={setShowReportPreview}
        previewReport={previewReport}
        handlePrintReport={handlePrintReport}
        handleShareReport={handleShareReport}
      />
    </div>
  );
};

export default AIClinicalSupport;
