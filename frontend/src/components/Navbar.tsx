'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ShieldAlert,
  GitPullRequest,
  AlertTriangle,
  TrendingUp,
  Code2,
  PlayCircle,
  Database,
  Brain,
  MessageSquare,
  Sun,
  Moon,
} from 'lucide-react';
import { useAppState } from '../app/providers';
import { api, HealthResponse } from '../lib/api';
import { MemoryInspectorDrawer } from './MemoryInspectorDrawer';

export function Navbar() {
  const pathname = usePathname();
  const { theme, toggleTheme, memoryEnabled, toggleMemory, setMemoryInspectorOpen } = useAppState();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => null);
  }, []);

  const navItems = [
    { label: 'Overview', href: '/', icon: ShieldAlert },
    { label: 'Deploy Check', href: '/check', icon: GitPullRequest },
    { label: 'Ask Foresight', href: '/ask', icon: MessageSquare },
    { label: 'Incident Mode', href: '/incident', icon: AlertTriangle },
    { label: 'Insights', href: '/insights', icon: TrendingUp },
    { label: 'Integrate', href: '/integrate', icon: Code2 },
    { label: 'System Operations', href: '/demo', icon: PlayCircle },
  ];

  return (
    <>
      <header className="sticky top-0 z-30 bg-[#0B0D12]/90 backdrop-blur-md border-b border-[#1F2430]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-2.5 group">
                <div className="w-9 h-9 rounded-12 bg-gradient-to-tr from-[#7C5CFF] to-[#9E85FF] flex items-center justify-center text-white shadow-glow group-hover:scale-105 transition-transform">
                  <ShieldAlert className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-lg tracking-tight text-white">
                      FORESIGHT
                    </span>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#7C5CFF]/20 text-[#9E85FF] border border-[#7C5CFF]/30 tracking-wider uppercase">
                      Deploy Safety
                    </span>
                  </div>
                  <p className="text-[10px] text-[#8A90A2] hidden sm:block">
                    Hindsight remembers. Foresight prevents.
                  </p>
                </div>
              </Link>

              <nav className="hidden lg:flex items-center space-x-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-2 px-3 py-2 rounded-12 text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-[#12151C] text-[#7C5CFF] border border-[#1F2430] shadow-sm'
                          : 'text-[#8A90A2] hover:text-[#E6E8EE] hover:bg-[#12151C]/50'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-[#7C5CFF]' : 'text-[#8A90A2]'}`} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#12151C] border border-[#1F2430] text-xs">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2DD4A0] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#2DD4A0]"></span>
                </span>
                <span className="text-[#8A90A2]">
                  {health ? (health.mode === 'offline' ? 'Ready (Mock Engine)' : 'Live Groq/Hindsight') : 'Connecting...'}
                </span>
              </div>

              <button
                onClick={toggleTheme}
                className="p-2 rounded-12 bg-[#12151C] hover:bg-[#1A1E29] border border-[#1F2430] text-[#E6E8EE] transition-all"
                title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
              >
                {theme === 'dark' ? (
                  <Sun className="w-4 h-4 text-[#FFB020]" />
                ) : (
                  <Moon className="w-4 h-4 text-[#7C5CFF]" />
                )}
              </button>

              <button
                onClick={toggleMemory}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-12 border text-xs font-semibold transition-all ${
                  memoryEnabled
                    ? 'bg-[#7C5CFF]/15 text-[#9E85FF] border-[#7C5CFF]/40 shadow-glow'
                    : 'bg-[#1A1E29] text-[#8A90A2] border-[#1F2430] hover:text-[#E6E8EE]'
                }`}
                title="Toggle Memory ON/OFF for deploy safety checks"
              >
                <Brain className={`w-4 h-4 ${memoryEnabled ? 'text-[#7C5CFF]' : 'text-[#8A90A2]'}`} />
                <span>Memory {memoryEnabled ? 'ON' : 'OFF'}</span>
              </button>

              <button
                onClick={() => setMemoryInspectorOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-12 bg-[#12151C] hover:bg-[#1A1E29] border border-[#1F2430] text-xs font-medium text-[#E6E8EE] transition-all hover:border-[#7C5CFF]/50"
                title="Open Hindsight Memory Inspector"
              >
                <Database className="w-4 h-4 text-[#7C5CFF]" />
                <span className="hidden md:inline">Memory Inspector</span>
              </button>
            </div>
          </div>

          <div className="lg:hidden flex items-center justify-between border-t border-[#1F2430] py-2 overflow-x-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-8 text-xs font-medium whitespace-nowrap ${
                    isActive ? 'bg-[#12151C] text-[#7C5CFF]' : 'text-[#8A90A2]'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </header>

      <MemoryInspectorDrawer />
    </>
  );
}
