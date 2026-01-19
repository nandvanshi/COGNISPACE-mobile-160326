import React, { useState } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { 
  PlayCircle, StopCircle, Clock, CreditCard, CheckCircle, 
  AlertCircle, User, Calendar, Loader2, Receipt
} from 'lucide-react';
import { formatDate, formatTime, formatCurrency } from '../utils/formatUtils';

// Helper to safely extract error message
const getErrorMessage = (error, fallback = 'An error occurred') => {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) return detail[0]?.msg || fallback;
  if (typeof detail === 'object' && detail?.msg) return detail.msg;
  return fallback;
};

// Session action buttons for appointment cards
export const SessionActionButtons = ({ appointment, onRefresh, isReadOnly = false }) => {
  const [showCheckInDialog, setShowCheckInDialog] = useState(false);
  const [showCheckOutDialog, setShowCheckOutDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkInNotes, setCheckInNotes] = useState('');
  
  // Check-out form state
  const [checkOutNotes, setCheckOutNotes] = useState('');
  const [recordPayment, setRecordPayment] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMode, setPaymentMode] = useState('cash');
  const [paymentStatus, setPaymentStatus] = useState('paid');
  const [paymentNotes, setPaymentNotes] = useState('');
  
  // Result state
  const [checkOutResult, setCheckOutResult] = useState(null);
  const [showReceiptDialog, setShowReceiptDialog] = useState(false);

  const handleCheckIn = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/appointments/${appointment.id}/check-in`, {
        notes: checkInNotes || null
      });
      toast.success('Session started successfully!');
      setShowCheckInDialog(false);
      setCheckInNotes('');
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to check in'));
    } finally {
      setLoading(false);
    }
  };

  const handleCheckOut = async () => {
    setLoading(true);
    try {
      const payload = {
        notes: checkOutNotes || null,
        record_payment: recordPayment,
        payment_amount: recordPayment ? parseFloat(paymentAmount) : null,
        payment_mode: recordPayment ? paymentMode : null,
        payment_status: recordPayment ? paymentStatus : null,
        payment_notes: recordPayment ? paymentNotes : null
      };
      
      const response = await axios.post(`${API}/appointments/${appointment.id}/check-out`, payload);
      
      toast.success(`Session completed! Duration: ${response.data.actual_duration_minutes} minutes`);
      
      if (recordPayment && response.data.payment) {
        setCheckOutResult(response.data);
        setShowReceiptDialog(true);
      }
      
      setShowCheckOutDialog(false);
      resetCheckOutForm();
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to check out'));
    } finally {
      setLoading(false);
    }
  };

  const resetCheckOutForm = () => {
    setCheckOutNotes('');
    setRecordPayment(false);
    setPaymentAmount('');
    setPaymentMode('cash');
    setPaymentStatus('paid');
    setPaymentNotes('');
  };

  // Don't show for cancelled or completed appointments
  if (appointment.status === 'cancelled' || appointment.status === 'completed') {
    return null;
  }

  return (
    <>
      <div className="flex gap-2">
        {appointment.status === 'scheduled' && (
          <Button
            size="sm"
            onClick={() => setShowCheckInDialog(true)}
            disabled={isReadOnly}
            className="bg-green-600 hover:bg-green-700"
            data-testid={`check-in-btn-${appointment.id}`}
          >
            <PlayCircle size={14} className="mr-1" /> Check In
          </Button>
        )}
        
        {appointment.status === 'in_progress' && (
          <Button
            size="sm"
            onClick={() => setShowCheckOutDialog(true)}
            disabled={isReadOnly}
            className="bg-red-600 hover:bg-red-700"
            data-testid={`check-out-btn-${appointment.id}`}
          >
            <StopCircle size={14} className="mr-1" /> Check Out
          </Button>
        )}
      </div>

      {/* Check-In Dialog */}
      <Dialog open={showCheckInDialog} onOpenChange={setShowCheckInDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <PlayCircle size={20} className="text-green-600" /> Start Session
            </DialogTitle>
          </DialogHeader>
          
          <Card className="p-4 bg-muted/30">
            <div className="flex items-center gap-3">
              <User size={16} className="text-muted-foreground" />
              <span className="font-medium">{appointment.client_name}</span>
            </div>
            <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
              <Calendar size={14} />
              <span>{formatDate(appointment.start_time)} • {formatTime(appointment.start_time)}</span>
            </div>
          </Card>

          <div>
            <Label>Check-in Notes (optional)</Label>
            <Textarea
              value={checkInNotes}
              onChange={(e) => setCheckInNotes(e.target.value)}
              placeholder="Any notes about session start..."
              rows={2}
              className="mt-1"
            />
          </div>

          <div className="flex gap-2">
            <Button 
              onClick={handleCheckIn} 
              disabled={loading}
              className="flex-1 bg-green-600 hover:bg-green-700"
            >
              {loading ? <Loader2 className="animate-spin mr-2" size={16} /> : <PlayCircle size={16} className="mr-2" />}
              Start Session
            </Button>
            <Button variant="outline" onClick={() => setShowCheckInDialog(false)}>
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Check-Out Dialog */}
      <Dialog open={showCheckOutDialog} onOpenChange={setShowCheckOutDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <StopCircle size={20} className="text-red-600" /> End Session
            </DialogTitle>
          </DialogHeader>
          
          <Card className="p-4 bg-muted/30">
            <div className="flex items-center gap-3">
              <User size={16} className="text-muted-foreground" />
              <span className="font-medium">{appointment.client_name}</span>
            </div>
            <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
              <Clock size={14} />
              <span>Started: {appointment.actual_start_time ? formatTime(appointment.actual_start_time) : 'N/A'}</span>
            </div>
          </Card>

          <div>
            <Label>Check-out Notes (optional)</Label>
            <Textarea
              value={checkOutNotes}
              onChange={(e) => setCheckOutNotes(e.target.value)}
              placeholder="Session summary notes..."
              rows={2}
              className="mt-1"
            />
          </div>

          {/* Payment Section */}
          <div className="border-t pt-4">
            <div className="flex items-center gap-2 mb-3">
              <input
                type="checkbox"
                id="recordPayment"
                checked={recordPayment}
                onChange={(e) => setRecordPayment(e.target.checked)}
                className="rounded border-gray-300"
              />
              <Label htmlFor="recordPayment" className="cursor-pointer flex items-center gap-2">
                <CreditCard size={16} /> Record Payment
              </Label>
            </div>

            {recordPayment && (
              <div className="space-y-3 p-3 bg-muted/30 rounded-lg">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Amount (₹)</Label>
                    <Input
                      type="number"
                      value={paymentAmount}
                      onChange={(e) => setPaymentAmount(e.target.value)}
                      placeholder="0.00"
                      className="mt-1"
                      required
                    />
                  </div>
                  <div>
                    <Label>Payment Mode</Label>
                    <Select value={paymentMode} onValueChange={setPaymentMode}>
                      <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cash">Cash</SelectItem>
                        <SelectItem value="upi">UPI</SelectItem>
                        <SelectItem value="card">Card</SelectItem>
                        <SelectItem value="bank">Bank Transfer</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label>Payment Status</Label>
                  <Select value={paymentStatus} onValueChange={setPaymentStatus}>
                    <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="paid">Paid</SelectItem>
                      <SelectItem value="partial">Partial</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Payment Notes (optional)</Label>
                  <Input
                    value={paymentNotes}
                    onChange={(e) => setPaymentNotes(e.target.value)}
                    placeholder="e.g., Discount applied, partial due date..."
                    className="mt-1"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <Button 
              onClick={handleCheckOut} 
              disabled={loading || (recordPayment && !paymentAmount)}
              className="flex-1 bg-red-600 hover:bg-red-700"
            >
              {loading ? <Loader2 className="animate-spin mr-2" size={16} /> : <StopCircle size={16} className="mr-2" />}
              End Session {recordPayment && paymentAmount ? `& Record ₹${paymentAmount}` : ''}
            </Button>
            <Button variant="outline" onClick={() => setShowCheckOutDialog(false)}>
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Receipt Preview Dialog */}
      {checkOutResult?.payment && (
        <Dialog open={showReceiptDialog} onOpenChange={setShowReceiptDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <CheckCircle size={20} className="text-green-600" /> Payment Recorded
              </DialogTitle>
            </DialogHeader>
            
            <Card className="p-4 text-center">
              <Receipt size={48} className="mx-auto text-primary mb-3" />
              <p className="text-2xl font-bold text-primary">{formatCurrency(checkOutResult.payment.amount)}</p>
              <p className="text-sm text-muted-foreground mt-1">
                Bill #: {checkOutResult.payment.bill_number}
              </p>
              <p className="text-sm text-muted-foreground">
                {checkOutResult.payment.payment_method?.toUpperCase()} • {checkOutResult.payment.payment_status?.toUpperCase()}
              </p>
            </Card>

            <div className="text-sm space-y-1 text-muted-foreground">
              <p>Session Duration: <strong>{checkOutResult.actual_duration_minutes} minutes</strong></p>
              <p>Client: <strong>{appointment.client_name}</strong></p>
            </div>

            <div className="flex gap-2">
              <Button 
                onClick={() => window.open(`${API}/payments/${checkOutResult.payment.id}/receipt`, '_blank')}
                variant="outline"
                className="flex-1"
              >
                <Receipt size={14} className="mr-1" /> View Receipt
              </Button>
              <Button onClick={() => setShowReceiptDialog(false)} className="flex-1">
                Done
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
};

// Appointment status badge component
export const AppointmentStatusBadge = ({ status, actualStartTime, actualDurationMinutes }) => {
  const statusConfig = {
    scheduled: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Scheduled' },
    in_progress: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'In Progress' },
    completed: { bg: 'bg-green-100', text: 'text-green-700', label: 'Completed' },
    cancelled: { bg: 'bg-red-100', text: 'text-red-700', label: 'Cancelled' }
  };

  const config = statusConfig[status] || statusConfig.scheduled;

  return (
    <div className="flex items-center gap-2">
      <span className={`text-xs px-2 py-1 rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
      {status === 'in_progress' && actualStartTime && (
        <span className="text-xs text-amber-600 flex items-center gap-1">
          <Clock size={12} /> Started {formatTime(actualStartTime)}
        </span>
      )}
      {status === 'completed' && actualDurationMinutes && (
        <span className="text-xs text-green-600 flex items-center gap-1">
          <Clock size={12} /> {actualDurationMinutes} min
        </span>
      )}
    </div>
  );
};

export default SessionActionButtons;
