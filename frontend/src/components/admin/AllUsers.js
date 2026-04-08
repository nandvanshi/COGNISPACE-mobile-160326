import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API } from '../../App';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Search, Users, UserCheck, UserCog, Headphones, ChevronLeft, ChevronRight, RefreshCw, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';

const ROLE_CONFIG = {
  all: { label: 'All Users', icon: Users, color: 'bg-slate-100 text-slate-700' },
  therapist: { label: 'Therapists', icon: UserCog, color: 'bg-blue-100 text-blue-700' },
  client: { label: 'Clients', icon: UserCheck, color: 'bg-green-100 text-green-700' },
  assistant: { label: 'Assistants', icon: Headphones, color: 'bg-purple-100 text-purple-700' },
};

const AllUsers = () => {
  const [users, setUsers] = useState([]);
  const [counts, setCounts] = useState({ all: 0, therapist: 0, client: 0, assistant: 0 });
  const [loading, setLoading] = useState(true);
  const [activeRole, setActiveRole] = useState('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [copiedId, setCopiedId] = useState(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 50 });
      if (activeRole !== 'all') params.append('role', activeRole);
      if (search.trim()) params.append('search', search.trim());

      const { data } = await axios.get(`${API}/admin/all-users?${params}`);
      setUsers(data.users);
      setCounts(data.counts);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  }, [activeRole, search, page]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  useEffect(() => { setPage(1); }, [activeRole, search]);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    toast.success('Copied!');
    setTimeout(() => setCopiedId(null), 1500);
  };

  const getRoleBadge = (role) => {
    const config = ROLE_CONFIG[role] || ROLE_CONFIG.all;
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.color}`}>{role}</span>;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch { return '-'; }
  };

  return (
    <div data-testid="all-users-view">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-serif text-primary" data-testid="all-users-title">All Users</h2>
          <p className="text-sm text-muted-foreground mt-1">View all registered users in the system</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchUsers} data-testid="refresh-users-btn">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      {/* Role Filter Tabs */}
      <div className="flex flex-wrap gap-2 mb-4" data-testid="role-filters">
        {Object.entries(ROLE_CONFIG).map(([role, config]) => {
          const Icon = config.icon;
          const isActive = activeRole === role;
          return (
            <button
              key={role}
              data-testid={`filter-${role}`}
              onClick={() => setActiveRole(role)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive ? 'bg-primary text-white shadow-sm' : 'bg-surface border border-border hover:bg-white/80 text-foreground'
              }`}
            >
              <Icon size={16} />
              {config.label}
              <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs ${isActive ? 'bg-white/20' : 'bg-muted'}`}>
                {counts[role] || 0}
              </span>
            </button>
          );
        })}
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <Input
          data-testid="user-search-input"
          placeholder="Search by name, mobile, or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Users Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="users-table">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">#</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Name</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Mobile</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Email</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Role</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Status</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">Created</th>
                <th className="text-left p-3 text-xs font-semibold text-muted-foreground uppercase">ID</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} className="p-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={8} className="p-8 text-center text-muted-foreground">No users found</td></tr>
              ) : (
                users.map((user, idx) => (
                  <tr key={user.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors" data-testid={`user-row-${idx}`}>
                    <td className="p-3 text-sm text-muted-foreground">{(page - 1) * 50 + idx + 1}</td>
                    <td className="p-3">
                      <span className="font-medium text-sm">{user.full_name || '-'}</span>
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-1">
                        <span className="text-sm font-mono">{user.mobile || '-'}</span>
                        {user.mobile && (
                          <button
                            onClick={() => copyToClipboard(user.mobile, `mob-${user.id}`)}
                            className="text-muted-foreground hover:text-foreground p-0.5"
                            data-testid={`copy-mobile-${idx}`}
                          >
                            {copiedId === `mob-${user.id}` ? <Check size={12} className="text-green-500" /> : <Copy size={12} />}
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="p-3 text-sm text-muted-foreground max-w-[200px] truncate">{user.email || '-'}</td>
                    <td className="p-3">{getRoleBadge(user.role)}</td>
                    <td className="p-3">
                      <Badge variant={user.status === 'approved' || user.status === 'active' ? 'default' : 'secondary'} className="text-xs">
                        {user.status || '-'}
                      </Badge>
                    </td>
                    <td className="p-3 text-sm text-muted-foreground whitespace-nowrap">{formatDate(user.created_at)}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-1">
                        <span className="text-xs font-mono text-muted-foreground max-w-[80px] truncate">{user.id?.slice(0, 8)}...</span>
                        <button
                          onClick={() => copyToClipboard(user.id, `id-${user.id}`)}
                          className="text-muted-foreground hover:text-foreground p-0.5"
                          data-testid={`copy-id-${idx}`}
                        >
                          {copiedId === `id-${user.id}` ? <Check size={12} className="text-green-500" /> : <Copy size={12} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-3 border-t border-border bg-muted/20">
            <span className="text-sm text-muted-foreground">
              Showing {(page - 1) * 50 + 1}-{Math.min(page * 50, total)} of {total}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline" size="sm"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                data-testid="prev-page-btn"
              >
                <ChevronLeft size={16} />
              </Button>
              <span className="text-sm font-medium">Page {page} / {totalPages}</span>
              <Button
                variant="outline" size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                data-testid="next-page-btn"
              >
                <ChevronRight size={16} />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default AllUsers;
