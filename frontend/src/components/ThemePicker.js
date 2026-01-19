import React from 'react';
import { Card } from './ui/card';
import { Check } from 'lucide-react';
import { themes } from '../config/themes';

const ThemePicker = ({ currentTheme, onThemeChange }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Object.entries(themes).map(([themeId, theme]) => {
        const isSelected = currentTheme === themeId;
        const primaryHsl = theme.colors['--primary'];
        const secondaryHsl = theme.colors['--secondary'];
        const bgHsl = theme.colors['--background'];
        
        return (
          <Card
            key={themeId}
            onClick={() => onThemeChange(themeId)}
            className={`p-4 cursor-pointer transition-all hover:shadow-md ${
              isSelected ? 'ring-2 ring-primary ring-offset-2' : 'hover:border-primary/50'
            }`}
            data-testid={`theme-${themeId}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h4 className="font-medium text-sm">{theme.name}</h4>
                <p className="text-xs text-muted-foreground">{theme.description}</p>
              </div>
              {isSelected && (
                <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                  <Check size={12} className="text-primary-foreground" />
                </div>
              )}
            </div>
            
            {/* Theme Preview */}
            <div 
              className="h-16 rounded-lg overflow-hidden border"
              style={{ backgroundColor: `hsl(${bgHsl})` }}
            >
              <div className="flex h-full">
                <div 
                  className="w-1/2 flex items-center justify-center"
                  style={{ backgroundColor: `hsl(${primaryHsl})` }}
                >
                  <div className="w-8 h-2 bg-white/80 rounded" />
                </div>
                <div 
                  className="w-1/2 flex items-center justify-center"
                  style={{ backgroundColor: `hsl(${secondaryHsl})` }}
                >
                  <div className="w-6 h-6 bg-white/20 rounded-full" />
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};

export default ThemePicker;
