import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Palette, Loader2, Bell, Mail, MessageCircle, AlertTriangle, Volume2, Smartphone, CalendarPlus } from 'lucide-react';
import ThemePicker from './ThemePicker';
import { applyTheme, getStoredTheme, DEFAULT_THEME } from '../config/themes';
import { Switch } from './ui/switch';
import notificationService from '../services/notificationService';

const Settings = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const [currentTheme, setCurrentTheme] = useState(getStoredTheme());
  const [saving, setSaving] = useState(false);
  
  // Notification settings state
  const [notificationEvents, setNotificationEvents] = useState([]);
  const [channelAvailability, setChannelAvailability] = useState({
    email_allowed: false,
    whatsapp_allowed: false,
    whatsapp_configured: false
  });
  const [loadingNotifications, setLoadingNotifications] = useState(false);
  const [savingNotification, setSavingNotification] = useState(null);
  
  // PWA Sound & Badge preferences
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [badgeEnabled, setBadgeEnabled] = useState(true);
  const [loadingPWAPrefs, setLoadingPWAPrefs] = useState(false);
  
  // Follow-up reminder settings
  const [followUpEmailEnabled, setFollowUpEmailEnabled] = useState(true);
  const [followUpWhatsAppEnabled, setFollowUpWhatsAppEnabled] = useState(false);
  const [savingFollowUp, setSavingFollowUp] = useState(false);

  useEffect(() => {
    if (isOpen && user) {
      fetchUserTheme();
      fetchPWAPreferences();
      if (user.role === 'therapist') {
        fetchNotificationSettings();
        fetchFollowUpSettings();
      }
    }
  }, [isOpen, user]);

  const fetchUserTheme = async () => {
    try {
      const response = await axios.get(`${API}/user/preferences`);
      const theme = response.data?.theme || DEFAULT_THEME;
      setCurrentTheme(theme);
      applyTheme(theme);
    } catch (error) {
      const stored = getStoredTheme();
      setCurrentTheme(stored);
    }
  };

  const fetchPWAPreferences = async () => {
    setLoadingPWAPrefs(true);
    try {
      const response = await axios.get(`${API}/notifications/preferences`);
      const { sound_enabled, badge_enabled } = response.data;
      setSoundEnabled(sound_enabled);
      setBadgeEnabled(badge_enabled);
      notificationService.setSoundPreference(sound_enabled);
      notificationService.setBadgePreference(badge_enabled);
    } catch (error) {
      console.error('Failed to fetch PWA preferences:', error);
      setSoundEnabled(notificationService.getSoundPreference());
      setBadgeEnabled(notificationService.getBadgePreference());
    } finally {
      setLoadingPWAPrefs(false);
    }
  };

  const handleSoundToggle = async (enabled) => {
    setSoundEnabled(enabled);
    notificationService.setSoundPreference(enabled);
    
    if (enabled) {
      notificationService.playSound();
      toast.success('Notification sound enabled');
    } else {
      toast.info('Notification sound disabled');
    }
    
    try {
      await axios.put(`${API}/notifications/preferences`, {
        sound_enabled: enabled,
        badge_enabled: badgeEnabled
      });
    } catch (error) {
      console.error('Failed to save sound preference:', error);
    }
  };

  const handleBadgeToggle = async (enabled) => {
    setBadgeEnabled(enabled);
    notificationService.setBadgePreference(enabled);
    
    if (!enabled) {
      notificationService.clearBadge();
      toast.info('Badge notifications disabled');
    } else {
      toast.success('Badge notifications enabled');
    }
    
    try {
      await axios.put(`${API}/notifications/preferences`, {
        sound_enabled: soundEnabled,
        badge_enabled: enabled
      });
    } catch (error) {
      console.error('Failed to save badge preference:', error);
    }
  };

  const fetchNotificationSettings = async () => {
    setLoadingNotifications(true);
    try {
      const [eventsRes, availabilityRes] = await Promise.all([
        axios.get(`${API}/notification-settings/events`),
        axios.get(`${API}/notification-settings/channel-availability`)
      ]);
      setNotificationEvents(eventsRes.data || []);
      setChannelAvailability(availabilityRes.data || {
        email_allowed: false,
        whatsapp_allowed: false,
        whatsapp_configured: false
      });
    } catch (error) {
      console.error('Failed to load notification settings:', error);
      toast.error('Failed to load notification settings');
    } finally {
      setLoadingNotifications(false);
    }
  };

  const fetchFollowUpSettings = async () => {
    try {
      const res = await axios.get(`${API}/follow-ups/settings`);
      setFollowUpEmailEnabled(res.data.followup_email_enabled ?? true);
      setFollowUpWhatsAppEnabled(res.data.followup_whatsapp_enabled ?? false);
    } catch (e) { /* ignore */ }
  };

  const handleFollowUpToggle = async (field, value) => {
    setSavingFollowUp(true);
    try {
      await axios.put(`${API}/follow-ups/settings`, { [field]: value });
      if (field === 'followup_email_enabled') setFollowUpEmailEnabled(value);
      if (field === 'followup_whatsapp_enabled') setFollowUpWhatsAppEnabled(value);
      toast.success('Follow-up reminder setting updated');
    } catch (e) {
      toast.error('Failed to update setting');
    } finally {
      setSavingFollowUp(false);
    }
  };

  const handleThemeChange = async (themeId) => {
    applyTheme(themeId);
    setCurrentTheme(themeId);
    
    setSaving(true);
    try {
      await axios.put(`${API}/user/preferences`, { theme: themeId });
      toast.success('Theme updated');
    } catch (error) {
      toast.error('Failed to save theme preference');
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationToggle = async (eventKey, channel, currentValue) => {
    const updateKey = `${eventKey}_${channel}`;
    setSavingNotification(updateKey);
    
    try {
      await axios.put(`${API}/notification-settings/preference`, {
        event_key: eventKey,
        [channel === 'email' ? 'send_email' : 'send_whatsapp']: !currentValue
      });
      
      // Update local state
      setNotificationEvents(prev => prev.map(event => {
        if (event.event_key === eventKey) {
          return {
            ...event,
            [channel === 'email' ? 'send_email' : 'send_whatsapp']: !currentValue
          };
        }
        return event;
      }));
      
      toast.success('Preference updated');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update preference');
    } finally {
      setSavingNotification(null);
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <SettingsIcon size={20} /> Settings
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Theme Section */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Palette size={18} className="text-primary" />
              <h3 className="font-medium">Appearance</h3>
              {saving && <Loader2 size={14} className="animate-spin text-muted-foreground" />}
            </div>
            
            <p className="text-sm text-muted-foreground mb-4">
              Choose a color theme for your interface
            </p>
            
            <ThemePicker 
              currentTheme={currentTheme} 
              onThemeChange={handleThemeChange} 
            />
          </Card>

          {/* PWA Sound & Badge Settings - For All Users */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <Bell size={18} className="text-primary" />
              <h3 className="font-medium">Sound & Badge Notifications</h3>
              {loadingPWAPrefs && <Loader2 size={14} className="animate-spin text-muted-foreground" />}
            </div>
            
            <p className="text-sm text-muted-foreground mb-4">
              Control notification sounds and app icon badges
            </p>

            <div className="space-y-4">
              {/* Sound Toggle */}
              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50">
                <div className="flex items-center gap-3">
                  <Volume2 size={18} className={soundEnabled ? "text-primary" : "text-gray-400"} />
                  <div>
                    <p className="text-sm font-medium">Notification Sound</p>
                    <p className="text-xs text-muted-foreground">Play sound when notification arrives</p>
                  </div>
                </div>
                <Switch
                  checked={soundEnabled}
                  onCheckedChange={handleSoundToggle}
                  data-testid="settings-sound-toggle"
                />
              </div>

              {/* Badge Toggle */}
              <div className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50">
                <div className="flex items-center gap-3">
                  <Smartphone size={18} className={badgeEnabled ? "text-primary" : "text-gray-400"} />
                  <div>
                    <p className="text-sm font-medium">App Badge Count</p>
                    <p className="text-xs text-muted-foreground">Show unread count on app icon (PWA)</p>
                  </div>
                </div>
                <Switch
                  checked={badgeEnabled}
                  onCheckedChange={handleBadgeToggle}
                  data-testid="settings-badge-toggle"
                />
              </div>
            </div>
          </Card>

          {/* Notification Settings Section - Only for Therapists */}
          {user?.role === 'therapist' && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <Bell size={18} className="text-primary" />
                <h3 className="font-medium">Notification Preferences</h3>
                {loadingNotifications && <Loader2 size={14} className="animate-spin text-muted-foreground" />}
              </div>
              
              <p className="text-sm text-muted-foreground mb-4">
                Configure which notifications your clients receive via Email and WhatsApp
              </p>

              {/* Channel Availability Info */}
              <div className="flex gap-4 mb-4 text-sm">
                <div className={`flex items-center gap-1 px-2 py-1 rounded ${channelAvailability.email_allowed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  <Mail size={14} />
                  <span>Email {channelAvailability.email_allowed ? 'Enabled' : 'Disabled'}</span>
                </div>
                <div className={`flex items-center gap-1 px-2 py-1 rounded ${channelAvailability.whatsapp_allowed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  <MessageCircle size={14} />
                  <span>WhatsApp {channelAvailability.whatsapp_allowed ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>

              {!channelAvailability.email_allowed && !channelAvailability.whatsapp_allowed && (
                <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg mb-4">
                  <AlertTriangle size={16} className="text-amber-600 mt-0.5" />
                  <div className="text-sm text-amber-800">
                    <p className="font-medium">Notifications not available</p>
                    <p className="text-amber-600">Upgrade your subscription plan to enable Email/WhatsApp notifications.</p>
                  </div>
                </div>
              )}

              {/* Notification Events List */}
              {notificationEvents.length > 0 && (
                <div className="space-y-3">
                  <div className="grid grid-cols-[1fr,80px,80px] gap-2 text-xs font-medium text-muted-foreground px-2">
                    <span>Event</span>
                    <span className="text-center">Email</span>
                    <span className="text-center">WhatsApp</span>
                  </div>
                  
                  {notificationEvents.map((event) => (
                    <div 
                      key={event.event_key} 
                      className="grid grid-cols-[1fr,80px,80px] gap-2 items-center p-2 rounded-lg hover:bg-muted/50"
                    >
                      <span className="text-sm">{event.event_name}</span>
                      
                      {/* Email Toggle */}
                      <div className="flex justify-center">
                        {event.supports_email ? (
                          <Switch
                            checked={event.send_email}
                            disabled={!event.email_allowed || savingNotification === `${event.event_key}_email`}
                            onCheckedChange={() => handleNotificationToggle(event.event_key, 'email', event.send_email)}
                            data-testid={`notification-email-${event.event_key}`}
                          />
                        ) : (
                          <span className="text-xs text-muted-foreground">N/A</span>
                        )}
                      </div>
                      
                      {/* WhatsApp Toggle */}
                      <div className="flex justify-center">
                        {event.supports_whatsapp ? (
                          <Switch
                            checked={event.send_whatsapp}
                            disabled={!event.whatsapp_allowed || savingNotification === `${event.event_key}_whatsapp`}
                            onCheckedChange={() => handleNotificationToggle(event.event_key, 'whatsapp', event.send_whatsapp)}
                            data-testid={`notification-whatsapp-${event.event_key}`}
                          />
                        ) : (
                          <span className="text-xs text-muted-foreground">N/A</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {loadingNotifications && notificationEvents.length === 0 && (
                <div className="text-center py-4 text-muted-foreground">
                  Loading notification settings...
                </div>
              )}
            </Card>
          )}

          {/* Follow-Up Reminder Settings - Only for Therapists */}
          {user?.role === 'therapist' && (
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-4">
                <CalendarPlus size={18} className="text-primary" />
                <h3 className="font-medium">Follow-Up Reminders</h3>
                {savingFollowUp && <Loader2 size={14} className="animate-spin text-muted-foreground" />}
              </div>
              
              <p className="text-sm text-muted-foreground mb-4">
                Automated reminders sent to clients who have pending follow-up sessions
              </p>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                  <div className="flex items-center gap-2">
                    <Mail size={16} className="text-blue-600" />
                    <div>
                      <p className="text-sm font-medium">Email Reminders</p>
                      <p className="text-xs text-muted-foreground">2 days before, same day, 1 week & 30 days after</p>
                    </div>
                  </div>
                  <Switch
                    checked={followUpEmailEnabled}
                    onCheckedChange={(v) => handleFollowUpToggle('followup_email_enabled', v)}
                    disabled={savingFollowUp}
                    data-testid="followup-email-toggle"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                  <div className="flex items-center gap-2">
                    <MessageCircle size={16} className="text-green-600" />
                    <div>
                      <p className="text-sm font-medium">WhatsApp Reminders</p>
                      <p className="text-xs text-muted-foreground">Template approval pending from Twilio</p>
                    </div>
                  </div>
                  <Switch
                    checked={followUpWhatsAppEnabled}
                    onCheckedChange={(v) => handleFollowUpToggle('followup_whatsapp_enabled', v)}
                    disabled={savingFollowUp}
                    data-testid="followup-whatsapp-toggle"
                  />
                </div>
              </div>
            </Card>
          )}
        </div>

        <div className="flex justify-end pt-4">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default Settings;
