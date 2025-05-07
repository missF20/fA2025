import React, { useEffect } from 'react';

export const DiagnoseApp: React.FC = () => {
  useEffect(() => {
    console.log('DiagnoseApp component mounted');
    
    // Check if Chart.js is loaded
    try {
      const chartImport = import('chart.js');
      console.log('Chart.js can be imported');
    } catch (error) {
      console.error('Error importing Chart.js:', error);
    }
    
    // Check if axios is loaded
    try {
      const axiosImport = import('axios');
      console.log('axios can be imported');
    } catch (error) {
      console.error('Error importing axios:', error);
    }
    
    // Check localStorage
    try {
      localStorage.setItem('test', 'test');
      console.log('localStorage works');
    } catch (error) {
      console.error('localStorage error:', error);
    }
    
    // Check Supabase
    try {
      const supabaseImport = import('../lib/supabase');
      console.log('Supabase can be imported');
    } catch (error) {
      console.error('Error importing Supabase:', error);
    }
  }, []);

  return (
    <div className="p-8 bg-white rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-4">Diagnosis Page</h1>
      <p className="text-gray-600 mb-4">
        This page is for diagnosing issues with the application.
        Please check the browser console for messages.
      </p>
      <div className="p-4 bg-blue-50 rounded border border-blue-100">
        <p className="font-medium">Common Issues:</p>
        <ul className="list-disc pl-5 mt-2">
          <li>Missing dependencies</li>
          <li>API connection issues</li>
          <li>Authentication problems</li>
          <li>React rendering errors</li>
        </ul>
      </div>
    </div>
  );
};

export default DiagnoseApp;