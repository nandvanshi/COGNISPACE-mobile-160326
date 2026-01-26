import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { toast } from 'sonner';
import { 
  IndianRupee, 
  TrendingUp, 
  TrendingDown,
  Calendar,
  Users,
  Download,
  BarChart3,
  FileSpreadsheet,
  Filter,
  RefreshCw,
  Wallet,
  CreditCard,
  Banknote
} from 'lucide-react';
import { formatCurrency, formatDate } from '../utils/formatUtils';

// Simple bar chart component - defined outside to prevent re-renders
const SimpleBarChart = ({ data, maxValue }) => {
  if (!data || data.length === 0) return null;
  const max = maxValue || Math.max(...data.map(d => d.paid));
  
  return (
    <div className="flex items-end gap-2 h-40 mt-4">
      {data.map((item, idx) => (
        <div key={idx} className="flex-1 flex flex-col items-center">
          <div className="w-full bg-gray-100 rounded-t-lg relative" style={{ height: '120px' }}>
            <div 
              className="absolute bottom-0 w-full bg-gradient-to-t from-primary to-primary/70 rounded-t-lg transition-all duration-500"
              style={{ height: `${max > 0 ? (item.paid / max) * 100 : 0}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground mt-2">
            {item.month?.split('-')[1] || ''}
          </span>
          <span className="text-xs font-medium text-primary">
            {formatCurrency(item.paid)}
          </span>
        </div>
      ))}
    </div>
  );
};

const PaymentReports = () => {
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState(true);
  const [clients, setClients] = useState([]);
  
  // Date filters
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setMonth(d.getMonth() - 1);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
  
  // Data states
  const [summaryStats, setSummaryStats] = useState(null);
  const [detailedReport, setDetailedReport] = useState(null);
  const [monthlyTrend, setMonthlyTrend] = useState(null);
  const [clientWiseReport, setClientWiseReport] = useState(null);
  
  // Filter states
  const [filterClient, setFilterClient] = useState('');
  const [filterMethod, setFilterMethod] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    fetchClients();
    fetchAllData();
  }, []);

  const fetchClients = async () => {
    try {
      const res = await axios.get(`${API}/clients`);
      setClients(res.data);
    } catch (error) {
      console.error('Failed to load clients');
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSummary(),
        fetchDetailedReport(),
        fetchMonthlyTrend(),
        fetchClientWise()
      ]);
    } catch (error) {
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await axios.get(`${API}/payments/stats/summary`, {
        params: { start_date: startDate, end_date: endDate }
      });
      setSummaryStats(res.data);
    } catch (error) {
      console.error('Failed to load summary');
    }
  };

  const fetchDetailedReport = async () => {
    try {
      const params = { start_date: startDate, end_date: endDate };
      if (filterClient) params.client_id = filterClient;
      if (filterMethod) params.payment_method = filterMethod;
      if (filterStatus) params.payment_status = filterStatus;
      
      const res = await axios.get(`${API}/payments/reports/detailed`, { params });
      setDetailedReport(res.data);
    } catch (error) {
      console.error('Failed to load detailed report');
    }
  };

  const fetchMonthlyTrend = async () => {
    try {
      const res = await axios.get(`${API}/payments/reports/monthly-trend`, {
        params: { months: 6 }
      });
      setMonthlyTrend(res.data);
    } catch (error) {
      console.error('Failed to load monthly trend');
    }
  };

  const fetchClientWise = async () => {
    try {
      const res = await axios.get(`${API}/payments/reports/client-wise`, {
        params: { start_date: startDate, end_date: endDate, sort_by: 'total' }
      });
      setClientWiseReport(res.data);
    } catch (error) {
      console.error('Failed to load client-wise report');
    }
  };

  const handleApplyFilters = () => {
    fetchAllData();
  };

  const handleExport = async (format) => {
    try {
      const res = await axios.get(`${API}/payments/reports/export`, {
        params: { start_date: startDate, end_date: endDate, format }
      });
      
      if (format === 'csv') {
        const blob = new Blob([res.data.csv_data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = res.data.filename;
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success('Report exported successfully');
      } else {
        // JSON - download as JSON file
        const blob = new Blob([JSON.stringify(res.data.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `payments_${startDate}_to_${endDate}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        toast.success('Report exported successfully');
      }
    } catch (error) {
      toast.error('Failed to export report');
    }
  };

  const getPaymentMethodIcon = (method) => {
    switch (method?.toLowerCase()) {
      case 'cash':
        return <Banknote size={16} className="text-green-600" />;
      case 'upi':
      case 'online':
        return <Wallet size={16} className="text-blue-600" />;
      case 'card':
        return <CreditCard size={16} className="text-purple-600" />;
      default:
        return <IndianRupee size={16} className="text-gray-600" />;
    }
  };

  // Simple bar chart component
  const SimpleBarChart = ({ data, maxValue }) => {
    if (!data || data.length === 0) return null;
    const max = maxValue || Math.max(...data.map(d => d.paid));
    
    return (
      <div className="flex items-end gap-2 h-40 mt-4">
        {data.map((item, idx) => (
          <div key={idx} className="flex-1 flex flex-col items-center">
            <div className="w-full bg-gray-100 rounded-t-lg relative" style={{ height: '120px' }}>
              <div 
                className="absolute bottom-0 w-full bg-gradient-to-t from-primary to-primary/70 rounded-t-lg transition-all duration-500"
                style={{ height: `${max > 0 ? (item.paid / max) * 100 : 0}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground mt-2">
              {item.month?.split('-')[1] || ''}
            </span>
            <span className="text-xs font-medium text-primary">
              {formatCurrency(item.paid)}
            </span>
          </div>
        ))}
      </div>
    );
  };

  if (loading && !summaryStats) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="animate-spin text-primary mr-2" size={24} />
        <span>Loading reports...</span>
      </div>
    );
  }

  return (
    <div data-testid="payment-reports">
      {/* Header */}
      <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-3xl md:text-4xl font-serif text-primary mb-2">Payment Reports</h2>
          <p className="text-muted-foreground">Analytics and insights for your practice revenue</p>
        </div>
        
        {/* Export Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleExport('csv')}
            className="gap-2"
            data-testid="export-csv-btn"
          >
            <FileSpreadsheet size={18} />
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport('json')}
            className="gap-2"
            data-testid="export-json-btn"
          >
            <Download size={18} />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Date Range Filters */}
      <Card className="p-4 mb-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <Label htmlFor="start-date" className="text-sm">Start Date</Label>
            <Input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-40"
              data-testid="start-date-input"
            />
          </div>
          <div>
            <Label htmlFor="end-date" className="text-sm">End Date</Label>
            <Input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-40"
              data-testid="end-date-input"
            />
          </div>
          <div>
            <Label htmlFor="filter-client" className="text-sm">Client</Label>
            <select
              id="filter-client"
              value={filterClient}
              onChange={(e) => setFilterClient(e.target.value)}
              className="h-10 px-3 rounded-lg border border-border bg-white text-sm"
              data-testid="filter-client-select"
            >
              <option value="">All Clients</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>{c.full_name}</option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="filter-method" className="text-sm">Method</Label>
            <select
              id="filter-method"
              value={filterMethod}
              onChange={(e) => setFilterMethod(e.target.value)}
              className="h-10 px-3 rounded-lg border border-border bg-white text-sm"
              data-testid="filter-method-select"
            >
              <option value="">All Methods</option>
              <option value="cash">Cash</option>
              <option value="upi">UPI</option>
              <option value="card">Card</option>
              <option value="online">Online</option>
              <option value="bank_transfer">Bank Transfer</option>
            </select>
          </div>
          <div>
            <Label htmlFor="filter-status" className="text-sm">Status</Label>
            <select
              id="filter-status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-10 px-3 rounded-lg border border-border bg-white text-sm"
              data-testid="filter-status-select"
            >
              <option value="">All Status</option>
              <option value="paid">Paid</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <Button onClick={handleApplyFilters} className="gap-2" data-testid="apply-filters-btn">
            <Filter size={16} />
            Apply Filters
          </Button>
        </div>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Total Revenue */}
        <Card className="p-5 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200" data-testid="total-revenue-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600 font-medium">Total Revenue</p>
              <p className="text-2xl font-bold text-green-700 mt-1">
                {formatCurrency(summaryStats?.total_amount || 0)}
              </p>
              <p className="text-xs text-green-500 mt-1">
                {summaryStats?.total_transactions || 0} transactions
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <IndianRupee className="text-green-600" size={24} />
            </div>
          </div>
        </Card>

        {/* Collected */}
        <Card className="p-5 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200" data-testid="collected-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600 font-medium">Collected</p>
              <p className="text-2xl font-bold text-blue-700 mt-1">
                {formatCurrency(summaryStats?.paid_amount || 0)}
              </p>
              <p className="text-xs text-blue-500 mt-1">
                {detailedReport?.summary?.collection_rate || 0}% collection rate
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <TrendingUp className="text-blue-600" size={24} />
            </div>
          </div>
        </Card>

        {/* Pending */}
        <Card className="p-5 bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200" data-testid="pending-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-amber-600 font-medium">Pending</p>
              <p className="text-2xl font-bold text-amber-700 mt-1">
                {formatCurrency(summaryStats?.pending_amount || 0)}
              </p>
              <p className="text-xs text-amber-500 mt-1">
                Awaiting payment
              </p>
            </div>
            <div className="p-3 bg-amber-100 rounded-full">
              <Calendar className="text-amber-600" size={24} />
            </div>
          </div>
        </Card>

        {/* Growth */}
        <Card className="p-5 bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200" data-testid="growth-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-purple-600 font-medium">Monthly Growth</p>
              <p className="text-2xl font-bold text-purple-700 mt-1">
                {monthlyTrend?.growth_rate_percent > 0 ? '+' : ''}{monthlyTrend?.growth_rate_percent || 0}%
              </p>
              <p className="text-xs text-purple-500 mt-1">
                vs. previous month
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              {(monthlyTrend?.growth_rate_percent || 0) >= 0 ? (
                <TrendingUp className="text-purple-600" size={24} />
              ) : (
                <TrendingDown className="text-purple-600" size={24} />
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-4 bg-white/70 border">
          <TabsTrigger value="summary" className="gap-2" data-testid="tab-summary">
            <BarChart3 size={16} />
            Overview
          </TabsTrigger>
          <TabsTrigger value="transactions" className="gap-2" data-testid="tab-transactions">
            <FileSpreadsheet size={16} />
            Transactions
          </TabsTrigger>
          <TabsTrigger value="clients" className="gap-2" data-testid="tab-clients">
            <Users size={16} />
            By Client
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="summary">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Monthly Trend Chart */}
            <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="monthly-trend-card">
              <h3 className="text-lg font-semibold text-primary mb-4">Monthly Revenue Trend</h3>
              {monthlyTrend?.months && monthlyTrend.months.length > 0 ? (
                <>
                  <SimpleBarChart data={monthlyTrend.months} />
                  <div className="mt-4 pt-4 border-t grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Average Monthly</p>
                      <p className="text-lg font-semibold text-primary">
                        {formatCurrency(monthlyTrend.average_monthly_revenue || 0)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Period Total</p>
                      <p className="text-lg font-semibold text-primary">
                        {formatCurrency(monthlyTrend.total_period_revenue || 0)}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-center text-muted-foreground py-10">No data available</p>
              )}
            </Card>

            {/* Payment Methods Breakdown */}
            <Card className="p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="payment-methods-card">
              <h3 className="text-lg font-semibold text-primary mb-4">Payment Methods</h3>
              {summaryStats?.by_payment_method && Object.keys(summaryStats.by_payment_method).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(summaryStats.by_payment_method).map(([method, amount]) => {
                    const total = summaryStats.total_amount || 1;
                    const percentage = Math.round((amount / total) * 100);
                    return (
                      <div key={method} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {getPaymentMethodIcon(method)}
                            <span className="capitalize font-medium">{method}</span>
                          </div>
                          <span className="font-semibold">{formatCurrency(amount)}</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground text-right">{percentage}%</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-10">No payment data</p>
              )}
            </Card>
          </div>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions">
          <Card className="overflow-hidden bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="transactions-table-card">
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="transactions-table">
                <thead className="bg-surface">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-foreground">Bill #</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-foreground">Date</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-foreground">Client</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-foreground">Amount</th>
                    <th className="px-4 py-3 text-center text-sm font-medium text-foreground">Method</th>
                    <th className="px-4 py-3 text-center text-sm font-medium text-foreground">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {detailedReport?.payments && detailedReport.payments.length > 0 ? (
                    detailedReport.payments.map((payment) => (
                      <tr key={payment.id} className="hover:bg-surface/50" data-testid={`transaction-row-${payment.id}`}>
                        <td className="px-4 py-3 text-sm font-mono text-muted-foreground">
                          {payment.bill_number}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {formatDate(payment.created_at)}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">
                          {payment.client_name}
                        </td>
                        <td className="px-4 py-3 text-sm text-right font-semibold text-primary">
                          {formatCurrency(payment.amount)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs capitalize">
                            {getPaymentMethodIcon(payment.payment_method)}
                            {payment.payment_method}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            payment.payment_status === 'paid' 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-amber-100 text-amber-700'
                          }`}>
                            {payment.payment_status}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">
                        No transactions found for the selected period
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>

        {/* By Client Tab */}
        <TabsContent value="clients">
          <Card className="overflow-hidden bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl" data-testid="client-wise-card">
            <div className="p-4 border-b bg-surface/50">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Client-wise Breakdown</h3>
                <p className="text-sm text-muted-foreground">
                  {clientWiseReport?.summary?.total_clients || 0} clients
                </p>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="client-wise-table">
                <thead className="bg-surface">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-foreground">Client</th>
                    <th className="px-4 py-3 text-center text-sm font-medium text-foreground">Transactions</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-foreground">Total</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-foreground">Collected</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-foreground">Pending</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-foreground">Avg Payment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {clientWiseReport?.clients && clientWiseReport.clients.length > 0 ? (
                    clientWiseReport.clients.map((client, idx) => (
                      <tr key={client.client_id || idx} className="hover:bg-surface/50" data-testid={`client-row-${client.client_id}`}>
                        <td className="px-4 py-3">
                          <div>
                            <p className="text-sm font-medium">{client.client_name}</p>
                            {client.client_code && (
                              <p className="text-xs text-muted-foreground">{client.client_code}</p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center text-sm">
                          {client.transaction_count}
                        </td>
                        <td className="px-4 py-3 text-right text-sm font-semibold">
                          {formatCurrency(client.total_amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-green-600 font-medium">
                          {formatCurrency(client.paid_amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-sm">
                          {client.pending_amount > 0 ? (
                            <span className="text-amber-600 font-medium">
                              {formatCurrency(client.pending_amount)}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-muted-foreground">
                          {formatCurrency(client.average_payment)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center text-muted-foreground">
                        No client data available
                      </td>
                    </tr>
                  )}
                </tbody>
                {clientWiseReport?.summary && (
                  <tfoot className="bg-surface font-semibold">
                    <tr>
                      <td className="px-4 py-3 text-sm">Total</td>
                      <td className="px-4 py-3 text-center text-sm">-</td>
                      <td className="px-4 py-3 text-right text-sm">
                        {formatCurrency(clientWiseReport.summary.grand_total)}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-green-600">
                        {formatCurrency(clientWiseReport.summary.total_collected)}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-amber-600">
                        {formatCurrency(clientWiseReport.summary.total_pending)}
                      </td>
                      <td className="px-4 py-3 text-right text-sm">-</td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PaymentReports;
