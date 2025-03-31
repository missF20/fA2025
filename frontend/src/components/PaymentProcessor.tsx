import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { Loader2, CheckCircle, AlertCircle, CreditCard } from 'lucide-react';
import type { SubscriptionTier } from '../types';
import { useNavigate } from 'react-router-dom';

interface PaymentProcessorProps {
  subscriptionTierId: string;
  onCancel: () => void;
  onSuccess: () => void;
}

export function PaymentProcessor({ 
  subscriptionTierId, 
  onCancel, 
  onSuccess 
}: PaymentProcessorProps) {
  const [tier, setTier] = useState<SubscriptionTier | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [orderId, setOrderId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchTierDetails() {
      try {
        const { data, error } = await supabase
          .from('subscription_tiers')
          .select('*')
          .eq('id', subscriptionTierId)
          .single();

        if (error) throw error;
        setTier(data);
      } catch (err) {
        console.error('Error fetching subscription tier:', err);
        setError('Failed to load subscription details');
      } finally {
        setLoading(false);
      }
    }

    fetchTierDetails();
  }, [subscriptionTierId]);

  const initiatePayment = async () => {
    try {
      setProcessing(true);
      setError(null);

      // Get API URL from window location
      const apiUrl = window.location.origin;

      // Get the current session
      const { data: { session } } = await supabase.auth.getSession();
      const accessToken = session?.access_token || '';
      
      // Call the payment initiation API
      const response = await fetch(`${apiUrl}/api/payments/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          subscription_tier_id: subscriptionTierId,
          billing_cycle: billingCycle
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to initiate payment');
      }

      // Store the payment URL and order ID
      setPaymentUrl(data.payment_url);
      setOrderId(data.order_id);

      // Redirect to the payment gateway
      window.location.href = data.payment_url;
    } catch (err) {
      console.error('Error initiating payment:', err);
      setError('Failed to initialize payment gateway. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const checkPaymentStatus = async () => {
    if (!orderId) return;

    try {
      setProcessing(true);
      
      // Get the current session
      const { data: { session } } = await supabase.auth.getSession();
      const accessToken = session?.access_token || '';
      
      // Call the payment status API
      const response = await fetch(`${window.location.origin}/api/payments/status/${orderId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      const data = await response.json();

      if (data.status === 'completed') {
        onSuccess();
      } else if (data.status === 'failed') {
        setError('Payment failed. Please try again.');
      }
      // For 'pending' status, we just wait
    } catch (err) {
      console.error('Error checking payment status:', err);
    } finally {
      setProcessing(false);
    }
  };

  const calculatePrice = () => {
    if (!tier) return 0;
    
    return billingCycle === 'monthly'
      ? tier.monthly_price || tier.price
      : tier.annual_price || tier.price * 10; // 10 months for annual (2 months free)
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4">
          <div className="flex justify-center">
            <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  if (!tier) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Subscription Not Found</h2>
            <p className="text-gray-600 mb-6">
              We couldn't find the subscription plan you selected. Please try again.
            </p>
            <button
              onClick={onCancel}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Complete Your Subscription</h2>
        <p className="text-gray-600 mb-6">
          You've selected the <span className="font-semibold">{tier.name}</span> plan.
        </p>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        <div className="border rounded-lg p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Order Summary</h3>
          
          <div className="flex justify-between mb-2">
            <span>Plan</span>
            <span>{tier.name}</span>
          </div>
          
          <div className="flex justify-between mb-4">
            <span>Billing Cycle</span>
            <div className="flex space-x-2">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-3 py-1 text-sm rounded ${
                  billingCycle === 'monthly'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('annual')}
                className={`px-3 py-1 text-sm rounded ${
                  billingCycle === 'annual'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Annual (Save 16%)
              </button>
            </div>
          </div>
          
          <div className="border-t pt-4 flex justify-between font-semibold">
            <span>Total</span>
            <span>${calculatePrice().toFixed(2)} {billingCycle === 'monthly' ? '/month' : '/year'}</span>
          </div>
        </div>

        <div className="mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Features Included</h3>
          <ul className="space-y-2">
            {tier.features.map((feature, index) => (
              <li key={index} className="flex items-start">
                <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex justify-between">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={initiatePayment}
            disabled={processing}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {processing ? (
              <>
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
                Processing...
              </>
            ) : (
              <>
                <CreditCard className="h-4 w-4 mr-2" />
                Proceed to Payment
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}