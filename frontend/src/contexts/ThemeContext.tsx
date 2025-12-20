// frontend/src/contexts/ThemeContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useMediaQuery } from 'react-responsive';

// Define types for theme context
interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  prefersDarkMode: boolean;
}

// Default context value with fallback functions
const defaultContext: ThemeContextType = {
  isDarkMode: false,
  toggleTheme: () => {},
  prefersDarkMode: false,
};

// Create the context
const ThemeContext = createContext<ThemeContextType>(defaultContext);

// Custom hook for consuming the theme context
export const useTheme = () => useContext(ThemeContext);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Use media query to detect system preference for dark mode
  const prefersDarkMode = useMediaQuery({ query: '(prefers-color-scheme: dark)' });
  
  // Initialize state based on localStorage or system preference
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    try {
      const savedTheme = localStorage.getItem('darkMode');
      return savedTheme ? JSON.parse(savedTheme) : prefersDarkMode;
    } catch (error) {
      console.error('Error reading theme from localStorage:', error);
      return prefersDarkMode;
    }
  });

  // Sync theme preference to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
      // Apply theme class to document root for global styling
      document.documentElement.classList.toggle('dark', isDarkMode);
    } catch (error) {
      console.error('Error saving theme to localStorage:', error);
    }
  }, [isDarkMode]);

  // Toggle between light and dark mode
  const toggleTheme = () => {
    setIsDarkMode((prevMode) => !prevMode);
  };

  // Provide context value to children components
  const contextValue: ThemeContextType = {
    isDarkMode,
    toggleTheme,
    prefersDarkMode,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Apply theme styles based on context (can be used in components)
export const applyThemeStyles = (isDarkMode: boolean) => ({
  backgroundColor: isDarkMode ? '#121212' : '#ffffff',
  color: isDarkMode ? '#ffffff' : '#333333',
  transition: 'background-color 0.3s ease-in-out, color 0.3s ease-in-out', // Smooth theme transition
});

// Helper function to get appropriate styles for skeleton loading based on theme
export const getSkeletonStyles = (isDarkMode: boolean) => ({
  background: isDarkMode 
    ? 'linear-gradient(90deg, #1e1e1e 0%, #2d2d2d 50%, #1e1e1e 100%)' 
    : 'linear-gradient(90deg, #f0f0f0 0%, #e0e0e0 50%, #f0f0f0 100%)',
  backgroundSize: '200% 100%',
  animation: 'skeleton-loading 1.5s ease-in-out infinite',
});