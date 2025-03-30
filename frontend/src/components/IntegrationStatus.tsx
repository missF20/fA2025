
import React from 'react';
import { CheckCircle, XCircle, AlertCircle } from 'react-feather';

interface Props {
  status: 'active' | 'inactive' | 'pending' | 'error' | 'not_configured';
}

export default function IntegrationStatus({ status }: Props) {
  const getStatusDisplay = () => {
    switch (status) {
      case 'active':
        return {
          icon: <CheckCircle size={12} className="mr-1" />,
          text: 'Connected',
          className: 'text-green-600 bg-green-50'
        };
      case 'error':
        return {
          icon: <AlertCircle size={12} className="mr-1" />,
          text: 'Error',
          className: 'text-red-600 bg-red-50'
        };
      case 'pending':
        return {
          icon: <AlertCircle size={12} className="mr-1" />,
          text: 'Pending',
          className: 'text-yellow-600 bg-yellow-50'
        };
      default:
        return {
          icon: <XCircle size={12} className="mr-1" />,
          text: 'Disconnected',
          className: 'text-gray-600 bg-gray-50'
        };
    }
  };

  const { icon, text, className } = getStatusDisplay();

  return (
    <span className={`flex items-center text-xs px-2 py-1 rounded-full ${className}`}>
      {icon}
      {text}
    </span>
  );
}
