import React from 'react';
import { FileText, Link2, CheckCircle, AlertTriangle, HelpCircle } from 'lucide-react';

export function IntegrationGuide() {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mt-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
        <FileText className="mr-2 text-blue-600" size={20} />
        Integration Setup Guide
      </h3>
      
      <div className="space-y-6">
        <div className="border-l-4 border-blue-500 pl-4 py-2">
          <p className="text-gray-700">
            Setting up integrations with Dana AI involves a few steps to ensure secure and proper data flow between systems.
            Follow this guide to connect your tools successfully.
          </p>
        </div>
        
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-gray-800">General Integration Process</h4>
          
          <div className="space-y-3">
            <div className="flex items-start">
              <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mt-0.5 mr-3">
                1
              </div>
              <div>
                <h5 className="font-medium text-gray-800">Generate API Keys</h5>
                <p className="text-gray-600 text-sm mt-1">
                  Click the "Connect" button on any integration card to generate the necessary API keys and credentials.
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mt-0.5 mr-3">
                2
              </div>
              <div>
                <h5 className="font-medium text-gray-800">Authorize Access</h5>
                <p className="text-gray-600 text-sm mt-1">
                  You'll be redirected to the service's authorization page where you'll need to grant Dana AI permission to access your data.
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mt-0.5 mr-3">
                3
              </div>
              <div>
                <h5 className="font-medium text-gray-800">Configure Data Mapping</h5>
                <p className="text-gray-600 text-sm mt-1">
                  Define how data should flow between Dana AI and your integrated service, including field mappings and synchronization settings.
                </p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mt-0.5 mr-3">
                4
              </div>
              <div>
                <h5 className="font-medium text-gray-800">Test the Connection</h5>
                <p className="text-gray-600 text-sm mt-1">
                  Verify the integration is working properly by sending test data between systems.
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div className="bg-green-50 p-4 rounded-lg border border-green-100">
            <div className="flex items-center mb-2">
              <CheckCircle size={18} className="text-green-600 mr-2" />
              <h5 className="font-medium text-green-800">Recommended Practices</h5>
            </div>
            <ul className="text-sm text-green-700 space-y-2 pl-6 list-disc">
              <li>Use unique API keys for each integration</li>
              <li>Regularly rotate credentials for security</li>
              <li>Start with minimal permissions and expand as needed</li>
              <li>Document custom field mappings for reference</li>
            </ul>
          </div>
          
          <div className="bg-amber-50 p-4 rounded-lg border border-amber-100">
            <div className="flex items-center mb-2">
              <AlertTriangle size={18} className="text-amber-600 mr-2" />
              <h5 className="font-medium text-amber-800">Common Issues</h5>
            </div>
            <ul className="text-sm text-amber-700 space-y-2 pl-6 list-disc">
              <li>Expired access tokens</li>
              <li>Insufficient permissions in the connected service</li>
              <li>Rate limiting from the third-party API</li>
              <li>Data format mismatches between systems</li>
            </ul>
          </div>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 mt-6">
          <div className="flex items-center mb-2">
            <HelpCircle size={18} className="text-blue-600 mr-2" />
            <h5 className="font-medium text-blue-800">Need Help?</h5>
          </div>
          <p className="text-sm text-blue-700 mb-3">
            Our integration specialists can help you set up custom connections or troubleshoot issues with existing integrations.
          </p>
          <div className="flex items-center">
            <Link2 size={16} className="text-blue-600 mr-2" />
            <a href="#" className="text-blue-600 hover:text-blue-800 font-medium text-sm">
              Schedule an integration consultation
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}