import React from 'react';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'full' | 'icon';
}

const Logo: React.FC<LogoProps> = ({ className = '', size = 'md', variant = 'full' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12'
  };

  const iconSize = sizeClasses[size];

  return (
    <div className={`flex items-center ${className}`}>
      {/* Logo Icon - Meeting Minutes symbol */}
      <div className={`relative ${iconSize}`}>
        {/* Outer gradient circle */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-indigo-600 to-blue-600 rounded-xl shadow-lg transform rotate-3 transition-transform hover:rotate-6"></div>

        {/* Inner content */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600 via-indigo-700 to-blue-700 rounded-xl flex items-center justify-center shadow-inner">
          {/* Document/Notes icon */}
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-3/5 h-3/5 text-white"
          >
            {/* Document outline */}
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            {/* Folded corner */}
            <polyline points="14 2 14 8 20 8" />
            {/* Lines representing text */}
            <line x1="8" y1="13" x2="16" y2="13" />
            <line x1="8" y1="17" x2="16" y2="17" />
            {/* Pencil/edit indicator */}
            <circle cx="10" cy="9" r="1.5" fill="currentColor" />
          </svg>
        </div>

        {/* Sparkle/AI indicator */}
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-gradient-to-r from-yellow-400 to-amber-500 rounded-full border-2 border-white shadow-md animate-pulse"></div>
      </div>

      {/* Logo Text */}
      {variant === 'full' && (
        <div className="ml-3">
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 bg-clip-text text-transparent">
              Meeting Minutes
            </span>
            <span className="text-xl font-bold text-indigo-400">Pro</span>
          </div>
          <div className="flex items-center gap-1 -mt-1">
            <div className="w-1 h-1 rounded-full bg-purple-400"></div>
            <div className="w-1 h-1 rounded-full bg-indigo-400"></div>
            <div className="w-1 h-1 rounded-full bg-blue-400"></div>
            <span className="text-[10px] font-medium text-gray-500 ml-1">AI-Powered</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Logo;
