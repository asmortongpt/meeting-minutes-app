import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface StealthContextType {
  stealthMode: boolean;
  toggleStealthMode: () => void;
  disguisedTitle: string;
  setDisguisedTitle: (title: string) => void;
  bossKeyPressed: boolean;
  activateBossKey: () => void;
  deactivateBossKey: () => void;
}

const StealthContext = createContext<StealthContextType | undefined>(undefined);

export const useStealthMode = () => {
  const context = useContext(StealthContext);
  if (!context) {
    throw new Error('useStealthMode must be used within StealthProvider');
  }
  return context;
};

interface StealthProviderProps {
  children: React.ReactNode;
}

export const StealthProvider: React.FC<StealthProviderProps> = ({ children }) => {
  const [stealthMode, setStealthMode] = useState(() => {
    const saved = localStorage.getItem('stealthMode');
    return saved ? JSON.parse(saved) : false;
  });

  const [disguisedTitle, setDisguisedTitle] = useState(() => {
    return localStorage.getItem('disguisedTitle') || 'Google Docs - Untitled Document';
  });

  const [bossKeyPressed, setBossKeyPressed] = useState(false);

  // Update document title based on stealth mode
  useEffect(() => {
    if (stealthMode) {
      document.title = disguisedTitle;
    } else {
      document.title = 'Meeting Minutes Pro - AI-Powered Meeting Management';
    }
  }, [stealthMode, disguisedTitle]);

  // Boss Key: Ctrl+Shift+H or Cmd+Shift+H
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Boss key combo
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'H') {
        e.preventDefault();
        setBossKeyPressed(prev => !prev);
      }

      // Toggle stealth mode: Ctrl+Shift+S or Cmd+Shift+S
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        toggleStealthMode();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Persist stealth mode preference
  useEffect(() => {
    localStorage.setItem('stealthMode', JSON.stringify(stealthMode));
  }, [stealthMode]);

  // Persist disguised title
  useEffect(() => {
    localStorage.setItem('disguisedTitle', disguisedTitle);
  }, [disguisedTitle]);

  const toggleStealthMode = useCallback(() => {
    setStealthMode(prev => !prev);
  }, []);

  const activateBossKey = useCallback(() => {
    setBossKeyPressed(true);
  }, []);

  const deactivateBossKey = useCallback(() => {
    setBossKeyPressed(false);
  }, []);

  const value: StealthContextType = {
    stealthMode,
    toggleStealthMode,
    disguisedTitle,
    setDisguisedTitle,
    bossKeyPressed,
    activateBossKey,
    deactivateBossKey,
  };

  return (
    <StealthContext.Provider value={value}>
      {children}
    </StealthContext.Provider>
  );
};
