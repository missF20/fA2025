import { useState } from 'react';
import { SocialMediaConnect } from './SocialMediaConnect';

/**
 * A simple preview component for testing the SocialMediaConnect component 
 * without going through the entire onboarding flow
 */
export function SocialMediaPreview() {
  const [showDemo, setShowDemo] = useState(false);
  
  // Mock handler for when connection is complete
  const handleConnectionComplete = () => {
    alert('Social media connection flow completed!');
    setShowDemo(false);
  };

  return (
    <div className="container mx-auto py-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold mb-6">Social Media Connection Preview</h1>
        
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-blue-700">
          <strong>Note:</strong> This is a preview mode. No actual connections will be made to social media platforms.
        </div>
        
        {!showDemo ? (
          <div className="flex flex-col items-center">
            <p className="mb-4 text-center">
              Click the button below to preview the social media connection flow.
              This is a test interface to see how the component works.
            </p>
            <button 
              onClick={() => setShowDemo(true)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Show Component Preview
            </button>
          </div>
        ) : (
          <div className="bg-gray-50 p-4 rounded-lg">
            <SocialMediaConnect 
              onComplete={handleConnectionComplete}
              availablePlatforms={['facebook', 'instagram', 'whatsapp']}
              subscription={{
                id: 'test-tier',
                name: 'Professional',
                price: 99,
                tokenLimit: 100000,
                description: 'Test subscription tier'
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}