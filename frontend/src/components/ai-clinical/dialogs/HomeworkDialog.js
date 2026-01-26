import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Label } from '../../ui/label';
import { Card } from '../../ui/card';
import { FileText, Clock, Send } from 'lucide-react';

const HomeworkDialog = ({
  open,
  onOpenChange,
  generatedHomework,
  handleAssignHomework,
  isReadOnly
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
              <Button variant="outline" onClick={() => onOpenChange(false)}>
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
  );
};

export default HomeworkDialog;
