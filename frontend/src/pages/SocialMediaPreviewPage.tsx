import { SocialMediaPreview } from '../components/SocialMediaPreview';

export function SocialMediaPreviewPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="container mx-auto pt-8">
        <div className="mb-4 p-4 bg-blue-100 rounded-lg">
          <h1 className="text-xl font-bold text-blue-800">Social Media Connection Preview</h1>
          <p className="text-blue-600">
            This is a preview of the social media connection component that appears after subscription selection.
          </p>
        </div>
        
        <SocialMediaPreview />
      </div>
    </div>
  );
}