import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '../App';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Palette, Loader2 } from 'lucide-react';
import ThemePicker from './ThemePicker';
import { applyTheme, getStoredTheme, DEFAULT_THEME } from '../config/themes';

const Settings = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const [currentTheme, setCurrentTheme] = useState(getStoredTheme());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen && user) {
      fetchUserTheme();
    }
  }, [isOpen, user]);

  const fetchUserTheme = async () => {
    try {
      const response = await axios.get(`${API}/user/preferences`);
      const theme = response.data?.theme || DEFAULT_THEME;
      setCurrentTheme(theme);
      applyTheme(theme);
    } catch (error) {
      // Use stored theme if API fails
      const stored = getStoredTheme();
      setCurrentTheme(stored);
    }
  };

  const handleThemeChange = async (themeId) => {
    // Apply immediately for instant feedback
    applyTheme(themeId);
    setCurrentTheme(themeId);
    
    // Save to backend
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
