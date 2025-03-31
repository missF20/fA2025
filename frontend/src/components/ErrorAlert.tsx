import { AlertTriangle, X } from 'lucide-react';
import { useState } from 'react';

interface ErrorAlertProps {
  message: string;
  details?: string;
  className?: string;
  onDismiss?: () => void;
}

export function ErrorAlert({ message, details, className = '', onDismiss }: ErrorAlertProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) {
    return null;
  }

  const handleDismiss = () => {
    setDismissed(true);
    if (onDismiss) {
      onDismiss();
    }
  };

  return (
    <div className={`bg-red-50 border-l-4 border-red-500 p-4 rounded mb-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <AlertTriangle className="h-5 w-5 text-red-500" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">{message}</h3>
          {details && <div className="mt-2 text-sm text-red-700">{details}</div>}
        </div>
        <button
          type="button"
          className="ml-auto flex-shrink-0 text-red-500 hover:text-red-700 focus:outline-none"
          onClick={handleDismiss}
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}