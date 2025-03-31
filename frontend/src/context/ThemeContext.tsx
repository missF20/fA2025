import { createContext, useState, useEffect, ReactNode } from 'react';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
}

const defaultThemeContext: ThemeContextType = {
  isDarkMode: false,
  toggleTheme: () => {},
};

export const ThemeContext = createContext<ThemeContextType>(defaultThemeContext);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  // Check for user preference or previously saved theme
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    // Check localStorage first
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme === 'dark';
    }
    // Otherwise check user's system preference
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute(
      'data-bs-theme',
      isDarkMode ? 'dark' : 'light'
    );
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};