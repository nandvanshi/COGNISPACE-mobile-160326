import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Bell, X, Check, CheckCheck, Trash2, Calendar, 
  CreditCard, FileText, User, Clock, AlertCircle,
  ChevronRight, Loader2, BellOff
} from 'lucide-react';
import { toast } from 'sonner';

// Format date to IST DD/MM/YYYY HH:mm
const formatNotificationTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const istOffset = 5.5 * 60 * 60 * 1000;
  const istDate = new Date(date.getTime() + istOffset);
  
  const now = new Date();
  const nowIST = new Date(now.getTime() + istOffset);
  const diffMs = nowIST - istDate;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  // Relative time for recent notifications
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  // Full date for older
  const day = istDate.getDate().toString().padStart(2, '0');
  const month = (istDate.getMonth() + 1).toString().padStart(2, '0');
  const year = istDate.getFullYear();
  const hours = istDate.getHours().toString().padStart(2, '0');
  const mins = istDate.getMinutes().toString().padStart(2, '0');
  
  return `${day}/${month}/${year} ${hours}:${mins}`;
};

// Get icon based on notification type
const getNotificationIcon = (type) => {
  switch (type) {
    case 'appointment': return Calendar;
    case 'payment': return CreditCard;
    case 'session': return FileText;
    case 'client': return User;
    case 'homework': return FileText;
    case 'report': return FileText;
    case 'system': return AlertCircle;
    default: return Bell;
  }
};

// Get color based on notification type
const getNotificationColor = (type) => {
  switch (type) {
    case 'appointment': return 'text-blue-600 bg-blue-100';
    case 'payment': return 'text-emerald-600 bg-emerald-100';
    case 'session': return 'text-violet-600 bg-violet-100';
    case 'client': return 'text-amber-600 bg-amber-100';
    case 'homework': return 'text-orange-600 bg-orange-100';
    case 'report': return 'text-purple-600 bg-purple-100';
    case 'system': return 'text-red-600 bg-red-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};

const NotificationBell = ({ onNavigate }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const [notifRes, countRes] = await Promise.all([
        axios.get(`${API}/notifications?limit=20`),
        axios.get(`${API}/notifications/unread-count`)
      ]);
      setNotifications(notifRes.data || []);
      setUnreadCount(countRes.data?.count || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  // Initial fetch and polling setup
  useEffect(() => {
    fetchNotifications();
    
    // Poll every 30 seconds
    pollIntervalRef.current = setInterval(fetchNotifications, 30000);
    
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Mark single notification as read
  const markAsRead = async (notificationId, link) => {
    try {
      await axios.patch(`${API}/notifications/${notificationId}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
      
      // Navigate if link provided
      if (link && onNavigate) {
        setIsOpen(false);
        onNavigate(link);
      }
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await axios.patch(`${API}/notifications/mark-all-read`);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  // Clear all notifications
  const clearAll = async () => {
    try {
      await axios.delete(`${API}/notifications/clear-all`);
      setNotifications([]);
      setUnreadCount(0);
      toast.success('All notifications cleared');
    } catch (error) {
      toast.error('Failed to clear notifications');
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setIsOpen(!isOpen)}
        className="relative rounded-full hover:bg-gray-100"
        data-testid="notification-bell"
      >
        <Bell size={20} className={unreadCount > 0 ? 'text-primary' : 'text-gray-600'} />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center bg-red-500 text-white text-xs font-bold rounded-full animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div 
          className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 overflow-hidden"
          data-testid="notification-dropdown"
        >
          {/* Header */}
          <div className="px-4 py-3 bg-gradient-to-r from-primary/10 to-primary/5 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell size={18} className="text-primary" />
              <h3 className="font-semibold text-gray-800">Notifications</h3>
              {unreadCount > 0 && (
                <Badge className="bg-primary text-white text-xs">{unreadCount} new</Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(false)}
              className="h-7 w-7 rounded-full"
            >
              <X size={16} />
            </Button>
          </div>

          {/* Actions Bar */}
          {notifications.length > 0 && (
            <div className="px-3 py-2 bg-gray-50 border-b flex items-center justify-between text-xs">
              <button
                onClick={markAllAsRead}
                className="flex items-center gap-1 text-primary hover:text-primary/80 font-medium"
                disabled={unreadCount === 0}
              >
                <CheckCheck size={14} /> Mark all read
              </button>
              <button
                onClick={clearAll}
                className="flex items-center gap-1 text-gray-500 hover:text-red-500 font-medium"
              >
                <Trash2 size={14} /> Clear all
              </button>
            </div>
          )}

          {/* Notifications List */}
          <div className="max-h-[400px] overflow-y-auto">
            {loading ? (
              <div className="py-10 text-center">
                <Loader2 className="animate-spin mx-auto text-primary" size={24} />
              </div>
            ) : notifications.length === 0 ? (
              <div className="py-10 text-center">
                <BellOff size={40} className="mx-auto text-gray-300 mb-3" />
                <p className="text-sm text-gray-500">No notifications</p>
                <p className="text-xs text-gray-400 mt-1">You're all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => {
                  const Icon = getNotificationIcon(notification.type);
                  const colorClass = getNotificationColor(notification.type);
                  
                  return (
                    <div
                      key={notification.id}
                      onClick={() => markAsRead(notification.id, notification.link)}
                      className={`px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors ${
                        !notification.is_read ? 'bg-primary/5' : ''
                      }`}
                      data-testid={`notification-${notification.id}`}
                    >
                      <div className="flex gap-3">
                        {/* Icon */}
                        <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${colorClass}`}>
                          <Icon size={16} />
                        </div>
                        
                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className={`text-sm ${!notification.is_read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
                              {notification.title}
                            </p>
                            {!notification.is_read && (
                              <span className="w-2 h-2 bg-primary rounded-full flex-shrink-0 mt-1.5" />
                            )}
                          </div>
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                            {notification.message}
                          </p>
                          <div className="flex items-center justify-between mt-1.5">
                            <span className="text-xs text-gray-400 flex items-center gap-1">
                              <Clock size={10} />
                              {formatNotificationTime(notification.created_at)}
                            </span>
                            {notification.link && (
                              <span className="text-xs text-primary flex items-center gap-0.5">
                                View <ChevronRight size={12} />
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 bg-gray-50 border-t text-center">
              <button
                onClick={() => {
                  setIsOpen(false);
                  if (onNavigate) onNavigate('notifications');
                }}
                className="text-xs text-primary hover:text-primary/80 font-medium"
              >
                View All Notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
