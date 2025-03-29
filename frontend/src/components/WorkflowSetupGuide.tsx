import React from 'react';
import { FileText, Link2, CheckCircle, AlertTriangle, HelpCircle, Code } from 'lucide-react';

export function WorkflowSetupGuide() {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mt-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
        <FileText className="mr-2 text-blue-600" size={20} />
        Make.com Workflow Setup Guide
      </h3>
      
      <div className="space-y-6">
        <div className="border-l-4 border-blue-500 pl-4 py-2">
          <p className="text-gray-700">
            This guide outlines how to set up the Make.com workflow that powers Dana AI's multi-platform messaging system.
            Our technical team will handle this setup for you, but this information helps you understand the process.
          </p>
        </div>
        
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-gray-800">Workflow Components</h4>
          
          <div className="space-y-6">
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <h5 className="font-medium text-gray-800 mb-3 flex items-center">
                <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mr-2">1</div>
                Platform Triggers
              </h5>
              <p className="text-sm text-gray-600 mb-3">
                The workflow begins with triggers that monitor your social media platforms for new messages.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-blue-700 text-sm">Facebook Messenger</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Monitors your Facebook page for new customer messages
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-pink-700 text-sm">Instagram DM</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Watches for new direct messages on your Instagram business account
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-green-700 text-sm">WhatsApp Business</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Listens for incoming messages on your WhatsApp Business number
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <h5 className="font-medium text-gray-800 mb-3 flex items-center">
                <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mr-2">2</div>
                Data Processing
              </h5>
              <p className="text-sm text-gray-600 mb-3">
                When a message is received, the workflow processes and standardizes the data.
              </p>
              <div className="space-y-3">
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Message Normalization</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Converts platform-specific message formats into a standardized structure
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Context Enrichment</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Adds customer information and conversation history for better AI understanding
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <h5 className="font-medium text-gray-800 mb-3 flex items-center">
                <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mr-2">3</div>
                AI Processing
              </h5>
              <p className="text-sm text-gray-600 mb-3">
                The normalized message is sent to the AI service for understanding and response generation.
              </p>
              <div className="space-y-3">
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Intent Classification</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Determines what the customer is asking for or trying to accomplish
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Response Generation</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Creates a natural language response based on the intent and available data
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Task Identification</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Identifies if the message requires creating a task or escalating to a human
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <h5 className="font-medium text-gray-800 mb-3 flex items-center">
                <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mr-2">4</div>
                Database Operations
              </h5>
              <p className="text-sm text-gray-600 mb-3">
                The workflow stores all relevant information in your Supabase database.
              </p>
              <div className="space-y-3">
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Conversation Storage</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Records the full conversation history in the conversations and messages tables
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Task Creation</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Creates tasks in the tasks table when action items are identified
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-gray-700 text-sm">Metrics Updating</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Updates interaction and response metrics for dashboard reporting
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <h5 className="font-medium text-gray-800 mb-3 flex items-center">
                <div className="bg-blue-100 text-blue-800 rounded-full h-6 w-6 flex items-center justify-center flex-shrink-0 mr-2">5</div>
                Response Distribution
              </h5>
              <p className="text-sm text-gray-600 mb-3">
                Finally, the workflow sends the AI-generated response back to the appropriate platform.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-blue-700 text-sm">Facebook Reply</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Sends the response back to the customer via Facebook Messenger
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-pink-700 text-sm">Instagram Reply</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Delivers the response through Instagram Direct Messages
                  </p>
                </div>
                <div className="bg-white p-3 rounded border border-gray-200">
                  <h6 className="font-medium text-green-700 text-sm">WhatsApp Reply</h6>
                  <p className="text-xs text-gray-600 mt-1">
                    Sends the message back through the WhatsApp Business API
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
          <h5 className="font-medium text-blue-800 mb-2 flex items-center">
            <Code size={18} className="text-blue-600 mr-2" />
            Technical Requirements
          </h5>
          <ul className="space-y-2 text-sm text-blue-700 pl-6 list-disc">
            <li>Facebook Developer account with Messenger permissions</li>
            <li>Instagram Professional account linked to Facebook</li>
            <li>WhatsApp Business API access</li>
            <li>Make.com Professional plan or higher</li>
            <li>Supabase database with the Dana AI schema</li>
          </ul>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div className="bg-green-50 p-4 rounded-lg border border-green-100">
            <div className="flex items-center mb-2">
              <CheckCircle size={18} className="text-green-600 mr-2" />
              <h5 className="font-medium text-green-800">Benefits</h5>
            </div>
            <ul className="text-sm text-green-700 space-y-2 pl-6 list-disc">
              <li>Centralized management of all customer conversations</li>
              <li>Consistent AI responses across all platforms</li>
              <li>Automated task creation and escalation</li>
              <li>Comprehensive analytics and reporting</li>
              <li>Reduced response time and improved customer satisfaction</li>
            </ul>
          </div>
          
          <div className="bg-amber-50 p-4 rounded-lg border border-amber-100">
            <div className="flex items-center mb-2">
              <AlertTriangle size={18} className="text-amber-600 mr-2" />
              <h5 className="font-medium text-amber-800">Important Notes</h5>
            </div>
            <ul className="text-sm text-amber-700 space-y-2 pl-6 list-disc">
              <li>Setup requires platform-specific API credentials</li>
              <li>Initial configuration takes approximately 24 hours</li>
              <li>Platform rate limits may apply to high-volume accounts</li>
              <li>Custom AI training may be needed for specialized industries</li>
              <li>Regular workflow maintenance ensures optimal performance</li>
            </ul>
          </div>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 mt-6">
          <div className="flex items-center mb-2">
            <HelpCircle size={18} className="text-blue-600 mr-2" />
            <h5 className="font-medium text-blue-800">Need Help?</h5>
          </div>
          <p className="text-sm text-blue-700 mb-3">
            Our technical team will handle the entire workflow setup process for you. If you have any questions or need to provide platform credentials, please contact our support team.
          </p>
          <div className="flex items-center">
            <Link2 size={16} className="text-blue-600 mr-2" />
            <a href="#" className="text-blue-600 hover:text-blue-800 font-medium text-sm">
              Contact technical support
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}