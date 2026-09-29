'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  PlayCircle,
  RotateCcw,
  CheckCircle2,
  Sparkles,
  Clock,
} from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Card, Badge, Button, ErrorBanner } from '../../components/UIComponents';
import { api, DemoReplayResponse, DemoResetResponse } from '../../lib/api';

export default function DemoControlPage() {
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayProgress, setReplayProgress] = useState(0);
  const [liveMemoryCounter, setLiveMemoryCounter] = useState(0);
  const [replayResult, setReplayResult] = useState<DemoReplayResponse | null>(null);

  const [isResetting, setIsResetting] = useState(false);
  const [resetResult, setResetResult] = useState<DemoResetResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleReplay = async () => {
    setIsReplaying(true);
    setError(null);
    setReplayResult(null);
    setResetResult(null);
    setReplayProgress(0);
    setLiveMemoryCounter(0);

    const progressInterval = setInterval(() => {
      setReplayProgress((prev) => {
        if (prev >= 95) return 95;
        return prev + 5;
      });
      setLiveMemoryCounter((prev) => Math.min(prev + 3, 60));
    }, 120);

    try {
      const res = await api.replayDemo();
      clearInterval(progressInterval);
      setReplayProgress(100);
      setLiveMemoryCounter(res.total_retained || 60);
      setReplayResult(res);
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.message || 'Failed to replay demo timeline');
    } finally {
      setIsReplaying(false);
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset the memory bank and demo state?')) return;
    setIsResetting(true);
    setError(null);
    setReplayResult(null);
    try {
      const res = await api.resetDemo();
      setResetResult(res);
      setReplayProgress(0);
      setLiveMemoryCounter(0);
    } catch (err: any) {
      setError(err.message || 'Failed to reset demo state');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0D12] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#12151C] p-6 rounded-16 border border-[#1F2430]">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-extrabold text-white">System Data & Memory Operations</h1>
              <Badge variant="primary">
                <PlayCircle className="w-3.5 h-3.5 mr-1" /> Seed & Replay Engine
              </Badge>
            </div>
            <p className="text-sm text-[#8A90A2]">
              Seed incident history and deploy timelines into Hindsight memory bank or manage system state.
            </p>
          </div>
        </div>

        {error && <ErrorBanner message={error} />}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 space-y-6">
            <Card glow glowColor="primary" className="space-y-6">
              <div className="flex items-center justify-between border-b border-[#1F2430] pb-4">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#7C5CFF]" />
                    Seeded Timeline Replay Engine
                  </h2>
                  <p className="text-xs text-[#8A90A2]">
                    Bank target: <span className="font-mono text-[#9E85FF]">foresight-paynest</span>
                  </p>
                </div>

                <Badge variant="success">20 Incidents + 40 Deploys</Badge>
              </div>

              <div className="space-y-3 bg-[#0B0D12] p-5 rounded-12 border border-[#1F2430]">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[#8A90A2] font-mono">Replay Progress:</span>
                  <span className="font-mono font-bold text-[#2DD4A0]">
                    {replayProgress}% | {liveMemoryCounter} Memories Retained
                  </span>
                </div>

                <div className="w-full bg-[#1F2430] h-3 rounded-full overflow-hidden relative">
                  <motion.div
                    className="bg-gradient-to-r from-[#7C5CFF] via-[#9E85FF] to-[#2DD4A0] h-full rounded-full"
                    style={{ width: `${replayProgress}%` }}
                    transition={{ ease: 'linear' }}
                  />
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 pt-2">
                <Button
                  variant="primary"
                  size="lg"
                  className="flex-1 gap-2 text-base font-bold"
                  isLoading={isReplaying}
                  onClick={handleReplay}
                >
                  <PlayCircle className="w-5 h-5" />
                  <span>Seed Incident Memory</span>
                </Button>

                <Button
                  variant="outline"
                  size="lg"
                  className="gap-2 border-[#FF4D6D]/40 text-[#FF4D6D] hover:bg-[#FF4D6D]/10"
                  isLoading={isResetting}
                  onClick={handleReset}
                >
                  <RotateCcw className="w-5 h-5" />
                  <span>Reset System Memory</span>
                </Button>
              </div>

              {replayResult && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-[#2DD4A0]/10 border border-[#2DD4A0]/40 rounded-12 space-y-2 text-xs"
                >
                  <div className="flex items-center gap-2 font-bold text-[#2DD4A0]">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Demo Timeline Replayed Successfully!</span>
                  </div>
                  <p className="text-[#E6E8EE]">{replayResult.message}</p>
                  <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-[11px] text-[#8A90A2]">
                    <div>• Retained Incidents: {replayResult.incidents_retained}</div>
                    <div>• Retained Deploys: {replayResult.deploys_retained}</div>
                  </div>
                </motion.div>
              )}

              {resetResult && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-[#FFB020]/10 border border-[#FFB020]/40 rounded-12 space-y-1 text-xs"
                >
                  <div className="flex items-center gap-2 font-bold text-[#FFB020]">
                    <RotateCcw className="w-4 h-4" />
                    <span>Demo State Reset</span>
                  </div>
                  <p className="text-[#E6E8EE]">{resetResult.message}</p>
                </motion.div>
              )}
            </Card>
          </div>

          <div className="lg:col-span-5 space-y-6">
            <Card className="space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-[#1F2430] pb-3">
                <Clock className="w-4 h-4 text-[#2DD4A0]" />
                90-Second Judge Flow
              </h3>

              <div className="space-y-3 text-xs text-[#8A90A2]">
                <div className="p-3 bg-[#0B0D12] rounded-12 border border-[#1F2430] space-y-1">
                  <span className="font-bold text-[#7C5CFF] block">Step 1: Replay Memory</span>
                  <p className="text-[#E6E8EE]">
                    Click <strong className="text-white">Run Demo Replay</strong> above to seed 20 incidents and 40 deploys into memory.
                  </p>
                </div>

                <div className="p-3 bg-[#0B0D12] rounded-12 border border-[#1F2430] space-y-1">
                  <span className="font-bold text-[#7C5CFF] block">Step 2: Check Deploy</span>
                  <p className="text-[#E6E8EE]">
                    Go to <strong className="text-white">Deploy Check (/check)</strong>, load the Friday 5:40 PM scenario, and run the check to see the cited <span className="text-[#FF4D6D] font-bold">HOLD</span> verdict.
                  </p>
                </div>

                <div className="p-3 bg-[#0B0D12] rounded-12 border border-[#1F2430] space-y-1">
                  <span className="font-bold text-[#7C5CFF] block">Step 3: Toggle Memory OFF</span>
                  <p className="text-[#E6E8EE]">
                    Flip the <strong className="text-white">Memory OFF</strong> toggle to observe the contrast with generic LLM advice.
                  </p>
                </div>

                <div className="p-3 bg-[#0B0D12] rounded-12 border border-[#1F2430] space-y-1">
                  <span className="font-bold text-[#2DD4A0] block">Step 4: View Learning Curve</span>
                  <p className="text-[#E6E8EE]">
                    Visit <strong className="text-white">Insights (/insights)</strong> to see how prediction accuracy rises and MTTR falls over time.
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
