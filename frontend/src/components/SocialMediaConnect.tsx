import React, { useState } from 'react';
import { Facebook, Instagram, MessageCircle } from 'lucide-react';
import { useToast } from '../hooks/useToast';

interface SocialMediaConnectProps {
  onConnected?: (platform: string) => void;
  onComplete?: () => void;
  availablePlatforms?: string[];
  subscription?: {
    id: string;
    name: string;
    price: number;
    tokenLimit: number;
    description: string;
  };
}

export function SocialMediaConnect({ 
  onConnected, 
  onComplete,
  availablePlatforms = ['facebook', 'instagram', 'whatsapp'],
  subscription
}: SocialMediaConnectProps) {
  const [isConnecting, setIsConnecting] = useState<string | null>(null);
  const { showToast } = useToast();

  // Function to handle initiating OAuth flow
  const handleConnect = (platform: string) => {
    setIsConnecting(platform);
    
    // For preview purposes, show a message instead of actually connecting
    // In the real app, this would open an OAuth window
    setTimeout(() => {
      setIsConnecting(null);
      showToast(`This is a preview. In the real app, you would be connected to ${platform}.`, 'info');
      
      if (onConnected) {
        onConnected(platform);
      }
      
      // Call the onComplete callback if provided (used by SocialMediaPreview)
      if (onComplete) {
        onComplete();
      }
    }, 1500);
  };

  // Generate OAuth URLs for each platform
  const getOAuthUrl = (platform: string): string => {
    const baseUrl = window.location.origin;
    const redirectUri = `${baseUrl}/api/integrations/${platform.toLowerCase()}/callback`;
    
    switch(platform) {
      case 'Facebook':
        return `https://www.facebook.com/v17.0/dialog/oauth?client_id=${process.env.REACT_APP_FACEBOOK_APP_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=pages_messaging,pages_show_list,pages_read_engagement&response_type=code`;
      
      case 'Instagram':
        return `https://api.instagram.com/oauth/authorize?client_id=${process.env.REACT_APP_INSTAGRAM_APP_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=user_profile,user_media&response_type=code`;
      
      case 'WhatsApp':
        // WhatsApp Business API requires business verification
        // This is typically done through the Facebook Business Manager
        return `https://www.facebook.com/v17.0/dialog/oauth?client_id=${process.env.REACT_APP_FACEBOOK_APP_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=whatsapp_business_management&response_type=code`;
      
      default:
        return '';
    }
  };

  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Connect Your Social Media</h3>
      <p className="text-gray-500 mb-6">Connect your accounts to receive and respond to messages through Dana AI.</p>
      
      <div className="space-y-4">
        {/* Facebook Connect Button */}
        <button
          onClick={() => handleConnect('Facebook')}
          disabled={isConnecting === 'Facebook'}
          className="w-full flex items-center justify-center gap-3 bg-blue-500 hover:bg-blue-600 text-white py-3 px-4 rounded-lg transition-colors"
        >
          <Facebook size={20} />
          {isConnecting === 'Facebook' ? 'Connecting...' : 'Connect Facebook Page'}
        </button>
        
        {/* Instagram Connect Button */}
        <button
          onClick={() => handleConnect('Instagram')}
          disabled={isConnecting === 'Instagram'}
          className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white py-3 px-4 rounded-lg transition-colors"
        >
          <Instagram size={20} />
          {isConnecting === 'Instagram' ? 'Connecting...' : 'Connect Instagram Business'}
        </button>
        
        {/* WhatsApp Connect Button */}
        <button
          onClick={() => handleConnect('WhatsApp')}
          disabled={isConnecting === 'WhatsApp'}
          className="w-full flex items-center justify-center gap-3 bg-green-500 hover:bg-green-600 text-white py-3 px-4 rounded-lg transition-colors"
        >
          <MessageCircle size={20} />
          {isConnecting === 'WhatsApp' ? 'Connecting...' : 'Connect WhatsApp Business'}
        </button>
      </div>
      
      <div className="mt-6 text-sm text-gray-500">
        <p>By connecting your accounts, you're allowing Dana AI to:</p>
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Receive messages sent to your business</li>
          <li>Send responses to your customers</li>
          <li>Access basic page/account information</li>
        </ul>
      </div>
    </div>
  );
}

export default SocialMediaConnect;