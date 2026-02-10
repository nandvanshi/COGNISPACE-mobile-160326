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
  Trash2, MoreVertical, Check, CheckCheck, ArrowLeft, Search, X 
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
  const [showDeleteMenu, setShowDeleteMenu] = useState(null);
  const [deletingMessage, setDeletingMessage] = useState(null);
  const [mobileView, setMobileView] = useState('list'); // 'list' or 'chat'
  const messagesEndRef = useRef(null);
  const messageContainerRef = useRef(null);
  
  const isClient = user?.role === 'client';

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchConversations, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.user_id);
      setMobileView('chat'); // Switch to chat view on mobile when conversation selected
    }
  }, [selectedConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    const handleClickOutside = () => setShowDeleteMenu(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const fetchData = async () => {
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
      
      if (user?.role === 'therapist') {
        const clients = contactsRes.data.filter(c => c.type === 'client');
        const settings = {};
        for (const client of clients) {
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

  const fetchMessages = async (userId) => {
    try {
      const response = await axios.get(`${API}/messages/${userId}`);
      setMessages(response.data);
    } catch (error) {
      toast.error('Messages load करने में error');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConversation || sending) return;

    setSending(true);
    try {
      await axios.post(`${API}/messages`, {
        recipient_id: selectedConversation.user_id,
        content: newMessage.trim(),
      });
      setNewMessage('');
      await fetchMessages(selectedConversation.user_id);
      await fetchConversations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Message भेजने में error');
    } finally {
      setSending(false);
    }
  };

  const handleDeleteMessage = async (messageId, permanent = false) => {
    setDeletingMessage(messageId);
    try {
      const endpoint = permanent 
        ? `${API}/messages/${messageId}/permanent`
        : `${API}/messages/${messageId}`;
      
      await axios.delete(endpoint);
      toast.success('Message delete हो गया');
      await fetchMessages(selectedConversation.user_id);
      await fetchConversations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Delete करने में error');
    } finally {
      setDeletingMessage(null);
      setShowDeleteMenu(null);
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

  const handleToggleClientMessaging = async (clientId, enabled) => {
    try {
      await axios.put(`${API}/clients/${clientId}/messaging`, {
        messaging_enabled: enabled,
      });
      setClientMessagingSettings(prev => ({ ...prev, [clientId]: enabled }));
      toast.success(`Messaging ${enabled ? 'enabled' : 'disabled'}`);
      const contactsRes = await axios.get(`${API}/messaging-contacts`);
      setContacts(contactsRes.data);
    } catch (error) {
      toast.error('Settings update करने में error');
    }
  };

  const handleBackToList = () => {
    setMobileView('list');
    setSelectedConversation(null);
  };

  const getUnreadTotal = () => conversations.reduce((sum, conv) => sum + (conv.unread_count || 0), 0);

  const getContactsNotInConversations = () => {
    const conversationUserIds = conversations.map(c => c.user_id);
    return contacts.filter(c => !conversationUserIds.includes(c.id));
  };

  const filteredConversations = conversations.filter(conv => 
    conv.user_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="h-[calc(100vh-120px)] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Message Bubble Component
  const MessageBubble = ({ msg, isSender }) => {
    const isDeleting = deletingMessage === msg.id;
    
    return (
      <div
        className={`group flex ${isSender ? 'justify-end' : 'justify-start'} mb-2`}
        data-testid={`message-${msg.id}`}
      >
        <div className="relative max-w-[75%]">
          {isSender && !isReadOnly && (
            <div className={`absolute -left-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity`}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDeleteMenu(showDeleteMenu === msg.id ? null : msg.id);
                }}
                className="p-1.5 rounded-full hover:bg-gray-200 text-gray-500"
                data-testid={`delete-menu-${msg.id}`}
              >
                <MoreVertical size={16} />
              </button>
              
              {showDeleteMenu === msg.id && (
                <div className="absolute right-0 top-8 bg-white rounded-lg shadow-xl border z-50 py-1 min-w-[140px]">
                  <button
                    onClick={() => handleDeleteMessage(msg.id, false)}
                    disabled={isDeleting}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 text-red-600"
                  >
                    <Trash2 size={14} />
                    Delete
                  </button>
                  {user?.role === 'therapist' && (
                    <button
                      onClick={() => handleDeleteMessage(msg.id, true)}
                      disabled={isDeleting}
                      className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 text-red-700"
                    >
                      <Trash2 size={14} />
                      Permanently Delete
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
          
          <div
            className={`px-4 py-2.5 rounded-2xl ${
              isSender
                ? 'bg-primary text-white rounded-br-md'
                : 'bg-gray-100 text-gray-900 rounded-bl-md'
            } ${isDeleting ? 'opacity-50' : ''}`}
          >
            <p className="text-[15px] whitespace-pre-wrap break-words">{msg.content}</p>
            <div className={`flex items-center gap-1 mt-1 ${isSender ? 'justify-end' : 'justify-start'}`}>
              <span className={`text-[11px] ${isSender ? 'text-white/70' : 'text-gray-500'}`}>
                {formatDateTime(msg.created_at)}
              </span>
              {isSender && (
                <span className={`${isSender ? 'text-white/70' : 'text-gray-500'}`}>
                  {msg.is_read ? <CheckCheck size={14} /> : <Check size={14} />}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Conversations List Component
  const ConversationsList = ({ fullWidth = false }) => (
    <Card className={`${fullWidth ? 'w-full' : 'w-80 hidden md:flex'} flex-col bg-white rounded-xl overflow-hidden`} data-testid="conversations-list">
      {/* Search */}
      <div className="p-3 border-b">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            className="pl-9 pr-8 rounded-full bg-gray-100 border-0"
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
          <div className="text-center py-8 px-4">
            <p className="text-sm text-gray-500">
              {searchQuery ? 'कोई result नहीं' : 'कोई conversation नहीं'}
            </p>
            {!searchQuery && !isReadOnly && (
              <Button
                variant="link"
                size="sm"
                onClick={() => setShowNewConversationDialog(true)}
                className="mt-2"
              >
                Start a chat
              </Button>
            )}
          </div>
        ) : (
          filteredConversations.map((conv) => (
            <div
              key={conv.user_id}
              onClick={() => setSelectedConversation(conv)}
              className={`px-4 py-3 cursor-pointer border-b border-gray-50 transition-colors ${
                selectedConversation?.user_id === conv.user_id
                  ? 'bg-primary/10'
                  : 'hover:bg-gray-50 active:bg-gray-100'
              }`}
              data-testid={`conversation-${conv.user_id}`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
                  selectedConversation?.user_id === conv.user_id
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  <User size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium text-gray-900 truncate">{conv.user_name}</p>
                    {conv.unread_count > 0 && (
                      <span className="bg-primary text-white text-xs rounded-full w-5 h-5 flex items-center justify-center shrink-0">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 truncate">{conv.last_message}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );

  // Chat Panel Component
  const ChatPanel = ({ fullWidth = false, showBack = false }) => (
    <Card className={`${fullWidth ? 'w-full h-full' : 'flex-1 hidden md:flex'} flex flex-col bg-white rounded-xl overflow-hidden`} data-testid="messages-panel">
      {selectedConversation ? (
        <>
          {/* Chat Header - Fixed */}
          <div className="px-4 py-3 border-b flex items-center gap-3 bg-gray-50 shrink-0">
            {showBack && (
              <button 
                onClick={handleBackToList}
                className="p-2 -ml-2 rounded-full hover:bg-gray-200 active:bg-gray-300"
              >
                <ArrowLeft size={20} className="text-gray-600" />
              </button>
            )}
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <User size={18} className="text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 truncate">{selectedConversation.user_name}</h3>
              <p className="text-xs text-gray-500">Client</p>
            </div>
          </div>

          {/* Messages - Scrollable */}
          <div 
            ref={messageContainerRef}
            className="flex-1 overflow-y-auto p-4 bg-[#f0f2f5] min-h-0"
            data-testid="messages-container"
          >
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center bg-white/80 rounded-xl px-6 py-4">
                  <MessageCircle size={32} className="mx-auto text-gray-400 mb-2" />
                  <p className="text-gray-500 text-sm">बातचीत शुरू करें!</p>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <MessageBubble 
                  key={msg.id} 
                  msg={msg} 
                  isSender={msg.sender_id !== selectedConversation.user_id}
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input - Fixed at bottom */}
          {!isReadOnly ? (
            <div className="p-3 bg-white border-t shrink-0">
              <form onSubmit={handleSendMessage} className="flex gap-2 items-center">
                <Input
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Message लिखें..."
                  className="flex-1 rounded-full bg-gray-100 border-0 px-4"
                  disabled={sending}
                  data-testid="message-input"
                />
                <Button
                  type="submit"
                  disabled={!newMessage.trim() || sending}
                  className="rounded-full w-10 h-10 p-0 bg-primary hover:bg-primary/90 shrink-0"
                  data-testid="send-message-button"
                >
                  <Send size={18} />
                </Button>
              </form>
            </div>
          ) : (
            <div className="p-3 bg-gray-100 border-t shrink-0">
              <p className="text-sm text-center text-gray-500">Read-only mode</p>
            </div>
          )}
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <MessageCircle size={40} className="text-gray-400" />
            </div>
            <p className="text-gray-500 mb-4">Chat select करें</p>
            {!isReadOnly && getContactsNotInConversations().length > 0 && (
              <Button
                variant="outline"
                onClick={() => setShowNewConversationDialog(true)}
              >
                <Plus size={16} className="mr-2" />
                New Chat
              </Button>
            )}
          </div>
        </div>
      )}
    </Card>
  );

  // Client View - Full Screen Messenger
  if (isClient) {
    const therapistContact = contacts[0];
    const therapistName = conversations[0]?.user_name || therapistContact?.name || 'Your Therapist';
    const effectiveConversation = selectedConversation || (therapistContact ? {
      user_id: therapistContact.id,
      user_name: therapistContact.name
    } : null);

    return (
      <div data-testid="messaging" className="h-[calc(100vh-120px)] flex flex-col">
        {contacts.length === 0 ? (
          <Card className="flex-1 flex items-center justify-center bg-white/70">
            <div className="text-center p-8">
              <MessageCircle size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">अभी कोई therapist assign नहीं है</p>
            </div>
          </Card>
        ) : (
          <Card className="flex-1 flex flex-col bg-white rounded-2xl overflow-hidden shadow-lg min-h-0">
            {/* Header - Fixed */}
            <div className="px-4 py-3 bg-primary text-white flex items-center gap-3 shrink-0">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <User size={20} />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">{therapistName}</h3>
                <p className="text-xs text-white/70">Therapist</p>
              </div>
            </div>

            {/* Messages - Scrollable */}
            <div 
              ref={messageContainerRef}
              className="flex-1 overflow-y-auto p-4 bg-[#f0f2f5] min-h-0"
              data-testid="messages-container"
            >
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center bg-white/80 rounded-xl px-6 py-4">
                    <MessageCircle size={32} className="mx-auto text-gray-400 mb-2" />
                    <p className="text-gray-500 text-sm">बातचीत शुरू करें!</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <MessageBubble 
                    key={msg.id} 
                    msg={msg} 
                    isSender={msg.sender_id === user?.id} 
                  />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input - Fixed at bottom */}
            {!isReadOnly && therapistContact?.messaging_enabled !== false ? (
              <div className="p-3 bg-white border-t shrink-0">
                <form onSubmit={async (e) => {
                  e.preventDefault();
                  if (!newMessage.trim() || sending || !effectiveConversation) return;
                  setSending(true);
                  try {
                    await axios.post(`${API}/messages`, {
                      recipient_id: effectiveConversation.user_id,
                      content: newMessage.trim(),
                    });
                    setNewMessage('');
                    await fetchMessages(effectiveConversation.user_id);
                    await fetchConversations();
                  } catch (error) {
                    toast.error(error.response?.data?.detail || 'Message भेजने में error');
                  } finally {
                    setSending(false);
                  }
                }} className="flex gap-2 items-center">
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Message लिखें..."
                    className="flex-1 rounded-full bg-gray-100 border-0 px-4"
                    disabled={sending}
                    data-testid="message-input"
                  />
                  <Button
                    type="submit"
                    disabled={!newMessage.trim() || sending}
                    className="rounded-full w-10 h-10 p-0 bg-primary hover:bg-primary/90 shrink-0"
                    data-testid="send-message-button"
                  >
                    <Send size={18} />
                  </Button>
                </form>
              </div>
            ) : (
              <div className="p-3 bg-amber-50 border-t border-amber-200">
                <p className="text-sm text-center text-amber-700">Messaging disabled</p>
              </div>
            )}
          </Card>
        )}
      </div>
    );
  }

  // Therapist View - Responsive Layout
  return (
    <div data-testid="messaging" className="h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl md:text-3xl font-serif text-primary">Messages</h2>
          <p className="text-xs md:text-sm text-gray-500">Secure messaging with clients</p>
        </div>
        <div className="flex gap-2">
          {!isReadOnly && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSettingsDialog(true)}
              data-testid="messaging-settings-button"
              className="text-xs md:text-sm"
            >
              <Settings size={16} className="mr-1 md:mr-2" />
              <span className="hidden sm:inline">Settings</span>
            </Button>
          )}
          {!isReadOnly && contacts.length > 0 && (
            <Button
              onClick={() => setShowNewConversationDialog(true)}
              size="sm"
              className="bg-primary rounded-full text-xs md:text-sm"
              data-testid="new-conversation-button"
            >
              <Plus size={16} className="mr-1 md:mr-2" />
              <span className="hidden sm:inline">New Chat</span>
            </Button>
          )}
        </div>
      </div>

      {isReadOnly && (
        <Card className="p-3 mb-4 bg-amber-50 border-amber-200">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-600" />
            <p className="text-sm text-amber-700">Read-only mode: Subscription expired</p>
          </div>
        </Card>
      )}

      {contacts.length === 0 ? (
        <Card className="flex-1 flex items-center justify-center bg-white/70">
          <div className="text-center">
            <MessageCircle size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">कोई client assign नहीं है</p>
          </div>
        </Card>
      ) : (
        <>
          {/* Desktop View - Side by Side */}
          <div className="hidden md:flex flex-1 gap-4 min-h-0">
            <ConversationsList />
            <ChatPanel />
          </div>

          {/* Mobile View - One at a time */}
          <div className="flex md:hidden flex-1 min-h-0">
            {mobileView === 'list' ? (
              <ConversationsList fullWidth />
            ) : (
              <ChatPanel fullWidth showBack />
            )}
          </div>
        </>
      )}

      {/* Security Notice - Hidden on small mobile */}
      <div className="mt-4 p-2 md:p-3 bg-blue-50 border border-blue-100 rounded-xl flex items-start gap-2">
        <Shield size={16} className="text-blue-600 shrink-0 mt-0.5" />
        <p className="text-[10px] md:text-xs text-blue-700">
          Encrypted & secure messaging. Emergency के लिए इस platform का use न करें।
        </p>
      </div>

      {/* New Conversation Dialog */}
      <Dialog open={showNewConversationDialog} onOpenChange={setShowNewConversationDialog}>
        <DialogContent data-testid="new-conversation-dialog" className="mx-4 max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-xl font-serif text-primary">New Message</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Client Select करें</Label>
              <Select value={selectedContact} onValueChange={setSelectedContact}>
                <SelectTrigger className="mt-1" data-testid="contact-select">
                  <SelectValue placeholder="Contact चुनें" />
                </SelectTrigger>
                <SelectContent>
                  {contacts.map((contact) => (
                    <SelectItem key={contact.id} value={contact.id}>
                      {contact.name} {contact.display_id && `(${contact.display_id})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-3">
              <Button onClick={handleStartNewConversation} className="flex-1" data-testid="start-conversation-button">
                Start Chat
              </Button>
              <Button variant="outline" onClick={() => { setShowNewConversationDialog(false); setSelectedContact(''); }}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent className="mx-4 max-w-md" data-testid="messaging-settings-dialog">
          <DialogHeader>
            <DialogTitle className="text-xl font-serif text-primary">Messaging Settings</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-gray-500 mb-4">
            Client के messaging को enable/disable करें
          </p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {contacts.filter(c => c.type === 'client').map((client) => (
              <div
                key={client.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                data-testid={`client-setting-${client.id}`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <User size={14} className="text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{client.name}</p>
                    {client.display_id && <p className="text-xs text-gray-500 truncate">{client.display_id}</p>}
                  </div>
                </div>
                <Switch
                  checked={clientMessagingSettings[client.id] !== false}
                  onCheckedChange={(checked) => handleToggleClientMessaging(client.id, checked)}
                  data-testid={`toggle-messaging-${client.id}`}
                />
              </div>
            ))}
            {contacts.filter(c => c.type === 'client').length === 0 && (
              <p className="text-center text-gray-500 py-4">कोई client नहीं</p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Messaging;
