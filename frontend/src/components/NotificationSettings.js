import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { Bell, BellOff, Volume2, VolumeX, Smartphone } from 'lucide-react';
import notificationService from '../services/notificationService';

const NotificationSettings = () => {
  const [soundEnabled, setSoundEnabled] = useState(notificationService.getSoundPreference());
  const [notificationPermission, setNotificationPermission] = useState(Notification.permission);
  const [isPWA, setIsPWA] = useState(false);

  useEffect(() => {
    // Check if running as PWA
    const checkPWA = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      const isIOSPWA = window.navigator.standalone === true;
      setIsPWA(isStandalone || isIOSPWA);
    };
    checkPWA();
  }, []);

  const handleSoundToggle = (enabled) => {
    setSoundEnabled(enabled);
    notificationService.setSoundPreference(enabled);
    
    // Play test sound if enabling
    if (enabled) {
      notificationService.playSound();
      toast.success('Notification sound enabled');
    } else {
      toast.info('Notification sound disabled');
    }
  };

  const handleRequestPermission = async () => {
    const granted = await notificationService.requestPermission();
    setNotificationPermission(Notification.permission);
    
    if (granted) {
      toast.success('Notifications enabled!');
      // Show test notification
      await notificationService.showNotification('COGNISPACE', {
        body: 'Notifications are now enabled!',
        playSound: soundEnabled
      });
    } else {
      toast.error('Notification permission denied. Please enable in browser settings.');
    }
  };

  const handleTestNotification = async () => {
    const success = await notificationService.showNotification('Test Notification', {
      body: 'This is a test notification from COGNISPACE',
      playSound: soundEnabled
    });
    
    if (!success) {
      toast.error('Could not show notification. Check permissions.');
    }
  };

  const handleTestBadge = async () => {
    await notificationService.updateBadge(5);
    toast.success('Badge set to 5. Check app icon!');
    
    // Clear after 5 seconds
    setTimeout(() => {
      notificationService.clearBadge();
      toast.info('Badge cleared');
    }, 5000);
  };

  return (
    <Card className="w-full max-w-md" data-testid="notification-settings">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg font-serif text-primary">
          <Bell size={20} />
          Notification Settings
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Notification Permission */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {notificationPermission === 'granted' ? (
                <Bell className="text-green-600" size={20} />
              ) : (
                <BellOff className="text-gray-400" size={20} />
              )}
              <div>
                <Label className="font-medium">Push Notifications</Label>
                <p className="text-xs text-gray-500">
                  {notificationPermission === 'granted' 
                    ? 'Notifications are enabled'
                    : notificationPermission === 'denied'
                    ? 'Blocked - Enable in browser settings'
                    : 'Click to enable notifications'}
                </p>
              </div>
            </div>
            {notificationPermission !== 'granted' && notificationPermission !== 'denied' && (
              <Button 
                size="sm" 
                onClick={handleRequestPermission}
                data-testid="enable-notifications-btn"
              >
                Enable
              </Button>
            )}
            {notificationPermission === 'granted' && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                Active
              </span>
            )}
          </div>
        </div>

        {/* Sound Toggle */}
        <div className="flex items-center justify-between py-3 border-t">
          <div className="flex items-center gap-3">
            {soundEnabled ? (
              <Volume2 className="text-primary" size={20} />
            ) : (
              <VolumeX className="text-gray-400" size={20} />
            )}
            <div>
              <Label className="font-medium">Notification Sound</Label>
              <p className="text-xs text-gray-500">
                Play sound when notification arrives
              </p>
            </div>
          </div>
          <Switch
            checked={soundEnabled}
            onCheckedChange={handleSoundToggle}
            data-testid="sound-toggle"
          />
        </div>

        {/* PWA Badge Info */}
        {isPWA && (
          <div className="flex items-center gap-3 py-3 border-t">
            <Smartphone className="text-primary" size={20} />
            <div>
              <Label className="font-medium">App Badge</Label>
              <p className="text-xs text-gray-500">
                Unread count shows on app icon
              </p>
            </div>
          </div>
        )}

        {/* Test Buttons */}
        {notificationPermission === 'granted' && (
          <div className="flex gap-2 pt-4 border-t">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleTestNotification}
              className="flex-1"
              data-testid="test-notification-btn"
            >
              Test Notification
            </Button>
            {isPWA && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleTestBadge}
                className="flex-1"
                data-testid="test-badge-btn"
              >
                Test Badge
              </Button>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="bg-blue-50 rounded-lg p-3 mt-4">
          <p className="text-xs text-blue-700">
            <strong>💡 Tip:</strong> For best experience, install COGNISPACE as an app using your browser's "Add to Home Screen" option.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default NotificationSettings;
