import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { CreditCard, CheckCircle, ArrowRight, Loader2 } from 'lucide-react';
import type { SubscriptionTier } from '../types';
import { PaymentProcessor } from './PaymentProcessor';

export function Subscriptions() {
  const [currentTier, setCurrentTier] = useState<SubscriptionTier | null>(null);
  const [availableTiers, setAvailableTiers] = useState<SubscriptionTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [upgrading, setUpgrading] = useState(false);
  const [showPaymentProcessor, setShowPaymentProcessor] = useState(false);
  const [selectedTierId, setSelectedTierId] = useState<string | null>(null);

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  async function fetchSubscriptionData() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      // Get user's current subscription tier
      const { data: profileData } = await supabase
        .from('profiles')
        .select('subscription_tier_id, subscription_tiers(*)')
        .eq('id', user.id)
        .single();

      if (profileData?.subscription_tiers) {
        setCurrentTier(profileData.subscription_tiers);
      }

      // Get available tiers
      const { data: tiers } = await supabase
        .from('subscription_tiers')
        .select('*')
        .order('price');

      if (tiers) {
        setAvailableTiers(tiers);
      }
    } catch (err) {
      console.error('Error fetching subscription data:', err);
      setError('Failed to load subscription information');
    } finally {
      setLoading(false);
    }
  }

  const handleUpgrade = (tierId: string) => {
    // Set the selected tier ID and show the payment processor
    setSelectedTierId(tierId);
    setShowPaymentProcessor(true);
  };
  
  const handlePaymentSuccess = async () => {
    try {
      // Payment was successful, refresh the subscription data
      await fetchSubscriptionData();
      setShowPaymentProcessor(false);
    } catch (err) {
      console.error('Error updating subscription after payment:', err);
      setError('Payment was successful, but we had trouble updating your subscription. Please refresh the page.');
    }
  };
  
  const handlePaymentCancel = () => {
    // User canceled the payment process
    setShowPaymentProcessor(false);
    setSelectedTierId(null);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
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

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 bg-blue-50 rounded-lg">
            <CreditCard className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Subscription Plans</h1>
            <p className="text-gray-500">Choose the perfect plan for your business</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {currentTier && (
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-6 mb-8">
            <h2 className="text-lg font-semibold text-blue-900 mb-2">Current Plan</h2>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xl font-bold text-blue-900">{currentTier.name}</p>
                <p className="text-blue-700">${currentTier.price}/month</p>
              </div>
              <div className="flex items-center gap-2 text-blue-700">
                <CheckCircle size={20} />
                <span>Active</span>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {availableTiers.map((tier) => (
            <div
              key={tier.id}
              className={`bg-white rounded-xl p-6 border ${
                currentTier?.id === tier.id
                  ? 'border-blue-500 ring-2 ring-blue-500 ring-opacity-50'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              <h3 className="text-xl font-bold text-gray-900 mb-2">{tier.name}</h3>
              <p className="text-3xl font-bold text-gray-900 mb-4">
                ${tier.price}
                <span className="text-base font-normal text-gray-500">/month</span>
              </p>
              
              <div className="space-y-4 mb-6">
                <h4 className="font-medium text-gray-900">Included Platforms:</h4>
                <div className="flex gap-2">
                  {tier.platforms.map((platform) => (
                    <span
                      key={platform}
                      className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                    >
                      {platform}
                    </span>
                  ))}
                </div>

                <h4 className="font-medium text-gray-900">Features:</h4>
                <ul className="space-y-2">
                  {tier.features.map((feature, index) => (
                    <li key={index} className="flex items-center text-gray-600">
                      <CheckCircle size={16} className="text-green-500 mr-2" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => handleUpgrade(tier.id)}
                disabled={currentTier?.id === tier.id || upgrading}
                className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentTier?.id === tier.id
                    ? 'bg-gray-100 text-gray-600 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {upgrading ? (
                  <Loader2 className="animate-spin h-5 w-5" />
                ) : currentTier?.id === tier.id ? (
                  'Current Plan'
                ) : (
                  <>
                    Upgrade
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}