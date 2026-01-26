import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Printer, Share2 } from 'lucide-react';

const ReportPreviewDialog = ({
  open,
  onOpenChange,
  previewReport,
  handlePrintReport,
  handleShareReport
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
          <Button variant="outline" onClick={() => onOpenChange(false)}>
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
  );
};

export default ReportPreviewDialog;
