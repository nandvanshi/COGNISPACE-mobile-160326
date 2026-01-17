import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { Send, MessageCircle } from 'lucide-react';

const Messaging = () => {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.user_id);
    }
  }, [selectedConversation]);

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API}/messages`);
      setConversations(response.data);
    } catch (error) {
      toast.error('Failed to load conversations');
    } finally {
      setLoading(false);
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
    if (!newMessage.trim() || !selectedConversation) return;

    try {
      await axios.post(`${API}/messages`, {
        recipient_id: selectedConversation.user_id,
        content: newMessage,
      });
      setNewMessage('');
      fetchMessages(selectedConversation.user_id);
      fetchConversations();
    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading messages...</div>;
  }

  return (
    <div data-testid="messaging">
      <div className="mb-8">
        <h2 className="text-4xl font-serif text-primary mb-2">Messages</h2>
        <p className="text-muted-foreground">Secure communication with your clients</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
        {/* Conversations List */}
        <Card className="lg:col-span-1 p-4 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl overflow-y-auto" data-testid="conversations-list">
          <h3 className="text-lg font-serif text-primary mb-4">Conversations</h3>
          {conversations.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">No conversations yet</p>
          ) : (
            <div className="space-y-2">
              {conversations.map((conv) => (
                <div
                  key={conv.user_id}
                  onClick={() => setSelectedConversation(conv)}
                  className={`p-4 rounded-lg cursor-pointer transition-colors ${
                    selectedConversation?.user_id === conv.user_id
                      ? 'bg-primary text-white'
                      : 'bg-surface hover:bg-surface/80'
                  }`}
                  data-testid={`conversation-${conv.user_id}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-medium truncate">{conv.user_name}</p>
                    {conv.unread_count > 0 && (
                      <span className="bg-error text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-sm opacity-80 truncate">{conv.last_message}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Messages Panel */}
        <Card className="lg:col-span-2 p-6 bg-white/70 backdrop-blur-xl border border-border/40 rounded-xl flex flex-col" data-testid="messages-panel">
          {selectedConversation ? (
            <>
              <div className="border-b border-border pb-4 mb-4">
                <h3 className="text-xl font-serif text-primary">{selectedConversation.user_name}</h3>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4" data-testid="messages-container">
                {messages.map((msg) => {
                  const isSender = msg.sender_id !== selectedConversation.user_id;
                  return (
                    <div
                      key={msg.id}
                      className={`flex ${isSender ? 'justify-end' : 'justify-start'}`}
                      data-testid={`message-${msg.id}`}
                    >
                      <div
                        className={`max-w-[70%] p-3 rounded-lg ${
                          isSender
                            ? 'bg-primary text-white'
                            : 'bg-surface text-foreground'
                        }`}
                      >
                        <p className="text-sm">{msg.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {new Date(msg.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Send Message */}
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Input
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1"
                  data-testid="message-input"
                />
                <Button type="submit" data-testid="send-message-button">
                  <Send size={20} />
                </Button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center">
              <MessageCircle size={48} className="text-muted-foreground mb-4" />
              <p className="text-muted-foreground">Select a conversation to start messaging</p>
            </div>
          )}
        </Card>
      </div>

      {/* HIPAA Notice */}
      <div className="mt-6 p-4 bg-info/10 border border-info/20 rounded-xl">
        <p className="text-sm text-info">
          <strong>Secure Messaging:</strong> All messages are encrypted and stored securely.
          Not for emergency communications.
        </p>
      </div>
    </div>
  );
};

export default Messaging;
