import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Plus, IndianRupee, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { formatCurrency, formatDate } from '../utils/formatUtils';

const Payments = ({ isReadOnly = false }) => {
  const [payments, setPayments] = useState([]);
  const [clients, setClients] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [newPayment, setNewPayment] = useState({
    client_id: '',
    amount: '',
    payment_method: 'cash',
    transaction_type: 'credit',
    notes: '',
  });
  const [loading, setLoading] = useState(true);
  const [filterClient, setFilterClient] = useState('');
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [paymentsRes, clientsRes] = await Promise.all([
        axios.get(`${API}/payments`),
        axios.get(`${API}/clients`),
      ]);
      setPayments(paymentsRes.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));
      setClients(clientsRes.data);
    } catch (error) {
      toast.error('Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();

    if (!newPayment.client_id || !newPayment.amount) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await axios.post(`${API}/payments`, {
        client_id: newPayment.client_id,
        amount: parseFloat(newPayment.amount),
        payment_method: newPayment.payment_method,
        transaction_type: newPayment.transaction_type,
        notes: newPayment.notes,
      });
      const actionText = newPayment.transaction_type === 'debit' ? 'Refund recorded' : 'Payment recorded';
      toast.success(actionText);
      setShowDialog(false);
      setNewPayment({ client_id: '', amount: '', payment_method: 'cash', transaction_type: 'credit', notes: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to record payment');
    }
  };

  const filteredPayments = filterClient
    ? payments.filter((p) => p.client_id === filterClient)
    : payments;

  // Calculate totals considering transaction_type
  const creditTotal = filteredPayments
    .filter(p => p.transaction_type !== 'debit')
    .reduce((sum, p) => sum + p.amount, 0);
  const debitTotal = filteredPayments
    .filter(p => p.transaction_type === 'debit')
    .reduce((sum, p) => sum + p.amount, 0);
  const netTotal = creditTotal - debitTotal;

  if (loading) {
    return <div className="text-center py-12">Loading payments...</div>;
  }

  return (
    <div data-testid="payments">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Payment Tracking</h2>
          <p className="text-muted-foreground">Manually track client payments</p>
        </div>
        {!isReadOnly && (
          <Button
            onClick={() => setShowDialog(true)}
            className="bg-primary hover:bg-primary-700 rounded-full"
            data-testid="record-payment-button"
          >
            <Plus size={20} className="mr-2" />
            Record Payment
          </Button>
        )}
      </div>

      {/* Summary Card */}
      <Card className="mb-6 p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="payment-summary">
        <div className="flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-success/10 rounded-lg">
              <IndianRupee className="text-success" size={32} />
            </div>
            <div>
              <p className="text-3xl font-bold text-primary">{formatCurrency(netTotal)}</p>
              <p className="text-sm text-muted-foreground">
                {filterClient ? 'Net Balance' : 'Net Revenue'}
              </p>
            </div>
          </div>
          
          {/* Credit/Debit breakdown */}
          <div className="flex gap-6 ml-auto">
            <div className="flex items-center gap-2">
              <ArrowUpCircle className="text-green-600" size={20} />
              <div>
                <p className="text-lg font-semibold text-green-600">{formatCurrency(creditTotal)}</p>
                <p className="text-xs text-muted-foreground">Credit</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ArrowDownCircle className="text-red-500" size={20} />
              <div>
                <p className="text-lg font-semibold text-red-500">{formatCurrency(debitTotal)}</p>
                <p className="text-xs text-muted-foreground">Debit/Refund</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Filter */}
      <div className="mb-6">
        <Label htmlFor="filter-client">Filter by Client</Label>
        <select
          id="filter-client"
          data-testid="filter-client-select"
          value={filterClient}
          onChange={(e) => setFilterClient(e.target.value)}
          className="w-full md:w-64 mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">All Clients</option>
          {clients.map((client) => (
            <option key={client.id} value={client.id}>
              {client.full_name}
            </option>
          ))}
        </select>
      </div>

      {/* Payments Table */}
      <Card className="overflow-hidden bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="payments-table">
            <thead className="bg-surface">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-medium text-foreground">Date</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-foreground">Client</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-foreground">Type</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-foreground">Amount</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-foreground">Method</th>
                <th className="px-6 py-4 text-left text-sm font-medium text-foreground">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredPayments.map((payment) => (
                <tr key={payment.id} data-testid={`payment-${payment.id}`}>
                  <td className="px-6 py-4 text-sm text-foreground">
                    {formatDate(payment.created_at)}
                  </td>
                  <td className="px-6 py-4 text-sm text-foreground font-medium">
                    {payment.client_name}
                  </td>
                  <td className="px-6 py-4">
                    {payment.transaction_type === 'debit' ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                        <ArrowDownCircle size={12} /> Debit
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        <ArrowUpCircle size={12} /> Credit
                      </span>
                    )}
                  </td>
                  <td className={`px-6 py-4 text-sm font-medium ${payment.transaction_type === 'debit' ? 'text-red-600' : 'text-foreground'}`}>
                    {payment.transaction_type === 'debit' ? '-' : ''}{formatCurrency(payment.amount)}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground capitalize">
                    {payment.payment_method === 'bank_transfer' ? 'Bank Transfer' : 
                     payment.payment_method === 'credit_card' ? 'Credit Card' :
                     payment.payment_method === 'upi' ? 'UPI' :
                     payment.payment_method}
                  </td>
                  <td className="px-6 py-4 text-sm text-muted-foreground">
                    {payment.notes || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredPayments.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No payments recorded</p>
          </div>
        )}
      </Card>

      {/* Record Payment Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent data-testid="payment-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">
              {newPayment.transaction_type === 'debit' ? 'Record Refund/Debit' : 'Record Payment'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleRecordPayment} className="space-y-4">
            {/* Transaction Type Toggle */}
            <div>
              <Label>Transaction Type</Label>
              <div className="flex gap-2 mt-2">
                <Button
                  type="button"
                  variant={newPayment.transaction_type === 'credit' ? 'default' : 'outline'}
                  onClick={() => setNewPayment({ ...newPayment, transaction_type: 'credit' })}
                  className={`flex-1 ${newPayment.transaction_type === 'credit' ? 'bg-green-600 hover:bg-green-700' : ''}`}
                  data-testid="credit-type-btn"
                >
                  <ArrowUpCircle size={16} className="mr-2" />
                  Credit (Payment)
                </Button>
                <Button
                  type="button"
                  variant={newPayment.transaction_type === 'debit' ? 'default' : 'outline'}
                  onClick={() => setNewPayment({ ...newPayment, transaction_type: 'debit' })}
                  className={`flex-1 ${newPayment.transaction_type === 'debit' ? 'bg-red-600 hover:bg-red-700' : ''}`}
                  data-testid="debit-type-btn"
                >
                  <ArrowDownCircle size={16} className="mr-2" />
                  Debit (Refund)
                </Button>
              </div>
            </div>

            <div>
              <Label htmlFor="payment-client">Client</Label>
              <select
                id="payment-client"
                data-testid="payment-client-select"
                value={newPayment.client_id}
                onChange={(e) => setNewPayment({ ...newPayment, client_id: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
                required
              >
                <option value="">Select a client</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="amount">
                Amount (₹) {newPayment.transaction_type === 'debit' && <span className="text-red-500">- Refund</span>}
              </Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                min="0"
                data-testid="amount-input"
                value={newPayment.amount}
                onChange={(e) => setNewPayment({ ...newPayment, amount: e.target.value })}
                required
                className={`mt-1 ${newPayment.transaction_type === 'debit' ? 'border-red-300 focus:ring-red-500' : ''}`}
                placeholder={newPayment.transaction_type === 'debit' ? 'Enter refund amount' : 'Enter amount in rupees'}
              />
            </div>
            <div>
              <Label htmlFor="payment-method">Payment Method</Label>
              <select
                id="payment-method"
                data-testid="payment-method-select"
                value={newPayment.payment_method}
                onChange={(e) => setNewPayment({ ...newPayment, payment_method: e.target.value })}
                className="w-full mt-1 h-12 px-4 rounded-lg border border-border bg-white focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="cash">Cash</option>
                <option value="upi">UPI</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="credit_card">Credit Card</option>
                <option value="cheque">Cheque</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <Label htmlFor="payment-notes">Notes (optional)</Label>
              <Textarea
                id="payment-notes"
                data-testid="payment-notes-input"
                value={newPayment.notes}
                onChange={(e) => setNewPayment({ ...newPayment, notes: e.target.value })}
                rows={3}
                placeholder={newPayment.transaction_type === 'debit' ? 'Reason for refund, cancellation details...' : 'Session number, invoice reference, etc.'}
                className="mt-1"
              />
            </div>
            <div className="flex gap-3">
              <Button 
                type="submit" 
                className={`flex-1 ${newPayment.transaction_type === 'debit' ? 'bg-red-600 hover:bg-red-700' : ''}`}
                data-testid="save-payment-button"
              >
                {newPayment.transaction_type === 'debit' ? 'Record Refund' : 'Record Payment'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDialog(false)}
                data-testid="cancel-payment-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Notice */}
      <div className="mt-6 p-4 bg-info/10 border border-info/20 rounded-xl">
        <p className="text-sm text-info">
          <strong>Manual Tracking:</strong> This is for record-keeping only. No payment processing is
          integrated in this MVP.
        </p>
      </div>
    </div>
  );
};

export default Payments;
