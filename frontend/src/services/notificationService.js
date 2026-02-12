/**
 * PWA Notification Service
 * Handles in-app notifications with sound and badge support
 */

class NotificationService {
  constructor() {
    this.audio = null;
    this.soundEnabled = this.getSoundPreference();
    this.permission = Notification.permission;
    this.setupServiceWorkerListener();
  }

  // Get sound preference from localStorage
  getSoundPreference() {
    const pref = localStorage.getItem('notification-sound-enabled');
    return pref === null ? true : pref === 'true';
  }

  // Set sound preference
  setSoundPreference(enabled) {
    this.soundEnabled = enabled;
    localStorage.setItem('notification-sound-enabled', String(enabled));
  }

  // Initialize audio element
  initAudio() {
    if (!this.audio) {
      this.audio = new Audio('/notification-sound.mp3');
      this.audio.volume = 0.5;
      // Preload
      this.audio.load();
    }
  }

  // Play notification sound
  async playSound() {
    if (!this.soundEnabled) return;
    
    try {
      this.initAudio();
      this.audio.currentTime = 0;
      await this.audio.play();
    } catch (error) {
      console.warn('Could not play notification sound:', error);
    }
  }

  // Request notification permission
  async requestPermission() {
    if (!('Notification' in window)) {
      console.warn('Notifications not supported');
      return false;
    }

    if (Notification.permission === 'granted') {
      this.permission = 'granted';
      return true;
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      return permission === 'granted';
    }

    return false;
  }

  // Setup service worker message listener
  setupServiceWorkerListener() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data?.type === 'PLAY_NOTIFICATION_SOUND') {
          this.playSound();
        }
        if (event.data?.type === 'NOTIFICATION_CLICKED') {
          // Handle notification click - could navigate to URL
          if (event.data.url && window.location.pathname !== event.data.url) {
            window.location.href = event.data.url;
          }
        }
      });
    }
  }

  // Update app badge count
  async updateBadge(count) {
    // Try using Badging API directly
    if ('setAppBadge' in navigator) {
      try {
        if (count > 0) {
          await navigator.setAppBadge(count);
        } else {
          await navigator.clearAppBadge();
        }
      } catch (error) {
        console.warn('Badge API error:', error);
      }
    }

    // Also notify service worker
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'UPDATE_BADGE',
        count: count
      });
    }
  }

  // Clear badge
  async clearBadge() {
    await this.updateBadge(0);
  }

  // Show in-app notification (browser notification)
  async showNotification(title, options = {}) {
    const hasPermission = await this.requestPermission();
    
    if (!hasPermission) {
      console.warn('Notification permission not granted');
      // Still play sound if enabled
      if (options.playSound !== false) {
        this.playSound();
      }
      return false;
    }

    const defaultOptions = {
      icon: '/icons/icon-192x192.png',
      badge: '/icons/icon-72x72.png',
      vibrate: [200, 100, 200],
      tag: 'cognispace-notification',
      renotify: true,
      requireInteraction: false,
      silent: !this.soundEnabled,
      ...options
    };

    try {
      // If service worker is available, use it
      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        const registration = await navigator.serviceWorker.ready;
        await registration.showNotification(title, defaultOptions);
      } else {
        // Fallback to regular notification
        new Notification(title, defaultOptions);
      }

      // Play sound if enabled
      if (options.playSound !== false && this.soundEnabled) {
        this.playSound();
      }

      return true;
    } catch (error) {
      console.error('Error showing notification:', error);
      return false;
    }
  }

  // Show notification for new message
  showMessageNotification(senderName, messagePreview) {
    return this.showNotification(`New message from ${senderName}`, {
      body: messagePreview,
      tag: 'message-notification',
      data: { url: '/dashboard#messages' }
    });
  }

  // Show notification for appointment
  showAppointmentNotification(title, details, url = '/dashboard#appointments') {
    return this.showNotification(title, {
      body: details,
      tag: 'appointment-notification',
      data: { url }
    });
  }

  // Show notification for payment
  showPaymentNotification(amount, clientName) {
    return this.showNotification('Payment Received', {
      body: `₹${amount} from ${clientName}`,
      tag: 'payment-notification',
      data: { url: '/dashboard#payments' }
    });
  }
}

// Singleton instance
const notificationService = new NotificationService();

export default notificationService;
export { NotificationService };
