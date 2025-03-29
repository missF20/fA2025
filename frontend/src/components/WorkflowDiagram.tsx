import React from 'react';
import { ArrowRight, MessageSquare, Database, Bot, AlertTriangle, CheckCircle } from 'lucide-react';

export function WorkflowDiagram() {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-xl font-bold text-gray-900 mb-6">Dana AI Workflow Architecture</h3>
      
      <div className="relative">
        {/* Main workflow diagram */}
        <div className="flex flex-col space-y-8">
          {/* Input Sources */}
          <div className="flex justify-between items-center">
            <div className="flex-1 flex justify-center">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 w-40 flex flex-col items-center">
                <div className="p-2 bg-blue-100 rounded-full mb-2">
                  <MessageSquare className="h-6 w-6 text-blue-600" />
                </div>
                <span className="text-sm font-medium text-blue-800">Facebook</span>
              </div>
            </div>
            <div className="flex-1 flex justify-center">
              <div className="bg-pink-50 p-4 rounded-lg border border-pink-100 w-40 flex flex-col items-center">
                <div className="p-2 bg-pink-100 rounded-full mb-2">
                  <MessageSquare className="h-6 w-6 text-pink-600" />
                </div>
                <span className="text-sm font-medium text-pink-800">Instagram</span>
              </div>
            </div>
            <div className="flex-1 flex justify-center">
              <div className="bg-green-50 p-4 rounded-lg border border-green-100 w-40 flex flex-col items-center">
                <div className="p-2 bg-green-100 rounded-full mb-2">
                  <MessageSquare className="h-6 w-6 text-green-600" />
                </div>
                <span className="text-sm font-medium text-green-800">WhatsApp</span>
              </div>
            </div>
          </div>
          
          {/* Arrows down */}
          <div className="flex justify-between items-center">
            <div className="flex-1 flex justify-center">
              <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
            </div>
            <div className="flex-1 flex justify-center">
              <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
            </div>
            <div className="flex-1 flex justify-center">
              <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
            </div>
          </div>
          
          {/* Make.com Workflow */}
          <div className="flex justify-center">
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-100 w-full max-w-2xl flex flex-col items-center">
              <h4 className="font-semibold text-purple-800 mb-3">Make.com Workflow</h4>
              <div className="grid grid-cols-3 gap-4 w-full">
                <div className="bg-white p-3 rounded border border-purple-100 flex flex-col items-center">
                  <span className="text-xs font-medium text-purple-700 mb-1">Trigger</span>
                  <span className="text-xs text-gray-600">New Message</span>
                </div>
                <div className="bg-white p-3 rounded border border-purple-100 flex flex-col items-center">
                  <span className="text-xs font-medium text-purple-700 mb-1">Process</span>
                  <span className="text-xs text-gray-600">Format Data</span>
                </div>
                <div className="bg-white p-3 rounded border border-purple-100 flex flex-col items-center">
                  <span className="text-xs font-medium text-purple-700 mb-1">Route</span>
                  <span className="text-xs text-gray-600">AI Processing</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Arrow down */}
          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
          </div>
          
          {/* AI Processing */}
          <div className="flex justify-center">
            <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100 w-full max-w-md flex flex-col items-center">
              <div className="p-2 bg-indigo-100 rounded-full mb-2">
                <Bot className="h-6 w-6 text-indigo-600" />
              </div>
              <h4 className="font-semibold text-indigo-800 mb-1">AI Processing</h4>
              <p className="text-xs text-indigo-600 text-center">
                Natural language understanding, intent classification, and response generation
              </p>
            </div>
          </div>
          
          {/* Arrow down */}
          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
          </div>
          
          {/* Decision & Database */}
          <div className="flex justify-between items-center">
            <div className="flex-1 flex justify-end pr-4">
              <div className="bg-amber-50 p-4 rounded-lg border border-amber-100 w-48 flex flex-col items-center">
                <div className="p-2 bg-amber-100 rounded-full mb-2">
                  <AlertTriangle className="h-6 w-6 text-amber-600" />
                </div>
                <h4 className="font-semibold text-amber-800 mb-1">Escalation</h4>
                <p className="text-xs text-amber-600 text-center">
                  Complex queries requiring human attention
                </p>
              </div>
            </div>
            <div className="flex-1 flex justify-start pl-4">
              <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100 w-48 flex flex-col items-center">
                <div className="p-2 bg-emerald-100 rounded-full mb-2">
                  <CheckCircle className="h-6 w-6 text-emerald-600" />
                </div>
                <h4 className="font-semibold text-emerald-800 mb-1">Resolution</h4>
                <p className="text-xs text-emerald-600 text-center">
                  Automated responses to common queries
                </p>
              </div>
            </div>
          </div>
          
          {/* Arrows down */}
          <div className="flex justify-between items-center">
            <div className="flex-1 flex justify-center">
              <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
            </div>
            <div className="flex-1 flex justify-center">
              <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
            </div>
          </div>
          
          {/* Database */}
          <div className="flex justify-center">
            <div className="bg-cyan-50 p-4 rounded-lg border border-cyan-100 w-full max-w-lg flex flex-col items-center">
              <div className="p-2 bg-cyan-100 rounded-full mb-2">
                <Database className="h-6 w-6 text-cyan-600" />
              </div>
              <h4 className="font-semibold text-cyan-800 mb-1">Supabase Database</h4>
              <p className="text-xs text-cyan-600 text-center">
                Stores conversations, responses, tasks, and metrics for the Dana dashboard
              </p>
            </div>
          </div>
          
          {/* Arrow down */}
          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-gray-400 transform rotate-90" />
          </div>
          
          {/* Response Distribution */}
          <div className="flex justify-between items-center">
            <div className="flex-1 flex justify-center">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 w-40 flex flex-col items-center">
                <span className="text-sm font-medium text-blue-800">Facebook</span>
                <span className="text-xs text-blue-600">Response</span>
              </div>
            </div>
            <div className="flex-1 flex justify-center">
              <div className="bg-pink-50 p-4 rounded-lg border border-pink-100 w-40 flex flex-col items-center">
                <span className="text-sm font-medium text-pink-800">Instagram</span>
                <span className="text-xs text-pink-600">Response</span>
              </div>
            </div>
            <div className="flex-1 flex justify-center">
              <div className="bg-green-50 p-4 rounded-lg border border-green-100 w-40 flex flex-col items-center">
                <span className="text-sm font-medium text-green-800">WhatsApp</span>
                <span className="text-xs text-green-600">Response</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-8 bg-gray-50 p-4 rounded-lg border border-gray-100">
        <h4 className="font-medium text-gray-800 mb-2">Key Workflow Features:</h4>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start">
            <CheckCircle size={16} className="text-green-500 mr-2 mt-0.5" />
            <span>Simultaneous multi-platform messaging (Facebook, Instagram, WhatsApp)</span>
          </li>
          <li className="flex items-start">
            <CheckCircle size={16} className="text-green-500 mr-2 mt-0.5" />
            <span>Centralized conversation history and context management</span>
          </li>
          <li className="flex items-start">
            <CheckCircle size={16} className="text-green-500 mr-2 mt-0.5" />
            <span>Automated response generation with AI-powered understanding</span>
          </li>
          <li className="flex items-start">
            <CheckCircle size={16} className="text-green-500 mr-2 mt-0.5" />
            <span>Intelligent task routing and escalation to human agents when needed</span>
          </li>
          <li className="flex items-start">
            <CheckCircle size={16} className="text-green-500 mr-2 mt-0.5" />
            <span>Comprehensive analytics and reporting in the Dana dashboard</span>
          </li>
        </ul>
      </div>
    </div>
  );
}