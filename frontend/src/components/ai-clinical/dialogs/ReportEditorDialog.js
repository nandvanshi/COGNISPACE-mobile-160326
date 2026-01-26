import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { FileSearch, Printer, Save, CheckCircle2 } from 'lucide-react';

const REPORT_STYLES = `
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
`;

const ReportEditorDialog = ({
  open,
  onOpenChange,
  editableReport,
  setEditableReport,
  reportEditorRef,
  handlePrintReport,
  handleSaveReport,
  handleApproveReport,
  isReadOnly
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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

        {/* Editor Toolbar */}
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
          <style>{REPORT_STYLES}</style>
          <div 
            ref={reportEditorRef}
            className="min-h-[400px] border rounded-lg p-6 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
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
            <Button variant="outline" onClick={() => onOpenChange(false)}>
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
  );
};

export default ReportEditorDialog;
