import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { Facebook, Instagram, MessageCircle, Loader2, ArrowRight } from 'lucide-react';
import type { SubscriptionTier } from '../types';
import { PaymentProcessor } from './PaymentProcessor';

interface SubscriptionTierSelectorProps {
  onComplete: (tierId: string) => Promise<void>;
  onSkip: () => void;
}

export function SubscriptionTierSelector({ onComplete, onSkip }: SubscriptionTierSelectorProps) {
  const [tiers, setTiers] = useState<SubscriptionTier[]>([]);
  const [selectedTierId, setSelectedTierId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPlatformConnect, setShowPlatformConnect] = useState(false);
  const [showPaymentProcessor, setShowPaymentProcessor] = useState(false);
  const [selectedTier, setSelectedTier] = useState<SubscriptionTier | null>(null);

  useEffect(() => {
    async function fetchSubscriptionTiers() {
      try {
        const { data, error } = await supabase
          .from('subscription_tiers')
          .select('*')
          .order('name');

        if (error) throw error;
        setTiers(data || []);
      } catch (err) {
        console.error('Error fetching subscription tiers:', err);
        setError('Failed to load subscription options');
      } finally {
        setLoading(false);
      }
    }

    fetchSubscriptionTiers();
  }, []);

  const handleSelectTier = (tier: SubscriptionTier) => {
    setSelectedTierId(tier.id);
    setSelectedTier(tier);
  };

  const handleContinue = async () => {
    if (!selectedTierId) {
      setError('Please select a subscription tier');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      // Show the payment processor instead of immediately completing
      setShowPaymentProcessor(true);
    } catch (err) {
      console.error('Error selecting subscription tier:', err);
      setError('Failed to select subscription tier');
    } finally {
      setSubmitting(false);
    }
  };
  
  const handlePaymentSuccess = async () => {
    // Complete the subscription process
    await onComplete(selectedTierId!);
    // Show the platform connection screen after payment
    setShowPaymentProcessor(false);
    setShowPlatformConnect(true);
  };
  
  const handlePaymentCancel = () => {
    // Go back to plan selection
    setShowPaymentProcessor(false);
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'facebook':
        return <Facebook size={24} className="text-blue-600" />;
      case 'instagram':
        return <Instagram size={24} className="text-pink-600" />;
      case 'whatsapp':
        return <MessageCircle size={24} className="text-green-600" />;
      default:
        return null;
    }
  };

  const renderPlatformConnection = () => {
    if (!selectedTier) return null;

    const availablePlatforms = selectedTier.platforms;
    const unavailablePlatforms = ['facebook', 'instagram', 'whatsapp'].filter(
      p => !availablePlatforms.includes(p)
    );

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-3xl w-full mx-4">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Connect Your Platforms</h2>
          <p className="text-gray-600 mb-6">
            Connect your social media accounts to start using Dana AI
          </p>

          <div className="space-y-4">
            {availablePlatforms.map(platform => (
              <div key={platform} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getPlatformIcon(platform)}
                    <div>
                      <h3 className="font-semibold text-gray-900 capitalize">{platform}</h3>
                      <p className="text-sm text-gray-500">Connect your {platform} account</p>
                    </div>
                  </div>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
                    Connect
                    <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            ))}

            {unavailablePlatforms.map(platform => (
              <div key={platform} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getPlatformIcon(platform)}
                    <div>
                      <h3 className="font-semibold text-gray-900 capitalize">{platform}</h3>
                      <p className="text-sm text-gray-500">Not available in current plan</p>
                    </div>
                  </div>
                  <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2">
                    Upgrade to Connect
                    <ArrowRight size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={onSkip}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              I'll connect later
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-3xl w-full mx-4">
          <div className="flex justify-center">
            <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  if (showPaymentProcessor && selectedTierId) {
    return (
      <PaymentProcessor 
        subscriptionTierId={selectedTierId} 
        onCancel={handlePaymentCancel}
        onSuccess={handlePaymentSuccess}
      />
    );
  }
  
  if (showPlatformConnect) {
    return renderPlatformConnection();
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-3xl w-full mx-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Your Dana AI Plan</h2>
        <p className="text-gray-600 mb-6">
          Select the platforms you want to connect with Dana AI. You can always upgrade later.
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {tiers.map((tier) => (
            <div
              key={tier.id}
              className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                selectedTierId === tier.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50/50'
              }`}
              onClick={() => handleSelectTier(tier)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-gray-900">{tier.name}</h3>
                  <div className="flex space-x-2 mt-2">
                    {tier.platforms.map(platform => (
                      <div key={platform} className="p-1">
                        {getPlatformIcon(platform)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mt-2">{tier.description}</p>
              
              <ul className="mt-3 space-y-1">
                {tier.features.map((feature, index) => (
                  <li key={index} className="flex items-start text-sm">
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="flex justify-between">
          <button
            onClick={onSkip}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            I'll decide later
          </button>
          <button
            onClick={handleContinue}
            disabled={!selectedTierId || submitting}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {submitting ? (
              <>
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
                Processing...
              </>
            ) : (
              'Continue'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}