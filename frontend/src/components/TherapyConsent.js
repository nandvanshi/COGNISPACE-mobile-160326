import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { 
  FileCheck, 
  Pen, 
  Check, 
  Clock, 
  AlertTriangle,
  Printer,
  Download,
  FileText,
  Loader2
} from 'lucide-react';
import { formatDate, formatTime } from '../utils/formatUtils';

const TherapyConsent = ({ clientId, clientName, isOpen, onClose, isReadOnly = false, userRole = 'therapist' }) => {
  const [consent, setConsent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [showSignatureConfirm, setShowSignatureConfirm] = useState(false);
  const [signatureMethod, setSignatureMethod] = useState(null);

  useEffect(() => {
    if (isOpen && clientId) {
      fetchConsent();
    }
  }, [isOpen, clientId]);

  const fetchConsent = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/therapy-consent/${clientId}`);
      setConsent(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        setConsent(null);
      } else {
        toast.error('Failed to load consent');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSign = async (method) => {
    setSigning(true);
    try {
      await axios.post(`${API}/therapy-consent/${clientId}/sign?signature_method=${method}`);
      toast.success(`Consent signed successfully (${method === 'digital' ? 'Digital Signature' : 'Paper Signed'})`);
      fetchConsent();
      setShowSignatureConfirm(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sign consent');
    } finally {
      setSigning(false);
    }
  };

  const handlePrint = () => {
    const printContent = consent?.consent_text || '';
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Therapy Consent - ${clientName}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; line-height: 1.6; }
            h1 { text-align: center; margin-bottom: 30px; }
            .signature-line { margin-top: 50px; border-top: 1px solid #000; width: 300px; padding-top: 5px; }
          </style>
        </head>
        <body>
          <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">${printContent}</pre>
          <div class="signature-line">Client Signature</div>
          <div class="signature-line">Date</div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileCheck className="text-primary" size={24} />
            Therapy Consent Form
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : !consent ? (
          <div className="text-center py-12">
            <AlertTriangle className="mx-auto text-amber-500 mb-4" size={48} />
            <h3 className="text-lg font-medium mb-2">Consent Not Found</h3>
            <p className="text-muted-foreground">
              Case history must be completed first to generate the consent form.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status Banner */}
            <div className={`p-4 rounded-lg border ${
              consent.is_signed 
                ? 'bg-green-50 border-green-200' 
                : 'bg-amber-50 border-amber-200'
            }`}>
              <div className="flex items-center gap-3">
                {consent.is_signed ? (
                  <>
                    <Check className="text-green-600" size={24} />
                    <div>
                      <p className="font-medium text-green-800">Consent Signed</p>
                      <p className="text-sm text-green-700">
                        Signed via {consent.signature_method === 'digital' ? 'Digital Signature' : 'Paper (Offline)'} on{' '}
                        {formatDate(consent.signed_at)} at {formatTime(consent.signed_at)}
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <Clock className="text-amber-600" size={24} />
                    <div>
                      <p className="font-medium text-amber-800">Awaiting Signature</p>
                      <p className="text-sm text-amber-700">
                        Client must sign this consent before therapy sessions can begin.
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Consent Details */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Client:</span>
                <span className="ml-2 font-medium">{consent.client_name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Therapist:</span>
                <span className="ml-2 font-medium">{consent.therapist_name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Version:</span>
                <span className="ml-2">{consent.consent_text_version}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Generated:</span>
                <span className="ml-2">{formatDate(consent.created_at)}</span>
              </div>
            </div>

            {/* Consent Text */}
            <Card className="p-4 bg-muted/30 max-h-[400px] overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-sans">
                {consent.consent_text}
              </pre>
            </Card>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t">
              <div className="flex gap-2">
                <Button variant="outline" onClick={handlePrint}>
                  <Printer size={16} className="mr-2" /> Print
                </Button>
              </div>

              {!consent.is_signed && !isReadOnly && (
                <div className="flex gap-2">
                  {userRole === 'client' ? (
                    <Button 
                      onClick={() => handleSign('digital')}
                      disabled={signing}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      {signing ? (
                        <Loader2 className="animate-spin mr-2" size={16} />
                      ) : (
                        <Pen size={16} className="mr-2" />
                      )}
                      Sign Digitally
                    </Button>
                  ) : (
                    <>
                      <Button 
                        variant="outline"
                        onClick={() => {
                          setSignatureMethod('paper');
                          setShowSignatureConfirm(true);
                        }}
                        disabled={signing}
                      >
                        <FileText size={16} className="mr-2" /> Mark as Signed (Paper)
                      </Button>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Signature Confirmation Dialog */}
        <Dialog open={showSignatureConfirm} onOpenChange={setShowSignatureConfirm}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Confirm Paper Signature</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-muted-foreground">
                Please confirm that the client has signed the consent form on paper.
              </p>
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800">
                  <AlertTriangle className="inline mr-2" size={14} />
                  By marking this as signed, you confirm that:
                </p>
                <ul className="text-sm text-amber-700 mt-2 list-disc pl-5">
                  <li>The consent form was printed and given to the client</li>
                  <li>The client has physically signed the document</li>
                  <li>You have retained the signed copy for records</li>
                </ul>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowSignatureConfirm(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={() => handleSign('paper')}
                  disabled={signing}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {signing ? <Loader2 className="animate-spin mr-2" size={16} /> : <Check size={16} className="mr-2" />}
                  Confirm Signature
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </DialogContent>
    </Dialog>
  );
};

export default TherapyConsent;
