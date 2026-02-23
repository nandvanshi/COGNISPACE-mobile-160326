import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { toast } from 'sonner';
import { 
  Send, MessageCircle, Plus, User, Settings, AlertTriangle, 
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
  
  const isClient = user?.role === 'client';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.user_id);
      setMobileView('chat');
    }
  }, [selectedConversation?.user_id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  const fetchMessages = async (userId) => {
    try {
      const response = await axios.get(`${API}/messages/${userId}`);
      setMessages(response.data);
    } catch (error) {
      console.error('Messages load error');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedConversation || sending) return;

    const messageToSend = newMessage.trim();
    setNewMessage('');
    setSending(true);
    
    try {
      await axios.post(`${API}/messages`, {
        recipient_id: selectedConversation.user_id,
        content: messageToSend,
      });
      await fetchMessages(selectedConversation.user_id);
      const convsRes = await axios.get(`${API}/messages/conversations`);
      setConversations(convsRes.data);
    } catch (error) {
      setNewMessage(messageToSend);
      toast.error(error.response?.data?.detail || 'Message भेजने में error');
    } finally {
      setSending(false);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    try {
      await axios.delete(`${API}/messages/${messageId}`);
      toast.success('Message delete हो गया');
      await fetchMessages(selectedConversation.user_id);
    } catch (error) {
      toast.error('Delete करने में error');
    }
  };

  const handleStartNewConversation = () => {
    if (!selectedContact) {
      toast.error('Contact select करें');
      return;
    }
    const contact = contacts.find(c => c.id === selectedContact);
    if (contact) {
      setSelectedConversation({ user_id: contact.id, user_name: contact.name });
      setShowNewConversationDialog(false);
      setSelectedContact('');
    }
  };

  const handleToggleMessaging = async (clientId, enabled) => {
    try {
      await axios.post(`${API}/clients/${clientId}/messaging-status`, { messaging_enabled: enabled });
      setClientMessagingSettings(prev => ({ ...prev, [clientId]: enabled }));
      toast.success(enabled ? 'Messaging enabled' : 'Messaging disabled');
    } catch (error) {
      toast.error('Setting update करने में error');
    }
  };

  const getContactsNotInConversations = () => {
    const conversationUserIds = conversations.map(c => c.user_id);
    return contacts.filter(c => !conversationUserIds.includes(c.id));
  };

  const filteredConversations = conversations.filter(conv =>
    conv.user_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="h-[600px]" data-testid="messaging">
      <div className="flex gap-4 h-full">
        
        {/* Conversations List - Hidden on mobile when chat selected */}
        <div className={`w-80 flex-shrink-0 flex flex-col bg-white rounded-xl border overflow-hidden ${mobileView === 'chat' ? 'hidden md:flex' : 'flex'}`}>
          <div className="p-4 border-b">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">Messages</h2>
              <div className="flex gap-2">
                {!isClient && !isReadOnly && (
                  <button onClick={() => setShowSettingsDialog(true)} className="p-2 hover:bg-gray-100 rounded-full">
                    <Settings size={18} />
                  </button>
                )}
                {!isReadOnly && getContactsNotInConversations().length > 0 && (
                  <button onClick={() => setShowNewConversationDialog(true)} className="p-2 bg-primary/10 text-primary hover:bg-primary/20 rounded-full">
                    <Plus size={18} />
                  </button>
                )}
              </div>
            </div>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="w-full pl-9 pr-3 py-2 rounded-full bg-gray-50 border text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {filteredConversations.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <MessageCircle size={40} className="mx-auto mb-3 opacity-50" />
                <p>No conversations</p>
              </div>
            ) : (
              filteredConversations.map((conv) => (
                <div
                  key={conv.user_id}
                  onClick={() => setSelectedConversation(conv)}
                  className={`px-4 py-3 cursor-pointer border-b hover:bg-gray-50 ${
                    selectedConversation?.user_id === conv.user_id ? 'bg-primary/10 border-l-4 border-l-primary' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-medium">
                      {conv.user_name?.charAt(0)?.toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between">
                        <p className="font-medium truncate">{conv.user_name}</p>
                        {conv.unread_count > 0 && (
                          <span className="bg-primary text-white text-xs px-2 py-0.5 rounded-full">{conv.unread_count}</span>
                        )}
                      </div>
                      {conv.last_message && <p className="text-sm text-gray-500 truncate">{conv.last_message}</p>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className={`flex-1 flex flex-col bg-white rounded-xl border overflow-hidden ${mobileView === 'list' && !selectedConversation ? 'hidden md:flex' : 'flex'}`}>
          {selectedConversation ? (
            <>
              {/* Header */}
              <div className="px-4 py-3 border-b flex items-center gap-3 bg-gray-50 flex-shrink-0">
                <button onClick={() => { setMobileView('list'); setSelectedConversation(null); }} className="md:hidden p-2 -ml-2 hover:bg-gray-200 rounded-full">
                  <ArrowLeft size={20} />
                </button>
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-medium">
                  {selectedConversation.user_name?.charAt(0)?.toUpperCase()}
                </div>
                <div>
                  <h3 className="font-semibold">{selectedConversation.user_name}</h3>
                  <p className="text-xs text-gray-500">{isClient ? 'Therapist' : 'Client'}</p>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 bg-gray-50/50">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <MessageCircle size={48} className="mx-auto mb-3 text-gray-300" />
                      <p className="text-gray-500">Start the conversation!</p>
                    </div>
                  </div>
                ) : (
                  messages.map((msg) => {
                    const isSender = msg.sender_id !== selectedConversation.user_id;
                    return (
                      <div key={msg.id} className={`flex mb-3 group ${isSender ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[70%] relative ${isSender ? 'order-2' : 'order-1'}`}>
                          <div className={`px-4 py-2 rounded-2xl ${
                            isSender ? 'bg-primary text-white rounded-br-sm' : 'bg-white border rounded-bl-sm'
                          }`}>
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            <div className={`flex items-center gap-1 mt-1 text-[10px] ${isSender ? 'text-white/70 justify-end' : 'text-gray-400'}`}>
                              <span>{formatDateTime(msg.created_at)}</span>
                              {isSender && (msg.is_read ? <CheckCheck size={12} /> : <Check size={12} />)}
                            </div>
                          </div>
                          {isSender && !isReadOnly && (
                            <button
                              onClick={() => handleDeleteMessage(msg.id)}
                              className="absolute -left-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 rounded-full hover:bg-red-100 text-gray-400 hover:text-red-500"
                            >
                              <Trash2 size={14} />
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input - Simple native input */}
              {!isReadOnly && (
                <div className="p-3 border-t bg-white flex-shrink-0">
                  <form onSubmit={handleSendMessage} className="flex gap-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Type a message..."
                      className="flex-1 px-4 py-2 rounded-full border bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:bg-white"
                      disabled={sending}
                    />
                    <button
                      type="submit"
                      disabled={!newMessage.trim() || sending}
                      className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center disabled:opacity-50 hover:bg-primary/90"
                    >
                      <Send size={18} />
                    </button>
                  </form>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageCircle size={48} className="mx-auto mb-3 text-gray-300" />
                <p className="text-gray-500">Select a conversation</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* New Conversation Dialog */}
      <Dialog open={showNewConversationDialog} onOpenChange={setShowNewConversationDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Conversation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div>
              <Label>Select Contact</Label>
              <Select value={selectedContact} onValueChange={setSelectedContact}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Choose..." />
                </SelectTrigger>
                <SelectContent>
                  {getContactsNotInConversations().map((contact) => (
                    <SelectItem key={contact.id} value={contact.id}>{contact.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowNewConversationDialog(false)}>Cancel</Button>
              <Button onClick={handleStartNewConversation}>Start</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Messaging Settings</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="p-3 bg-amber-50 rounded-lg text-sm text-amber-700 flex gap-2">
              <AlertTriangle size={18} className="shrink-0" />
              <p>Control which clients can message you.</p>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {contacts.map((contact) => (
                <div key={contact.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <User size={16} />
                    <span>{contact.name}</span>
                  </div>
                  <Switch
                    checked={clientMessagingSettings[contact.id] !== false}
                    onCheckedChange={(checked) => handleToggleMessaging(contact.id, checked)}
                  />
                </div>
              ))}
            </div>
            <Button className="w-full" onClick={() => setShowSettingsDialog(false)}>Done</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Messaging;
