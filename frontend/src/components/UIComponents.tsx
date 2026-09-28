'use client';

import React, { useState } from 'react';
import { Copy, Check, AlertCircle, RefreshCw, Layers } from 'lucide-react';

export function Card({
  children,
  className = '',
  glow = false,
  glowColor = 'primary',
  ...props
}: {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  glowColor?: 'primary' | 'danger' | 'warning' | 'success';
  [key: string]: any;
}) {
  const glowClasses = {
    primary: 'hover:shadow-glow hover:border-[#7C5CFF]/50',
    danger: 'hover:shadow-glow-danger hover:border-[#FF4D6D]/50',
    warning: 'hover:shadow-glow-warning hover:border-[#FFB020]/50',
    success: 'hover:shadow-glow-success hover:border-[#2DD4A0]/50',
  };

  return (
    <div
      className={`bg-[#12151C] border border-[#1F2430] rounded-16 p-5 transition-all duration-200 ${
        glow ? glowClasses[glowColor] : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function Badge({
  children,
  variant = 'default',
  className = '',
}: {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'danger' | 'warning' | 'success' | 'outline' | 'ghost';
  className?: string;
}) {
  const variants = {
    default: 'bg-[#1F2430] text-[#E6E8EE]',
    primary: 'bg-[#7C5CFF]/15 text-[#9E85FF] border border-[#7C5CFF]/30',
    danger: 'bg-[#FF4D6D]/15 text-[#FF4D6D] border border-[#FF4D6D]/30',
    warning: 'bg-[#FFB020]/15 text-[#FFB020] border border-[#FFB020]/30',
    success: 'bg-[#2DD4A0]/15 text-[#2DD4A0] border border-[#2DD4A0]/30',
    outline: 'border border-[#1F2430] text-[#8A90A2]',
    ghost: 'bg-transparent text-[#8A90A2]',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium tracking-wide ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className = '',
  disabled,
  ...props
}: {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  className?: string;
  disabled?: boolean;
  [key: string]: any;
}) {
  const base =
    'inline-flex items-center justify-center font-medium rounded-12 transition-all duration-200 focus-visible:ring-2 focus-visible:ring-[#7C5CFF] disabled:opacity-50 disabled:cursor-not-allowed';

  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base font-semibold',
  };

  const variants = {
    primary:
      'bg-[#7C5CFF] hover:bg-[#6B47FF] text-white shadow-glow hover:shadow-glow-lg active:scale-[0.98]',
    secondary: 'bg-[#1A1E29] hover:bg-[#252A38] text-[#E6E8EE] border border-[#1F2430]',
    danger:
      'bg-[#FF4D6D] hover:bg-[#E03C5A] text-white shadow-glow-danger active:scale-[0.98]',
    outline: 'border border-[#1F2430] hover:border-[#7C5CFF] hover:text-[#7C5CFF] text-[#E6E8EE]',
    ghost: 'hover:bg-[#1A1E29] text-[#8A90A2] hover:text-[#E6E8EE]',
  };

  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
      ) : null}
      {children}
    </button>
  );
}

export function CopyButton({ text, label = 'Copy' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1.5 text-xs text-[#8A90A2] hover:text-[#E6E8EE] bg-[#12151C] hover:bg-[#1A1E29] border border-[#1F2430] px-2.5 py-1 rounded-lg transition-colors"
      title="Copy to clipboard"
    >
      {copied ? (
        <>
          <Check className="w-3.5 h-3.5 text-[#2DD4A0]" />
          <span className="text-[#2DD4A0]">Copied!</span>
        </>
      ) : (
        <>
          <Copy className="w-3.5 h-3.5" />
          <span>{label}</span>
        </>
      )}
    </button>
  );
}

export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-[#1F2430]/60 rounded-lg ${className}`}
    />
  );
}

export function EmptyState({
  icon: Icon = Layers,
  title,
  description,
  action,
}: {
  icon?: any;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border border-dashed border-[#1F2430] rounded-16 bg-[#12151C]/50">
      <div className="w-12 h-12 rounded-full bg-[#1A1E29] border border-[#1F2430] flex items-center justify-center text-[#8A90A2] mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-[#E6E8EE] mb-1">{title}</h3>
      <p className="text-sm text-[#8A90A2] max-w-md mb-4">{description}</p>
      {action}
    </div>
  );
}

export function ErrorBanner({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex items-center justify-between p-4 bg-[#FF4D6D]/10 border border-[#FF4D6D]/30 rounded-12 text-sm text-[#FF4D6D]">
      <div className="flex items-center gap-2">
        <AlertCircle className="w-5 h-5 flex-shrink-0" />
        <span>{message}</span>
      </div>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry} className="border-[#FF4D6D]/40 text-[#FF4D6D] hover:bg-[#FF4D6D]/20">
          Retry
        </Button>
      )}
    </div>
  );
}
