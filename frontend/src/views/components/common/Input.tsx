import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  rightAction?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  rightAction,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || props.name;

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-bold text-slate-800 mb-1.5 tracking-tight">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        <input
          id={inputId}
          className={`w-full px-3.5 py-2.5 bg-white border-2 rounded-lg text-base text-slate-900 transition-all focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-600 placeholder-slate-400 shadow-sm ${error ? 'border-rose-400 focus:ring-rose-400 focus:border-rose-600 bg-rose-50/20' : 'border-slate-300 hover:border-slate-400'
            } ${rightAction ? 'pr-11' : ''} ${className}`}
          {...props}
        />
        {rightAction && (
          <div className="absolute right-3 flex items-center">
            {rightAction}
          </div>
        )}
      </div>
      {error && <p className="mt-1 text-sm font-medium text-rose-600">{error}</p>}
      {helperText && !error && <p className="mt-1 text-sm text-slate-500">{helperText}</p>}
    </div>
  );
};


