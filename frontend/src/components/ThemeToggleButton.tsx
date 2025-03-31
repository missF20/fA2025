import { useContext } from 'react';
import { ThemeContext } from '../context/ThemeContext';
import { Sun, Moon } from 'lucide-react';

interface ThemeToggleButtonProps {
  className?: string;
}

export const ThemeToggleButton = ({ className = '' }: ThemeToggleButtonProps) => {
  const { isDarkMode, toggleTheme } = useContext(ThemeContext);

  return (
    <button
      className={`btn btn-sm ${isDarkMode ? 'btn-outline-light' : 'btn-outline-dark'} ${className}`}
      onClick={toggleTheme}
      aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDarkMode ? (
        <Sun size={16} className="me-1" />
      ) : (
        <Moon size={16} className="me-1" />
      )}
      {isDarkMode ? 'Light Mode' : 'Dark Mode'}
    </button>
  );
};