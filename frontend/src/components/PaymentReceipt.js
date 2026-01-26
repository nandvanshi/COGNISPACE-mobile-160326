import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Receipt, Printer, Download, X, CheckCircle, 
  Clock, User, CreditCard, Calendar, FileText, Loader2
} from 'lucide-react';
import { formatCurrency } from '../utils/formatUtils';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

// Helper to safely extract error message
const getErrorMessage = (error, fallback = 'An error occurred') => {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) return detail[0]?.msg || fallback;
  if (typeof detail === 'object' && detail?.msg) return detail.msg;
  return fallback;
};

// Receipt View Component
export const PaymentReceiptView = ({ paymentId, isOpen, onClose }) => {
  const [receipt, setReceipt] = useState(null);
  const [loading, setLoading] = useState(true);
  const receiptRef = useRef(null);

  useEffect(() => {
    if (isOpen && paymentId) {
      fetchReceipt();
    }
  }, [isOpen, paymentId]);

  const fetchReceipt = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/payments/${paymentId}/receipt`);
      setReceipt(response.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to load receipt'));
    } finally {
      setLoading(false);
    }
  };

  const generateReceiptHTML = () => {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Payment Receipt - ${receipt?.bill_number}</title>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            padding: 20px;
            max-width: 400px;
            margin: 0 auto;
          }
          .receipt { 
            border: 2px solid #333; 
            padding: 20px;
            border-radius: 8px;
          }
          .header { 
            text-align: center; 
            border-bottom: 2px dashed #ccc; 
            padding-bottom: 15px; 
            margin-bottom: 15px;
          }
          .clinic-name { 
            font-size: 20px; 
            font-weight: bold; 
            color: #333;
          }
          .bill-number {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
          }
          .section { 
            margin: 15px 0;
            padding: 10px 0;
            border-bottom: 1px dashed #eee;
          }
          .row { 
            display: flex; 
            justify-content: space-between; 
            margin: 8px 0;
            font-size: 14px;
          }
          .label { color: #666; }
          .value { font-weight: 500; }
          .amount-section {
            text-align: center;
            padding: 20px 0;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 15px 0;
          }
          .amount { 
            font-size: 32px; 
            font-weight: bold; 
            color: #2563eb;
          }
          .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-top: 8px;
          }
          .status-paid { background: #dcfce7; color: #166534; }
          .status-partial { background: #fef3c7; color: #92400e; }
          .status-pending { background: #fee2e2; color: #991b1b; }
          .footer { 
            text-align: center; 
            font-size: 11px; 
            color: #999; 
            margin-top: 20px;
            padding-top: 15px;
            border-top: 2px dashed #ccc;
          }
          @media print {
            body { padding: 0; }
            .receipt { border: none; }
          }
        </style>
      </head>
      <body>
        <div class="receipt">
          <div class="header">
            <div class="clinic-name">${receipt?.clinic_name || 'Therapy Practice'}</div>
            <div class="bill-number">Receipt No: ${receipt?.bill_number}</div>
          </div>
          
          <div class="section">
            <div class="row">
              <span class="label">Therapist:</span>
              <span class="value">${receipt?.therapist_name || 'N/A'}</span>
            </div>
            ${receipt?.therapist_mobile ? `<div class="row"><span class="label">Phone:</span><span class="value">${receipt.therapist_mobile}</span></div>` : ''}
            ${receipt?.therapist_email ? `<div class="row"><span class="label">Email:</span><span class="value" style="font-size:12px">${receipt.therapist_email}</span></div>` : ''}
            ${receipt?.clinic_address ? `<div class="row"><span class="label">Address:</span><span class="value" style="font-size:12px;text-align:right;max-width:200px">${receipt.clinic_address}</span></div>` : ''}
          </div>

          <div class="section">
            <div class="row">
              <span class="label">Client:</span>
              <span class="value">${receipt?.client_name || 'N/A'}</span>
            </div>
            <div class="row">
              <span class="label">Client ID:</span>
              <span class="value">${receipt?.client_code || 'N/A'}</span>
            </div>
          </div>

          <div class="section">
            <div class="row">
              <span class="label">Date:</span>
              <span class="value">${receipt?.date || 'N/A'}</span>
            </div>
            <div class="row">
              <span class="label">Time:</span>
              <span class="value">${receipt?.time || 'N/A'}</span>
            </div>
            ${receipt?.session_date ? `
            <div class="row">
              <span class="label">Session Date:</span>
              <span class="value">${receipt.session_date} at ${receipt.session_time}</span>
            </div>
            ` : ''}
          </div>

          <div class="amount-section">
            <div class="amount">₹${receipt?.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '0.00'}</div>
            <span class="status status-${receipt?.payment_status?.toLowerCase() || 'paid'}">${receipt?.payment_status || 'PAID'}</span>
          </div>

          <div class="section">
            <div class="row">
              <span class="label">Payment Method:</span>
              <span class="value">${receipt?.payment_method || 'CASH'}</span>
            </div>
            ${receipt?.notes ? `<div class="row"><span class="label">Notes:</span><span class="value">${receipt.notes}</span></div>` : ''}
          </div>

          <div class="footer">
            <p>Thank you for your payment!</p>
            <p>This is a computer generated receipt.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  };

  const handlePrint = () => {
    if (!receipt) return;
    
    const receiptHTML = generateReceiptHTML();
    
    // Create a hidden iframe for printing
    const iframe = document.createElement('iframe');
    iframe.style.position = 'absolute';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = 'none';
    iframe.style.left = '-9999px';
    document.body.appendChild(iframe);
    
    const iframeDoc = iframe.contentWindow || iframe.contentDocument;
    const doc = iframeDoc.document || iframeDoc;
    
    doc.open();
    doc.write(receiptHTML);
    doc.close();
    
    // Wait for content to load then print
    iframe.onload = () => {
      try {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      } catch (e) {
        console.error('Print failed:', e);
        toast.error('Print failed. Please try downloading instead.');
      }
      // Remove iframe after printing
      setTimeout(() => {
        document.body.removeChild(iframe);
      }, 1000);
    };
  };

  const handleDownloadPDF = async () => {
    if (!receipt || !receiptRef.current) return;
    
    try {
      toast.info('Generating PDF...');
      
      // Create a temporary container with receipt content for PDF generation
      const tempContainer = document.createElement('div');
      tempContainer.style.position = 'absolute';
      tempContainer.style.left = '-9999px';
      tempContainer.style.top = '0';
      tempContainer.style.width = '380px';
      tempContainer.style.padding = '20px';
      tempContainer.style.backgroundColor = 'white';
      tempContainer.innerHTML = generateReceiptHTML();
      document.body.appendChild(tempContainer);
      
      // Wait for content to render
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Generate canvas from the temporary container
      const canvas = await html2canvas(tempContainer, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false
      });
      
      // Remove temporary container
      document.body.removeChild(tempContainer);
      
      // Create PDF
      const imgWidth = 190;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgData = canvas.toDataURL('image/png');
      
      // Add image to PDF with some margin
      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
      
      // Save the PDF
      pdf.save(`Receipt-${receipt.bill_number}.pdf`);
      
      toast.success('Receipt downloaded successfully!');
    } catch (error) {
      console.error('PDF generation error:', error);
      toast.error('Failed to generate PDF. Please try again.');
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Receipt size={20} /> Payment Receipt
          </DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : receipt ? (
          <div ref={receiptRef}>
            {/* Receipt Header */}
            <div className="text-center border-b-2 border-dashed pb-4 mb-4">
              <h3 className="text-xl font-bold text-primary">{receipt.clinic_name}</h3>
              <p className="text-xs text-muted-foreground mt-1">Receipt No: {receipt.bill_number}</p>
            </div>

            {/* Therapist Info */}
            <div className="space-y-1 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Therapist:</span>
                <span className="font-medium">{receipt.therapist_name}</span>
              </div>
              {receipt.therapist_mobile && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Phone:</span>
                  <span>{receipt.therapist_mobile}</span>
                </div>
              )}
              {receipt.therapist_email && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Email:</span>
                  <span className="text-xs">{receipt.therapist_email}</span>
                </div>
              )}
              {receipt.clinic_address && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Address:</span>
                  <span className="text-xs text-right max-w-[200px]">{receipt.clinic_address}</span>
                </div>
              )}
            </div>

            {/* Client Info */}
            <Card className="p-3 bg-muted/30 mb-4">
              <div className="flex items-center gap-2 mb-2">
                <User size={14} className="text-muted-foreground" />
                <span className="font-medium">{receipt.client_name}</span>
              </div>
              <p className="text-xs text-muted-foreground">ID: {receipt.client_code}</p>
            </Card>

            {/* Date/Time Info */}
            <div className="space-y-1 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Calendar size={12} /> Date:
                </span>
                <span>{receipt.date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Clock size={12} /> Time:
                </span>
                <span>{receipt.time}</span>
              </div>
              {receipt.session_date && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Session:</span>
                  <span>{receipt.session_date} at {receipt.session_time}</span>
                </div>
              )}
            </div>

            {/* Amount */}
            <Card className="p-4 text-center bg-primary/5 border-primary/20 mb-4">
              <p className="text-3xl font-bold text-primary">{formatCurrency(receipt.amount)}</p>
              <span className={`inline-block mt-2 text-xs px-3 py-1 rounded-full font-medium ${
                receipt.payment_status === 'PAID' ? 'bg-green-100 text-green-700' :
                receipt.payment_status === 'PARTIAL' ? 'bg-amber-100 text-amber-700' :
                'bg-red-100 text-red-700'
              }`}>
                {receipt.payment_status}
              </span>
            </Card>

            {/* Payment Method */}
            <div className="space-y-1 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <CreditCard size={12} /> Payment Method:
                </span>
                <span className="font-medium">{receipt.payment_method}</span>
              </div>
              {receipt.notes && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Notes:</span>
                  <span>{receipt.notes}</span>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="text-center text-xs text-muted-foreground border-t-2 border-dashed pt-4">
              <p>Thank you for your payment!</p>
              <p>This is a computer generated receipt.</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Failed to load receipt
          </div>
        )}

        {/* Action Buttons */}
        {receipt && (
          <div className="flex gap-2 mt-4">
            <Button onClick={handlePrint} variant="outline" className="flex-1">
              <Printer size={14} className="mr-1" /> Print
            </Button>
            <Button onClick={handleDownloadPDF} className="flex-1">
              <Download size={14} className="mr-1" /> Download PDF
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

// Payment card for listing payments with receipt button
export const PaymentCard = ({ payment, showReceipt = true }) => {
  const [showReceiptDialog, setShowReceiptDialog] = useState(false);

  return (
    <>
      <Card className={`p-3 ${
        payment.payment_status === 'paid' ? 'border-green-200 bg-green-50/30' :
        payment.payment_status === 'partial' ? 'border-amber-200 bg-amber-50/30' :
        'border-red-200 bg-red-50/30'
      }`}>
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2">
              <p className="font-medium">{formatCurrency(payment.amount)}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${
                payment.payment_status === 'paid' ? 'bg-green-100 text-green-700' :
                payment.payment_status === 'partial' ? 'bg-amber-100 text-amber-700' :
                'bg-red-100 text-red-700'
              }`}>
                {payment.payment_status}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {payment.payment_method?.toUpperCase()} • {formatDate(payment.created_at)}
            </p>
            {payment.bill_number && (
              <p className="text-xs text-muted-foreground">Bill #: {payment.bill_number}</p>
            )}
          </div>
          {showReceipt && (
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setShowReceiptDialog(true)}
              data-testid={`view-receipt-${payment.id}`}
            >
              <Receipt size={14} />
            </Button>
          )}
        </div>
        {payment.notes && (
          <p className="text-xs text-muted-foreground mt-2">{payment.notes}</p>
        )}
      </Card>

      <PaymentReceiptView
        paymentId={payment.id}
        isOpen={showReceiptDialog}
        onClose={() => setShowReceiptDialog(false)}
      />
    </>
  );
};

export default PaymentReceiptView;
