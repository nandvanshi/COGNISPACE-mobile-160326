import React, { useState, useEffect, useRef } from 'react';
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
import { Send, MessageCircle, Plus, User, Settings, Shield, AlertTriangle } from 'lucide-react';
import { formatDate, formatTime, formatDateTime, toIST } from '../utils/formatUtils';

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
  const [mobileShowMessages, setMobileShowMessages] = useState(false); // Mobile: show messages panel
  const messagesEndRef = useRef(null);
  
  const isClient = user?.role === 'client';

  useEffect(() => {
    fetchData();
    // Poll for new messages every 10 seconds
    const interval = setInterval(fetchConversations, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.user_id);
    }
  }, [selectedConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchData = async () => {
    try {
      const [convsRes, contactsRes] = await Promise.all([
        axios.get(`${API}/messages/conversations`),
        axios.get(`${API}/messaging-contacts`),
      ]);
      setConversations(convsRes.data);
      setContacts(contactsRes.data);
      
      // Auto-select conversation for client (they usually have only one therapist)
      if (user?.role === 'client' && convsRes.data.length > 0 && !selectedConversation) {
        setSelectedConversation(convsRes.data[0]);
      }
      
      // If therapist, load messaging settings for all clients
      if (user?.role === 'therapist') {
        const clients = contactsRes.data.filter(c => c.type === 'client');
        const settings = {};
        for (const client of clients) {
          try {
            const res = await axios.get(`${API}/clients/${client.id}/messaging-status`);
            settings[client.id] = res.data.messaging_enabled;
          } catch (e) {
            settings[client.id] = true; // Default to enabled
          }
        }
        setClientMessagingSettings(settings);
      }
    } catch (error) {
      toast.error('Failed to load messaging data');
    } finally {
      setLoading(false);
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API}/messages/conversations`);
      setConversations(response.data);
    } catch (error) {
      // Silent fail for polling
    }
  };

  const fetchMessages = async (userId) => {
    try {
      const response = await axios.get(`${API}/messages/${userId}`);
      setMessages(response.data);
    } catch (error) {
      toast.error('Failed to load messages');
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
      toast.error(error.response?.data?.detail || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleStartNewConversation = async () => {
    if (!selectedContact) {
      toast.error('Please select a contact');
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
      setClientMessagingSettings(prev => ({
        ...prev,
        [clientId]: enabled,
      }));
      toast.success(`Messaging ${enabled ? 'enabled' : 'disabled'}`);
      // Refresh contacts list to reflect the change
      const contactsRes = await axios.get(`${API}/messaging-contacts`);
      setContacts(contactsRes.data);
    } catch (error) {
      toast.error('Failed to update messaging settings');
    }
  };

  const getUnreadTotal = () => {
    return conversations.reduce((sum, conv) => sum + (conv.unread_count || 0), 0);
  };

  const getContactsNotInConversations = () => {
    const conversationUserIds = conversations.map(c => c.user_id);
    return contacts.filter(c => !conversationUserIds.includes(c.id));
  };

  if (loading) {
    return <div className="text-center py-12">Loading messages...</div>;
  }

  // Client Mobile View - Full Screen Messages
  if (isClient) {
    const therapistName = conversations[0]?.user_name || contacts[0]?.full_name || 'Your Therapist';
    
    return (
      <div data-testid="messaging" className="h-[calc(100vh-120px)] flex flex-col">
        {/* Header - Compact for mobile */}
        <div className="mb-4 flex items-center justify-between px-2">
          <div>
            <h2 className="text-2xl md:text-4xl font-serif text-primary">Messages</h2>
            <p className="text-sm text-muted-foreground">Chat with your therapist</p>
          </div>
        </div>

        {contacts.length === 0 ? (
          <Card className="flex-1 flex items-center justify-center bg-white/70 backdrop-blur-xl border border-border/40">
            <div className="text-center p-8">
              <MessageCircle size={48} className="mx-auto text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground">You are not assigned to a therapist yet.</p>
            </div>
          </Card>
        ) : (
          <Card className="flex-1 flex flex-col bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl overflow-hidden">
            {/* Therapist Header - Always show if contacts exist */}
            <div className="border-b border-border p-4 bg-primary/5">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <User size={24} className="text-primary" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-primary">{therapistName}</h3>
                  <p className="text-xs text-muted-foreground">Therapist</p>
                </div>
              </div>
            </div>

            {/* Messages Area - Full Height */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3" data-testid="messages-container">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <MessageCircle size={40} className="mx-auto text-muted-foreground/30 mb-3" />
                    <p className="text-muted-foreground">No messages yet. Start the conversation!</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => {
                  const isSender = msg.sender_id === user?.id;
                  return (
                    <div
                      key={msg.id}
                      className={`flex ${isSender ? 'justify-end' : 'justify-start'}`}
                      data-testid={`message-${msg.id}`}
                    >
                      <div
                        className={`max-w-[80%] p-3 rounded-2xl ${
                          isSender
                            ? 'bg-primary text-white rounded-br-sm'
                            : 'bg-gray-100 text-foreground rounded-bl-sm'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                        <p className={`text-xs mt-1 ${isSender ? 'text-white/70' : 'text-muted-foreground'}`}>
                          {formatTime(msg.created_at)}
                          {msg.read && isSender && ' ✓'}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input - Fixed at Bottom */}
            {!isReadOnly ? (
              <div className="border-t border-border p-3 bg-white">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 rounded-full px-4"
                    disabled={sending || contacts.length === 0}
                    data-testid="message-input"
                  />
                  <Button
                    type="submit"
                    disabled={!newMessage.trim() || sending || contacts.length === 0}
                    className="rounded-full w-12 h-10 p-0 bg-primary hover:bg-primary-700"
                    data-testid="send-message-button"
                  >
                    <Send size={18} />
                  </Button>
                </form>
              </div>
            ) : (
              <div className="border-t border-border p-3 bg-warning/10">
                <p className="text-sm text-center text-warning">Messaging disabled - Contact your therapist</p>
              </div>
            )}
          </Card>
        )}
      </div>
    );
  }

  // Therapist View - Original Layout
  return (
    <div data-testid="messaging">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-4xl font-serif text-primary mb-2">Messages</h2>
          <p className="text-muted-foreground">Secure communication with your {user?.role === 'therapist' ? 'clients' : 'therapist'}</p>
        </div>
        <div className="flex gap-2">
          {user?.role === 'therapist' && !isReadOnly && (
            <Button
              variant="outline"
              onClick={() => setShowSettingsDialog(true)}
              data-testid="messaging-settings-button"
            >
              <Settings size={16} className="mr-2" />
              Client Settings
            </Button>
          )}
          {!isReadOnly && contacts.length > 0 && (
            <Button
              onClick={() => setShowNewConversationDialog(true)}
              className="bg-primary hover:bg-primary-700 rounded-full"
              data-testid="new-conversation-button"
            >
              <Plus size={20} className="mr-2" />
              New Message
            </Button>
          )}
        </div>
      </div>

      {/* Read-only warning */}
      {isReadOnly && (
        <Card className="p-4 mb-6 bg-warning/10 border-warning/30">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} className="text-warning" />
            <p className="text-sm">
              <strong>Read-only mode:</strong> Your subscription has expired. You can view messages but cannot send new ones.
            </p>
          </div>
        </Card>
      )}

      {/* No contacts message */}
      {contacts.length === 0 && (
        <Card className="p-8 text-center bg-white/70 backdrop-blur-xl border border-border/40">
          <MessageCircle size={48} className="mx-auto text-muted-foreground/30 mb-4" />
          <p className="text-muted-foreground">
            {user?.role === 'therapist' 
              ? 'You have no assigned clients to message yet.'
              : 'You are not assigned to a therapist yet.'}
          </p>
        </Card>
      )}

      {contacts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
          {/* Conversations List */}
          <Card className="lg:col-span-1 p-4 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl overflow-y-auto" data-testid="conversations-list">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-serif text-primary">Conversations</h3>
              {getUnreadTotal() > 0 && (
                <span className="bg-error text-white text-xs rounded-full px-2 py-0.5">
                  {getUnreadTotal()} unread
                </span>
              )}
            </div>
            
            {conversations.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-muted-foreground mb-4">No conversations yet</p>
                {!isReadOnly && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowNewConversationDialog(true)}
                  >
                    Start a conversation
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <div
                    key={conv.user_id}
                    onClick={() => setSelectedConversation(conv)}
                    className={`p-4 rounded-lg cursor-pointer transition-all ${
                      selectedConversation?.user_id === conv.user_id
                        ? 'bg-primary text-white shadow-md'
                        : 'bg-surface hover:bg-surface/80'
                    }`}
                    data-testid={`conversation-${conv.user_id}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          selectedConversation?.user_id === conv.user_id
                            ? 'bg-white/20'
                            : 'bg-primary/10'
                        }`}>
                          <User size={14} className={
                            selectedConversation?.user_id === conv.user_id
                              ? 'text-white'
                              : 'text-primary'
                          } />
                        </div>
                        <p className="font-medium truncate">{conv.user_name}</p>
                      </div>
                      {conv.unread_count > 0 && (
                        <span className={`text-xs rounded-full w-5 h-5 flex items-center justify-center ${
                          selectedConversation?.user_id === conv.user_id
                            ? 'bg-white text-primary'
                            : 'bg-error text-white'
                        }`}>
                          {conv.unread_count}
                        </span>
                      )}
                    </div>
                    <p className="text-sm opacity-80 truncate pl-10">{conv.last_message}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Messages Panel */}
          <Card className="lg:col-span-2 p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl flex flex-col h-[600px]" data-testid="messages-panel">
            {selectedConversation ? (
              <>
                <div className="border-b border-border pb-4 mb-4 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <User size={18} className="text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xl font-serif text-primary">{selectedConversation.user_name}</h3>
                    <p className="text-xs text-muted-foreground">
                      {user?.role === 'therapist' ? 'Client' : 'Your Therapist'}
                    </p>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 max-h-[400px]" data-testid="messages-container">
                  {messages.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <p>No messages yet. Start the conversation!</p>
                    </div>
                  ) : (
                    messages.map((msg) => {
                      const isSender = msg.sender_id !== selectedConversation.user_id;
                      return (
                        <div
                          key={msg.id}
                          className={`flex ${isSender ? 'justify-end' : 'justify-start'}`}
                          data-testid={`message-${msg.id}`}
                        >
                          <div
                            className={`max-w-[70%] p-3 rounded-2xl ${
                              isSender
                                ? 'bg-primary text-white rounded-br-md'
                                : 'bg-surface text-foreground rounded-bl-md'
                            }`}
                          >
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            <p className={`text-xs mt-1 ${isSender ? 'text-white/70' : 'text-muted-foreground'}`}>
                              {formatTime(msg.created_at)}
                              {msg.read && isSender && ' • Read'}
                            </p>
                          </div>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Send Message */}
                {!isReadOnly ? (
                  <form onSubmit={handleSendMessage} className="flex gap-2">
                    <Input
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Type your message..."
                      className="flex-1"
                      disabled={sending}
                      data-testid="message-input"
                    />
                    <Button 
                      type="submit" 
                      disabled={!newMessage.trim() || sending}
                      data-testid="send-message-button"
                    >
                      <Send size={20} />
                    </Button>
                  </form>
                ) : (
                  <div className="p-3 bg-muted rounded-lg text-center">
                    <p className="text-sm text-muted-foreground">Messaging disabled in read-only mode</p>
                  </div>
                )}
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center">
                <MessageCircle size={48} className="text-muted-foreground/30 mb-4" />
                <p className="text-muted-foreground mb-4">Select a conversation to start messaging</p>
                {!isReadOnly && getContactsNotInConversations().length > 0 && (
                  <Button 
                    variant="outline"
                    onClick={() => setShowNewConversationDialog(true)}
                  >
                    <Plus size={16} className="mr-2" />
                    Start New Conversation
                  </Button>
                )}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* HIPAA Notice */}
      <div className="mt-6 p-4 bg-info/10 border border-info/20 rounded-xl flex items-start gap-3">
        <Shield size={20} className="text-info shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-info font-medium">Secure In-App Messaging</p>
          <p className="text-xs text-info/80 mt-1">
            All messages are encrypted and stored securely. Messages are only between you and your {user?.role === 'therapist' ? 'assigned clients' : 'assigned therapist'}. 
            This is not for emergency communications - if you are in crisis, please call emergency services.
          </p>
        </div>
      </div>

      {/* New Conversation Dialog */}
      <Dialog open={showNewConversationDialog} onOpenChange={setShowNewConversationDialog}>
        <DialogContent data-testid="new-conversation-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">New Message</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Select {user?.role === 'therapist' ? 'Client' : 'Contact'}</Label>
              <Select value={selectedContact} onValueChange={setSelectedContact}>
                <SelectTrigger className="mt-1" data-testid="contact-select">
                  <SelectValue placeholder="Choose a contact" />
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
              <Button 
                onClick={handleStartNewConversation} 
                className="flex-1"
                data-testid="start-conversation-button"
              >
                Start Conversation
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowNewConversationDialog(false);
                  setSelectedContact('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Client Messaging Settings Dialog (Therapist only) */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent className="max-w-md" data-testid="messaging-settings-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif text-primary">Client Messaging Settings</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground mb-4">
            Control which clients can send you messages. Disabled clients will not be able to message you.
          </p>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {contacts.filter(c => c.type === 'client').map((client) => (
              <div
                key={client.id}
                className="flex items-center justify-between p-3 bg-surface rounded-lg"
                data-testid={`client-setting-${client.id}`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <User size={14} className="text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{client.name}</p>
                    {client.display_id && (
                      <p className="text-xs text-muted-foreground">{client.display_id}</p>
                    )}
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
              <p className="text-center text-muted-foreground py-4">
                No clients assigned yet
              </p>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Messaging;
