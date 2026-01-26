import React from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Sparkles, Loader2 } from 'lucide-react';

const AssessmentsTab = ({
  clients,
  assessmentRequest,
  setAssessmentRequest,
  assessmentSuggestions,
  loadingAssessment,
  handleSuggestAssessments,
  getPriorityColor,
  isReadOnly
}) => {
  return (
    <div className="space-y-6">
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
    </div>
  );
};

export default AssessmentsTab;
