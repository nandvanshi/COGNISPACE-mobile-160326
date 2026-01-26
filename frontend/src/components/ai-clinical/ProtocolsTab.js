import React from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { BookOpen, Sparkles, Loader2 } from 'lucide-react';

const ProtocolsTab = ({
  clients,
  protocolRequest,
  setProtocolRequest,
  loadingProtocol,
  handleGenerateProtocol,
  isReadOnly
}) => {
  return (
    <div className="space-y-6">
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
    </div>
  );
};

export default ProtocolsTab;
