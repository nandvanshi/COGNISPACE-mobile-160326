// Theme configuration with CSS variables
export const themes = {
  'calm-professional': {
    name: 'Calm Professional',
    description: 'Sage Green + Teal',
    colors: {
      '--primary': '142 45% 35%',
      '--primary-foreground': '0 0% 100%',
      '--secondary': '174 42% 40%',
      '--secondary-foreground': '0 0% 100%',
      '--background': '120 20% 98%',
      '--foreground': '142 20% 15%',
      '--card': '0 0% 100%',
      '--card-foreground': '142 20% 15%',
      '--muted': '142 15% 92%',
      '--muted-foreground': '142 10% 45%',
      '--accent': '142 30% 90%',
      '--accent-foreground': '142 45% 25%',
      '--border': '142 15% 85%',
      '--input': '142 15% 85%',
      '--ring': '142 45% 35%',
      '--destructive': '0 84% 60%',
      '--destructive-foreground': '0 0% 100%',
    }
  },
  'soft-reassuring': {
    name: 'Soft & Reassuring',
    description: 'Blue + Lavender',
    colors: {
      '--primary': '221 83% 53%',
      '--primary-foreground': '0 0% 100%',
      '--secondary': '270 50% 65%',
      '--secondary-foreground': '0 0% 100%',
      '--background': '240 20% 98%',
      '--foreground': '221 30% 15%',
      '--card': '0 0% 100%',
      '--card-foreground': '221 30% 15%',
      '--muted': '240 15% 92%',
      '--muted-foreground': '221 10% 45%',
      '--accent': '270 40% 92%',
      '--accent-foreground': '270 50% 35%',
      '--border': '240 15% 85%',
      '--input': '240 15% 85%',
      '--ring': '221 83% 53%',
      '--destructive': '0 84% 60%',
      '--destructive-foreground': '0 0% 100%',
    }
  },
  'warm-approachable': {
    name: 'Warm & Approachable',
    description: 'Terracotta + Beige',
    colors: {
      '--primary': '16 60% 50%',
      '--primary-foreground': '0 0% 100%',
      '--secondary': '35 40% 55%',
      '--secondary-foreground': '0 0% 100%',
      '--background': '35 30% 97%',
      '--foreground': '16 30% 15%',
      '--card': '35 20% 99%',
      '--card-foreground': '16 30% 15%',
      '--muted': '35 20% 90%',
      '--muted-foreground': '16 15% 45%',
      '--accent': '35 30% 88%',
      '--accent-foreground': '16 60% 35%',
      '--border': '35 20% 82%',
      '--input': '35 20% 82%',
      '--ring': '16 60% 50%',
      '--destructive': '0 84% 60%',
      '--destructive-foreground': '0 0% 100%',
    }
  },
  'clean-saas': {
    name: 'Clean SaaS',
    description: 'Blue + Neutral Grey',
    colors: {
      '--primary': '217 91% 60%',
      '--primary-foreground': '0 0% 100%',
      '--secondary': '215 20% 55%',
      '--secondary-foreground': '0 0% 100%',
      '--background': '210 20% 98%',
      '--foreground': '215 25% 15%',
      '--card': '0 0% 100%',
      '--card-foreground': '215 25% 15%',
      '--muted': '215 15% 92%',
      '--muted-foreground': '215 15% 45%',
      '--accent': '217 50% 94%',
      '--accent-foreground': '217 91% 40%',
      '--border': '215 15% 85%',
      '--input': '215 15% 85%',
      '--ring': '217 91% 60%',
      '--destructive': '0 84% 60%',
      '--destructive-foreground': '0 0% 100%',
    }
  },
  'dark-calm': {
    name: 'Dark Calm',
    description: 'Low-contrast dark mode',
    colors: {
      '--primary': '142 40% 50%',
      '--primary-foreground': '0 0% 100%',
      '--secondary': '174 35% 45%',
      '--secondary-foreground': '0 0% 100%',
      '--background': '220 15% 12%',
      '--foreground': '210 20% 90%',
      '--card': '220 15% 15%',
      '--card-foreground': '210 20% 90%',
      '--muted': '220 15% 20%',
      '--muted-foreground': '210 15% 60%',
      '--accent': '142 25% 20%',
      '--accent-foreground': '142 40% 70%',
      '--border': '220 15% 25%',
      '--input': '220 15% 25%',
      '--ring': '142 40% 50%',
      '--destructive': '0 62% 50%',
      '--destructive-foreground': '0 0% 100%',
    }
  }
};

export const DEFAULT_THEME = 'calm-professional';

export const applyTheme = (themeId) => {
  const theme = themes[themeId] || themes[DEFAULT_THEME];
  const root = document.documentElement;
  
  Object.entries(theme.colors).forEach(([property, value]) => {
    root.style.setProperty(property, value);
  });
  
  // Store in localStorage for immediate access on reload
  localStorage.setItem('user-theme', themeId);
};

export const getStoredTheme = () => {
  return localStorage.getItem('user-theme') || DEFAULT_THEME;
};
