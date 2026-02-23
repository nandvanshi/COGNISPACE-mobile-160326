import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { toast } from 'sonner';
import { 
  Send, MessageCircle, Plus, User, Settings, Shield, AlertTriangle, 
  Trash2, Check, CheckCheck, ArrowLeft, Search, X 
} from 'lucide-react';
import { formatDateTime } from '../utils/formatUtils';

const Messaging = ({ isReadOnly = false }) => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [showNewConversationDialog, setShowNewConversationDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [selectedContact, setSelectedContact] = useState('');
  const [clientMessagingSettings, setClientMessagingSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileView, setMobileView] = useState('list');
  const messagesEndRef = useRef(null);
  const selectedConvRef = useRef(null);
  
  const isClient = user?.role === 'client';

  // Scroll to bottom only when needed
  const scrollToBottom = useCallback((force = false) => {
    if (messagesEndRef.current && (isScrolledToBottom.current || force)) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  // Handle scroll to track if user scrolled up
  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    isScrolledToBottom.current = scrollHeight - scrollTop - clientHeight < 50;
  };

  // Track if user is typing to pause polling
  const selectedConvRef = useRef(null);
  
  // Keep ref updated
  useEffect(() => {
    selectedConvRef.current = selectedConversation;
  }, [selectedConversation]);

  // Initial data load
  useEffect(() => {
    fetchData();
  }, []);

  // Manual refresh only - no auto polling to avoid input issues
  const refreshMessages = useCallback(() => {
    fetchConversations();
    if (selectedConvRef.current) {
      fetchMessages(selectedConvRef.current.user_id, false);
    }
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.user_id, true);
      setMobileView('chat');
    }
  }, [selectedConversation?.user_id]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages.length, scrollToBottom]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [convsRes, contactsRes] = await Promise.all([
        axios.get(`${API}/messages/conversations`),
        axios.get(`${API}/messaging-contacts`),
      ]);
      setConversations(convsRes.data);
      setContacts(contactsRes.data);
      
      if (user?.role === 'client' && convsRes.data.length > 0 && !selectedConversation) {
        setSelectedConversation(convsRes.data[0]);
      }

      // Fetch messaging settings for clients (therapist only)
      if (user?.role === 'therapist') {
        const settings = {};
        for (const client of contactsRes.data) {
          try {
            const res = await axios.get(`${API}/clients/${client.id}/messaging-status`);
            settings[client.id] = res.data.messaging_enabled;
          } catch (e) {
            settings[client.id] = true;
          }
        }
        setClientMessagingSettings(settings);
      }
    } catch (error) {
      toast.error('Messages load करने में error');
    } finally {
      setLoading(false);
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API}/messages/conversations`);
      setConversations(response.data);
    } catch (error) {}
  };

  const fetchMessages = async (userId, forceScroll = false) => {
    try {
      const response = await axios.get(`${API}/messages/${userId}`);
      setMessages(response.data);
      if (forceScroll) {
        setTimeout(() => scrollToBottom(true), 100);
      }
    } catch (error) {
      console.error('Messages load error');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConversation || sending) return;

    const messageToSend = newMessage.trim();
    setNewMessage(''); // Clear immediately for better UX
    setSending(true);
    
    try {
      await axios.post(`${API}/messages`, {
        recipient_id: selectedConversation.user_id,
        content: messageToSend,
      });
      await fetchMessages(selectedConversation.user_id, true);
      await fetchConversations();
      inputRef.current?.focus();
    } catch (error) {
      setNewMessage(messageToSend); // Restore on error
      toast.error(error.response?.data?.detail || 'Message भेजने में error');
    } finally {
      setSending(false);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    try {
      await axios.delete(`${API}/messages/${messageId}`);
      toast.success('Message delete हो गया');
      await fetchMessages(selectedConversation.user_id, false);
      await fetchConversations();
    } catch (error) {
      toast.error('Delete करने में error');
    }
  };

  const handleStartNewConversation = async () => {
    if (!selectedContact) {
      toast.error('Contact select करें');
      return;
    }

    const contact = contacts.find(c => c.id === selectedContact);
    if (contact) {
      setSelectedConversation({
        user_id: contact.id,
        user_name: contact.name,
      });
      setShowNewConversationDialog(false);
      setSelectedContact('');
    }
  };

  const handleToggleMessaging = async (clientId, enabled) => {
    try {
      await axios.post(`${API}/clients/${clientId}/messaging-status`, {
        messaging_enabled: enabled
      });
      setClientMessagingSettings(prev => ({ ...prev, [clientId]: enabled }));
      toast.success(enabled ? 'Messaging enabled' : 'Messaging disabled');
    } catch (error) {
      toast.error('Setting update करने में error');
    }
  };

  const handleBackToList = () => {
    setMobileView('list');
    setSelectedConversation(null);
  };

  const getContactsNotInConversations = () => {
    const conversationUserIds = conversations.map(c => c.user_id);
    return contacts.filter(c => !conversationUserIds.includes(c.id));
  };

  const filteredConversations = conversations.filter(conv =>
    conv.user_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Message Bubble Component
  const MessageBubble = ({ msg, isSender }) => (
    <div className={`flex ${isSender ? 'justify-end' : 'justify-start'} mb-3 group`}>
      <div className={`max-w-[75%] relative ${isSender ? 'order-2' : 'order-1'}`}>
        <div
          className={`px-4 py-2.5 rounded-2xl shadow-sm ${
            isSender
              ? 'bg-gradient-to-br from-primary to-primary/90 text-white rounded-br-sm'
              : 'bg-white text-gray-900 rounded-bl-sm border border-gray-100'
          }`}
        >
          <p className="text-[15px] whitespace-pre-wrap break-words leading-relaxed">{msg.content}</p>
          <div className={`flex items-center gap-1.5 mt-1.5 ${isSender ? 'justify-end' : 'justify-start'}`}>
            <span className={`text-[10px] ${isSender ? 'text-white/70' : 'text-gray-400'}`}>
              {formatDateTime(msg.created_at)}
            </span>
            {isSender && (
              <span className="text-white/70">
                {msg.is_read ? <CheckCheck size={12} /> : <Check size={12} />}
              </span>
            )}
          </div>
        </div>
        
        {/* Delete button on hover */}
        {isSender && !isReadOnly && (
          <button
            onClick={() => handleDeleteMessage(msg.id)}
            className="absolute -left-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-full hover:bg-red-100 text-gray-400 hover:text-red-500"
            title="Delete"
          >
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );

  // Conversations List
  const ConversationsList = ({ fullWidth = false }) => (
    <div className={`${fullWidth ? 'w-full h-full' : 'w-80 hidden md:flex'} flex flex-col bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm`}>
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-primary/5 to-transparent">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Messages</h2>
          <div className="flex gap-2">
            {!isClient && !isReadOnly && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowSettingsDialog(true)}
                className="h-8 w-8 rounded-full"
              >
                <Settings size={16} />
              </Button>
            )}
            {!isReadOnly && getContactsNotInConversations().length > 0 && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowNewConversationDialog(true)}
                className="h-8 w-8 rounded-full bg-primary/10 text-primary hover:bg-primary/20"
              >
                <Plus size={16} />
              </Button>
            )}
          </div>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="pl-9 pr-8 rounded-full bg-gray-50 border-gray-200 h-9 text-sm"
          />
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {filteredConversations.length === 0 ? (
          <div className="text-center py-12 px-4">
            <MessageCircle size={40} className="mx-auto text-gray-300 mb-3" />
            <p className="text-sm text-gray-500">
              {searchQuery ? 'No results found' : 'No conversations yet'}
            </p>
            {!searchQuery && !isReadOnly && getContactsNotInConversations().length > 0 && (
              <Button
                variant="link"
                size="sm"
                onClick={() => setShowNewConversationDialog(true)}
                className="mt-2 text-primary"
              >
                Start a conversation
              </Button>
            )}
          </div>
        ) : (
          filteredConversations.map((conv) => {
            const isSelected = selectedConversation?.user_id === conv.user_id;
            return (
              <div
                key={conv.user_id}
                onClick={() => setSelectedConversation(conv)}
                className={`px-4 py-3 cursor-pointer border-b border-gray-50 transition-all ${
                  isSelected
                    ? 'bg-primary/10 border-l-4 border-l-primary'
                    : 'hover:bg-gray-50 active:bg-gray-100 border-l-4 border-l-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-11 h-11 rounded-full flex items-center justify-center shrink-0 ${
                    isSelected
                      ? 'bg-primary text-white'
                      : 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600'
                  }`}>
                    <span className="text-sm font-medium">
                      {conv.user_name?.charAt(0)?.toUpperCase() || <User size={18} />}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className={`font-medium truncate ${isSelected ? 'text-primary' : 'text-gray-900'}`}>
                        {conv.user_name}
                      </p>
                      {conv.unread_count > 0 && (
                        <span className="bg-primary text-white text-xs font-medium px-2 py-0.5 rounded-full min-w-[20px] text-center">
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                    {conv.last_message && (
                      <p className="text-sm text-gray-500 truncate mt-0.5">{conv.last_message}</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );

  // Chat Area
  const ChatArea = ({ showBack = false }) => (
    <div className="flex-1 flex flex-col bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
      {selectedConversation ? (
        <>
          {/* Header */}
          <div className="px-4 py-3 border-b flex items-center gap-3 bg-gradient-to-r from-gray-50 to-white shrink-0">
            {showBack && (
              <button 
                onClick={handleBackToList}
                className="p-2 -ml-2 rounded-full hover:bg-gray-100 transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-600" />
              </button>
            )}
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center">
              <span className="text-primary font-medium">
                {selectedConversation.user_name?.charAt(0)?.toUpperCase() || '?'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 truncate">{selectedConversation.user_name}</h3>
              <p className="text-xs text-gray-500">{isClient ? 'Therapist' : 'Client'}</p>
            </div>
          </div>

          {/* Messages */}
          <div 
            className="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-gray-50/50 to-gray-100/30"
            onScroll={handleScroll}
            style={{ minHeight: 0 }}
          >
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center bg-white/90 backdrop-blur rounded-2xl px-8 py-6 shadow-sm">
                  <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-primary/10 flex items-center justify-center">
                    <MessageCircle size={28} className="text-primary" />
                  </div>
                  <p className="text-gray-600 font-medium">Start the conversation!</p>
                  <p className="text-gray-400 text-sm mt-1">Send your first message</p>
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <MessageBubble 
                    key={msg.id} 
                    msg={msg} 
                    isSender={msg.sender_id !== selectedConversation.user_id}
                  />
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input */}
          {!isReadOnly ? (
            <div className="p-3 bg-white border-t shrink-0">
              <form onSubmit={handleSendMessage} className="flex gap-2 items-center">
                <input
                  ref={inputRef}
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1 rounded-full bg-gray-50 border border-gray-200 px-4 h-11 focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  disabled={sending}
                  autoComplete="off"
                />
                <Button
                  type="submit"
                  disabled={!newMessage.trim() || sending}
                  className="rounded-full w-11 h-11 p-0 bg-primary hover:bg-primary/90 shrink-0 shadow-md hover:shadow-lg transition-all disabled:opacity-50"
                >
                  <Send size={18} className={sending ? 'animate-pulse' : ''} />
                </Button>
              </form>
            </div>
          ) : (
            <div className="p-3 bg-gray-50 border-t shrink-0">
              <p className="text-sm text-center text-gray-400">Read-only mode</p>
            </div>
          )}
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-50 to-white">
          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center">
              <MessageCircle size={40} className="text-primary/60" />
            </div>
            <h3 className="text-gray-700 font-medium mb-1">Select a conversation</h3>
            <p className="text-gray-400 text-sm mb-4">Choose from your contacts to start messaging</p>
            {!isReadOnly && getContactsNotInConversations().length > 0 && (
              <Button
                onClick={() => setShowNewConversationDialog(true)}
                className="rounded-full"
              >
                <Plus size={16} className="mr-2" />
                New Conversation
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading messages...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-180px)] max-h-[700px]" data-testid="messaging">
      {/* Desktop Layout */}
      <div className="hidden md:flex gap-4 h-full">
        <ConversationsList />
        <ChatArea />
      </div>

      {/* Mobile Layout */}
      <div className="md:hidden h-full">
        {mobileView === 'list' ? (
          <ConversationsList fullWidth />
        ) : (
          <ChatArea showBack />
        )}
      </div>

      {/* New Conversation Dialog */}
      <Dialog open={showNewConversationDialog} onOpenChange={setShowNewConversationDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus size={20} className="text-primary" />
              New Conversation
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div>
              <Label>Select Contact</Label>
              <Select value={selectedContact} onValueChange={setSelectedContact}>
                <SelectTrigger className="mt-1.5">
                  <SelectValue placeholder="Choose a contact..." />
                </SelectTrigger>
                <SelectContent>
                  {getContactsNotInConversations().map((contact) => (
                    <SelectItem key={contact.id} value={contact.id}>
                      {contact.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowNewConversationDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleStartNewConversation} disabled={!selectedContact}>
                Start Chat
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog (Therapist Only) */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings size={20} className="text-primary" />
              Messaging Settings
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
              <div className="flex gap-2">
                <AlertTriangle size={18} className="text-amber-600 shrink-0 mt-0.5" />
                <p className="text-sm text-amber-700">
                  Control which clients can message you. Disabled clients won't be able to send messages.
                </p>
              </div>
            </div>
            
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {contacts.map((contact) => (
                <div key={contact.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                      <User size={16} className="text-primary" />
                    </div>
                    <span className="font-medium text-gray-900">{contact.name}</span>
                  </div>
                  <Switch
                    checked={clientMessagingSettings[contact.id] !== false}
                    onCheckedChange={(checked) => handleToggleMessaging(contact.id, checked)}
                  />
                </div>
              ))}
            </div>
            
            <Button className="w-full" onClick={() => setShowSettingsDialog(false)}>
              Done
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Messaging;
