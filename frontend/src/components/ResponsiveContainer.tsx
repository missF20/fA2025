import { ReactNode } from 'react';

interface ResponsiveContainerProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: boolean;
}

export function ResponsiveContainer({
  children,
  className = '',
  maxWidth = 'xl',
  padding = true,
}: ResponsiveContainerProps) {
  const maxWidthClasses = {
    sm: 'max-w-screen-sm',
    md: 'max-w-screen-md',
    lg: 'max-w-screen-lg',
    xl: 'max-w-screen-xl',
    '2xl': 'max-w-screen-2xl',
    full: 'max-w-full',
  };

  return (
    <div
      className={`mx-auto ${maxWidthClasses[maxWidth]} ${
        padding ? 'px-4 sm:px-6 md:px-8' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
}