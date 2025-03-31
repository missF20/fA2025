import React, { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import { UserCircle, CreditCard, LogOut, ChevronDown } from 'lucide-react';

interface ProfileMenuProps {
  onSectionChange: (section: string) => void;
}

export function ProfileMenu({ onSectionChange }: ProfileMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [companyName, setCompanyName] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProfile() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;

        const { data: profile, error } = await supabase
          .from('profiles')
          .select('company')
          .eq('id', session.user.id)
          .single();

        if (error) throw error;
        if (profile?.company) {
          setCompanyName(profile.company);
        }
      } catch (error) {
        console.error('Error fetching profile:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchProfile();
  }, []);

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
      >
        <UserCircle className="h-6 w-6" />
        <span className="font-medium">
          {loading ? 'Loading...' : companyName || 'My Account'}
        </span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50">
          <div className="px-4 py-2 border-b border-gray-100">
            <p className="text-sm font-medium text-gray-900">{companyName}</p>
          </div>
          
          <button
            onClick={() => {
              onSectionChange('subscriptions');
              setIsOpen(false);
            }}
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
          >
            <CreditCard className="h-4 w-4 inline-block mr-2" />
            Subscription
          </button>
          
          <button
            onClick={handleSignOut}
            className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 cursor-pointer"
          >
            <LogOut className="h-4 w-4 inline-block mr-2" />
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}