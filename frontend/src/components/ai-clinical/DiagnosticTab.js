import React from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { FileSearch, Loader2, Eye, Edit3, Share2, Trash2 } from 'lucide-react';

const DiagnosticTab = ({
  clients,
  diagnosticRequest,
  setDiagnosticRequest,
  completedAssessments,
  loadingReport,
  savedReports,
  fetchClientAssessments,
  handleGenerateDiagnosticReport,
  handleViewReport,
  handleEditReport,
  handleShareReport,
  handleDeleteReport,
  toggleAssessmentSelection,
  isReadOnly
}) => {
  return (
    <div className="space-y-6">
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
                      {(() => {
                        const d = new Date(report.created_at);
                        return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`;
                      })()} • 
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
    </div>
  );
};

export default DiagnosticTab;
