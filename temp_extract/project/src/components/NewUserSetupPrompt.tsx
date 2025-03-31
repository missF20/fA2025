import React, { useState } from 'react';
import { Clock, CheckCircle, X, Mail } from 'lucide-react';

interface NewUserSetupPromptProps {
  onDismiss: () => void;
}

export function NewUserSetupPrompt({ onDismiss }: NewUserSetupPromptProps) {
  const [isVisible, setIsVisible] = useState(true);

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss();
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 right-4 max-w-md bg-white rounded-lg shadow-lg border border-blue-100 p-4 z-50 animate-fade-in">
      <div className="flex items-start">
        <div className="flex-shrink-0 bg-blue-50 rounded-full p-2 mr-3">
          <Clock className="h-6 w-6 text-blue-600" />
        </div>
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <h3 className="text-lg font-medium text-gray-900">Welcome to Dana AI!</h3>
            <button 
              onClick={handleDismiss}
              className="ml-4 text-gray-400 hover:text-gray-500"
            >
              <X size={20} />
            </button>
          </div>
          <p className="mt-1 text-sm text-gray-600">
            Thank you for signing up! Our technical team is currently setting up your workflow integrations.
          </p>
          <div className="mt-3 bg-blue-50 rounded-lg p-3">
            <div className="flex items-center">
              <CheckCircle size={16} className="text-blue-600 mr-2" />
              <p className="text-sm text-blue-700">
                Setup will be completed within 24 hours
              </p>
            </div>
          </div>
          <div className="mt-3 bg-green-50 rounded-lg p-3">
            <div className="flex items-center">
              <Mail size={16} className="text-green-600 mr-2" />
              <p className="text-sm text-green-700">
                A welcome email has been sent to your inbox
              </p>
            </div>
          </div>
          <p className="mt-3 text-xs text-gray-500">
            You can explore the dashboard in the meantime. We'll notify you once everything is ready.
          </p>
        </div>
      </div>
    </div>
  );
}