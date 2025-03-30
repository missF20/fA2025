import React, { useState, useEffect } from 'react';
import { BrainCircuit, Loader2, Eye, EyeOff, Quote } from 'lucide-react';
import type { AuthFormData } from '../types';
import { motion } from 'framer-motion';

interface AuthFormProps {
  mode: 'signin' | 'signup';
  onSubmit: (data: AuthFormData) => Promise<void>;
  error?: string | null;
  onToggleMode: () => void;
  onForgotPassword: () => void;
}

const testimonials = [
  {
    name: "Sarah Johnson",
    role: "Marketing Director",
    company: "TechCorp",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&auto=format&fit=crop&w=128&h=128&q=80",
    content: "Dana AI has transformed how we handle customer interactions. The AI responses are incredibly natural and accurate."
  },
  {
    name: "Michael Chen",
    role: "Customer Success Lead",
    company: "InnovateHub",
    image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&auto=format&fit=crop&w=128&h=128&q=80",
    content: "The multi-platform support is seamless. We've seen a 50% reduction in response time since implementing Dana AI."
  }
];

const FloatingFeature = () => (
  <motion.div
    className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96"
    animate={{
      rotateX: [0, 25, 0],
      rotateY: [0, 25, 0],
    }}
    transition={{
      duration: 10,
      repeat: Infinity,
      ease: "linear"
    }}
  >
    <div className="relative w-full h-full">
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-full blur-xl"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0.8, 0.5],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <motion.div
        className="absolute inset-0 border-2 border-blue-500/20 rounded-full"
        animate={{
          rotate: [0, 360],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
      />
      <motion.div
        className="absolute inset-0 border-2 border-purple-500/20 rounded-full"
        animate={{
          rotate: [360, 0],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "linear"
        }}
      />
    </div>
  </motion.div>
);

const TestimonialCard = ({ testimonial, position }: { testimonial: typeof testimonials[0], position: 'left' | 'right' }) => (
  <motion.div
    initial={{ opacity: 0, x: position === 'left' ? -100 : 100 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ duration: 0.8, delay: 0.5 }}
    className={`absolute bottom-8 ${position === 'left' ? 'left-8' : 'right-8'} max-w-sm bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-lg hidden md:block`}
  >
    <Quote className="text-blue-500 mb-2" size={24} />
    <p className="text-gray-700 text-sm mb-4">{testimonial.content}</p>
    <div className="flex items-center">
      <img src={testimonial.image} alt={testimonial.name} className="w-10 h-10 rounded-full mr-3" />
      <div>
        <p className="font-medium text-gray-900">{testimonial.name}</p>
        <p className="text-sm text-gray-500">{testimonial.role} at {testimonial.company}</p>
      </div>
    </div>
  </motion.div>
);

export function AuthForm({ mode, onSubmit, error, onToggleMode, onForgotPassword }: AuthFormProps) {
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState<AuthFormData>({
    email: '',
    password: '',
    company: '',
    rememberMe: false,
  });

  useEffect(() => {
    const savedEmail = localStorage.getItem('dana_email');
    if (savedEmail && mode === 'signin') {
      setFormData(prev => ({
        ...prev,
        email: savedEmail,
        rememberMe: true,
      }));
    }
  }, [mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setFormError(null);

    try {
      if (!formData.email || !formData.password) {
        throw new Error('Please fill in all required fields');
      }

      if (mode === 'signup' && !formData.company) {
        throw new Error('Company name is required for signup');
      }

      await onSubmit(formData);
      
      if (formData.rememberMe) {
        localStorage.setItem('dana_email', formData.email);
      } else {
        localStorage.removeItem('dana_email');
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4 relative overflow-hidden">
      <FloatingFeature />
      
      <div className="w-full max-w-md relative">
        <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-center mb-8">
            <BrainCircuit className="text-blue-600 h-12 w-12" />
          </div>
          
          <h2 className="text-2xl font-bold text-center text-gray-900 mb-2">
            {mode === 'signin' ? 'Welcome back to Dana' : 'Get started with Dana'}
          </h2>
          <p className="text-center text-gray-500 text-sm mb-8">
            {mode === 'signin' 
              ? 'Sign in to access your Dana dashboard'
              : 'Create an account to start using Dana AI'
            }
          </p>

          {(error || formError) && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-6 text-sm">
              {error || formError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="you@company.com"
                autoComplete="email"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                {mode === 'signin' && (
                  <button
                    type="button"
                    onClick={onForgotPassword}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                  placeholder="••••••••"
                  autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? (
                    <EyeOff size={18} className="text-gray-500" />
                  ) : (
                    <Eye size={18} className="text-gray-500" />
                  )}
                </button>
              </div>
            </div>

            {mode === 'signup' && (
              <div>
                <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-1">
                  Company name
                </label>
                <input
                  id="company"
                  type="text"
                  required
                  value={formData.company}
                  onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Your company"
                  autoComplete="organization"
                />
              </div>
            )}

            <div className="pt-4 mt-2">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  type="checkbox"
                  checked={formData.rememberMe}
                  onChange={(e) => setFormData({ ...formData, rememberMe: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                  Remember me
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <Loader2 className="animate-spin h-5 w-5" />
              ) : mode === 'signin' ? (
                'Sign in'
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {mode === 'signin' ? (
                <>
                  Don't have an account?{' '}
                  <button
                    onClick={onToggleMode}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Sign up
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <button
                    onClick={onToggleMode}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Sign in
                  </button>
                </>
              )}
            </p>
          </div>
        </div>
      </div>

      <TestimonialCard testimonial={testimonials[0]} position="left" />
      <TestimonialCard testimonial={testimonials[1]} position="right" />
    </div>
  );
}