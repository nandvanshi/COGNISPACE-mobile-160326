import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { X, Download, Smartphone } from 'lucide-react';

const InstallPWA = () => {
  const [installPrompt, setInstallPrompt] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
      return;
    }

    // Check if iOS
    const isIOSDevice = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    setIsIOS(isIOSDevice);

    // Listen for the beforeinstallprompt event (Android/Chrome)
    const handleBeforeInstall = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
      
      // Show prompt after a delay (don't show immediately)
      const hasSeenPrompt = localStorage.getItem('pwa-prompt-seen');
      const lastPrompt = localStorage.getItem('pwa-prompt-time');
      const daysSinceLastPrompt = lastPrompt ? (Date.now() - parseInt(lastPrompt)) / (1000 * 60 * 60 * 24) : 999;
      
      if (!hasSeenPrompt || daysSinceLastPrompt > 7) {
        setTimeout(() => setShowPrompt(true), 3000);
      }
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // Listen for successful installation
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setShowPrompt(false);
      setInstallPrompt(null);
    });

    // Show iOS prompt after delay
    if (isIOSDevice) {
      const hasSeenPrompt = localStorage.getItem('pwa-ios-prompt-seen');
      if (!hasSeenPrompt) {
        setTimeout(() => setShowPrompt(true), 5000);
      }
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;

    installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setIsInstalled(true);
    }
    
    setInstallPrompt(null);
    setShowPrompt(false);
    localStorage.setItem('pwa-prompt-seen', 'true');
    localStorage.setItem('pwa-prompt-time', Date.now().toString());
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-prompt-seen', 'true');
    localStorage.setItem('pwa-prompt-time', Date.now().toString());
    if (isIOS) {
      localStorage.setItem('pwa-ios-prompt-seen', 'true');
    }
  };

  if (isInstalled || !showPrompt) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:w-96 z-50 animate-in slide-in-from-bottom-4 duration-300">
      <div className="bg-white rounded-2xl shadow-2xl border border-border/50 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary to-primary/80 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <Smartphone size={20} />
            <span className="font-medium">Install TheraGenie</span>
          </div>
          <button 
            onClick={handleDismiss}
            className="text-white/80 hover:text-white p-1"
            aria-label="Dismiss"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {isIOS ? (
            // iOS Instructions
            <div className="space-y-3">
              <p className="text-sm text-foreground">
                Install TheraGenie on your iPhone for quick access:
              </p>
              <ol className="text-sm text-muted-foreground space-y-2">
                <li className="flex items-start gap-2">
                  <span className="bg-primary/10 text-primary w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium">1</span>
                  <span>Tap the <strong>Share</strong> button <span className="inline-block w-4 h-4 align-middle">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8M16 6l-4-4-4 4M12 2v13"/>
                    </svg>
                  </span> in Safari</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="bg-primary/10 text-primary w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium">2</span>
                  <span>Scroll down and tap <strong>"Add to Home Screen"</strong></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="bg-primary/10 text-primary w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium">3</span>
                  <span>Tap <strong>"Add"</strong> to install</span>
                </li>
              </ol>
              <Button 
                onClick={handleDismiss} 
                variant="outline" 
                className="w-full mt-2"
              >
                Got it
              </Button>
            </div>
          ) : (
            // Android/Desktop Install
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Add TheraGenie to your home screen for quick access, offline support, and a native app experience.
              </p>
              <div className="flex gap-2">
                <Button 
                  onClick={handleInstall} 
                  className="flex-1 gap-2"
                >
                  <Download size={16} />
                  Install App
                </Button>
                <Button 
                  onClick={handleDismiss} 
                  variant="outline"
                >
                  Not Now
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InstallPWA;
