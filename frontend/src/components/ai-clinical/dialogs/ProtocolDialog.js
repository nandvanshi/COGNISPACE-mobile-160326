import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Label } from '../../ui/label';
import { Card } from '../../ui/card';
import { BookOpen, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

const ProtocolDialog = ({
  open,
  onOpenChange,
  generatedProtocol,
  protocolRequest,
  handleSaveProtocol,
  isReadOnly
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
              <Button variant="outline" onClick={() => onOpenChange(false)}>
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
  );
};

export default ProtocolDialog;
