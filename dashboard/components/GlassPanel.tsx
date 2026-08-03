import { ReactNode } from 'react';

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
}

export function GlassPanel({ children, className = '' }: GlassPanelProps) {
  return (
    <div className={`rounded-3xl border border-[#262626] bg-[rgba(23,23,23,0.72)] bg-gradient-to-br from-[#161616]/90 to-[#111111]/80 p-6 shadow-glow backdrop-blur-xl ${className}`}>
      {children}
    </div>
  );
}
