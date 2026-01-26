import React from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { FileText, Sparkles, Loader2 } from 'lucide-react';

const HomeworkTab = ({
  clients,
  homeworkRequest,
  setHomeworkRequest,
  loadingHomework,
  handleGenerateHomework,
  isReadOnly
}) => {
  return (
    <div className="space-y-6">
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
    </div>
  );
};

export default HomeworkTab;
