'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert,
  ArrowRight,
  Sparkles,
  GitPullRequest,
  CheckCircle2,
  AlertOctagon,
  Brain,
  TrendingUp,
  Code2,
  Activity,
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { Card, Badge, Button, CopyButton } from '../components/UIComponents';

export default function LandingPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [activeSnippetTab, setActiveSnippetTab] = useState<'cli' | 'python' | 'github' | 'curl'>('cli');

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % 4);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const demoSteps = [
    {
      id: 0,
      title: '1. Change Submitted',
      subtitle: 'PR #402: Lower gateway retry timeout 30s → 8s',
      badge: 'GitHub PR',
      badgeColor: 'primary' as const,
      content: (
        <div className="space-y-3 font-mono text-xs">
          <div className="flex items-center gap-2 text-[#8A90A2]">
            <GitPullRequest className="w-4 h-4 text-[#7C5CFF]" />
            <span className="text-[#E6E8EE]">payments-gateway / diff</span>
          </div>
          <div className="bg-[#0B0D12] p-3 rounded-12 border border-[#1F2430] text-[#E6E8EE] space-y-1">
            <p className="text-[#FF4D6D]">- const GATEWAY_RETRY_TIMEOUT_MS = 30000;</p>
            <p className="text-[#2DD4A0]">+ const GATEWAY_RETRY_TIMEOUT_MS = 8000;</p>
          </div>
          <p className="text-[#8A90A2] italic">Author: Arjun | Friday 5:40 PM</p>
        </div>
      ),
    },
    {
      id: 1,
      title: '2. Memory Recall',
      subtitle: 'Searching Hindsight bank foresight-paynest',
      badge: 'Hindsight Memory',
      badgeColor: 'warning' as const,
      content: (
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between text-[#8A90A2] font-mono">
            <span>Recall Query: "retry timeout 8s gateway"</span>
            <span className="text-[#2DD4A0]">3 Matches Found</span>
          </div>
          <div className="p-3 rounded-12 bg-[#FFB020]/10 border border-[#FFB020]/30 space-y-1">
            <p className="font-semibold text-[#FFB020]">INC-809 (Aug 12) & INC-912 (Sep 3)</p>
            <p className="text-[#E6E8EE]">
              Lowering retry timeout caused double-debit retry storms under 2M tx/day load.
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 2,
      title: '3. Cited Verdict',
      subtitle: 'Risk Score 87/100 | HOLD Enforced',
      badge: 'Foresight Agent',
      badgeColor: 'danger' as const,
      content: (
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-mono text-sm text-[#FF4D6D] font-bold">VERDICT: HOLD</span>
            <span className="px-2 py-0.5 rounded-full bg-[#FF4D6D]/20 text-[#FF4D6D] font-bold">
              Risk 87 / 100
            </span>
          </div>
          <p className="text-[#E6E8EE] bg-[#0B0D12] p-2.5 rounded-8 border border-[#1F2430]">
            "Do not ship without an idempotency-key validation and canary release. Similar timeout change caused 38 min outage."
          </p>
        </div>
      ),
    },
    {
      id: 3,
      title: '4. Outcome Retained',
      subtitle: 'Learning curve accuracy updated',
      badge: 'Continuous Learning',
      badgeColor: 'success' as const,
      content: (
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2 text-[#2DD4A0] font-semibold">
            <CheckCircle2 className="w-4 h-4" />
            <span>Outage Prevented & Outcome Retained in Hindsight</span>
          </div>
          <div className="flex items-center justify-between bg-[#0B0D12] p-2.5 rounded-8 border border-[#1F2430]">
            <span className="text-[#8A90A2]">Agent Accuracy:</span>
            <span className="text-[#2DD4A0] font-mono font-bold">94.8% (+1.2%)</span>
          </div>
        </div>
      ),
    },
  ];

  const snippets = {
    cli: `# Install and run deploy safety check directly in CLI
pip install foresight-cli
foresight check \\
  --service payments-gateway \\
  --title "Lower retry timeout from 30s to 8s" \\
  --diff ./change.diff`,

    python: `from foresight import ForesightClient

client = ForesightClient(api_key="fs_live_...")
verdict = client.check_deploy(
    service="payments-gateway",
    title="Lower retry timeout from 30s to 8s",
    config_changes=["PAYMENT_GATEWAY_RETRY_TIMEOUT_MS=8000"]
)

if verdict.verdict == "HOLD":
    print(f"Deployment blocked: {verdict.summary}")`,

    github: `name: Foresight Deploy Guard
on: [pull_request]

jobs:
  check-safety:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: foresight/action@v1
        with:
          api-key: \${{ secrets.FORESIGHT_API_KEY }}
          service: payments-gateway`,

    curl: `curl -X POST "https://api.foresight.dev/api/v1/deploys/check" \\
  -H "X-API-Key: fs_live_12345" \\
  -H "Content-Type: application/json" \\
  -d '{
    "service": "payments-gateway",
    "title": "Lower gateway retry timeout from 30s to 8s",
    "config_changes": ["PAYMENT_GATEWAY_RETRY_TIMEOUT_MS=8000"]
  }'`,
  };

  return (
    <div className="min-h-screen bg-[#0B0D12] flex flex-col">
      <Navbar />

      <main className="flex-1">
        <section className="relative pt-16 pb-20 px-4 sm:px-6 lg:px-8 hero-gradient overflow-hidden border-b border-[#1F2430]">
          <div className="max-w-6xl mx-auto text-center space-y-8 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#7C5CFF]/15 border border-[#7C5CFF]/30 text-xs font-semibold text-[#9E85FF] shadow-glow">
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Deploy-Safety Agent for Fintech & Payments</span>
            </div>

            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
              Hindsight remembers.{' '}
              <span className="bg-gradient-to-r from-[#7C5CFF] via-[#9E85FF] to-[#2DD4A0] bg-clip-text text-transparent">
                Foresight prevents.
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-[#8A90A2] max-w-2xl mx-auto leading-relaxed">
              Before a risky change ships, Foresight compares it against your team's full incident history in Hindsight memory—citing past outages, temporary fixes, and failed attempts.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Link href="/check">
                <Button size="lg" className="w-full sm:w-auto gap-2 text-base">
                  <span>Try the Live Demo</span>
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link href="/demo">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto gap-2 text-base">
                  <Activity className="w-5 h-5 text-[#2DD4A0]" />
                  <span>Replay Demo Timeline</span>
                </Button>
              </Link>
            </div>

            <div className="mt-12 max-w-4xl mx-auto text-left">
              <Card className="border-[#1F2430] bg-[#12151C]/90 shadow-2xl overflow-hidden p-0">
                <div className="px-5 py-3 bg-[#0B0D12] border-b border-[#1F2430] flex items-center justify-between text-xs text-[#8A90A2]">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#FF4D6D]/80" />
                    <div className="w-3 h-3 rounded-full bg-[#FFB020]/80" />
                    <div className="w-3 h-3 rounded-full bg-[#2DD4A0]/80" />
                    <span className="ml-2 font-mono text-[#E6E8EE] font-semibold">
                      Foresight Safety Cycle (20s Loop)
                    </span>
                  </div>
                  <span className="font-mono text-[#7C5CFF]">Step {activeStep + 1} of 4</span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 border-b border-[#1F2430]">
                  {demoSteps.map((step) => (
                    <button
                      key={step.id}
                      onClick={() => setActiveStep(step.id)}
                      className={`p-3 text-left border-r last:border-r-0 border-[#1F2430] transition-colors relative ${
                        activeStep === step.id ? 'bg-[#1A1E29]' : 'hover:bg-[#12151C]'
                      }`}
                    >
                      <p className="text-xs font-bold text-[#E6E8EE] truncate">{step.title}</p>
                      {activeStep === step.id && (
                        <motion.div
                          className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#7C5CFF]"
                          layoutId="activeTabUnderline"
                        />
                      )}
                    </button>
                  ))}
                </div>

                <div className="p-6 min-h-[160px] flex flex-col justify-between">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeStep}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.3 }}
                      className="space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-[#E6E8EE]">
                          {demoSteps[activeStep].subtitle}
                        </span>
                        <Badge variant={demoSteps[activeStep].badgeColor}>
                          {demoSteps[activeStep].badge}
                        </Badge>
                      </div>
                      {demoSteps[activeStep].content}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </Card>
            </div>
          </div>
        </section>

        <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
              Why Memory is the Core Difference
            </h2>
            <p className="text-sm sm:text-base text-[#8A90A2] max-w-xl mx-auto">
              Without memory, AI agents give generic advice ("add tests"). With Hindsight memory, Foresight cites exact past outages, temporary fixes, and config drift patterns.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card glow glowColor="danger" className="space-y-4">
              <div className="w-10 h-10 rounded-12 bg-[#FF4D6D]/15 border border-[#FF4D6D]/30 flex items-center justify-center text-[#FF4D6D]">
                <AlertOctagon className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">1. Intercept & Prevent</h3>
              <p className="text-sm text-[#8A90A2] leading-relaxed">
                Reads every PR and config change before deployment. Flags retry storms, certificate drift, and database failover traps based on past team incidents.
              </p>
            </Card>

            <Card glow glowColor="primary" className="space-y-4">
              <div className="w-10 h-10 rounded-12 bg-[#7C5CFF]/15 border border-[#7C5CFF]/30 flex items-center justify-center text-[#7C5CFF]">
                <Brain className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">2. Deep Memory Recall</h3>
              <p className="text-sm text-[#8A90A2] leading-relaxed">
                Connects directly to Hindsight memory bank. Recalls what fix worked, what failed, and which fixes held for only a few days before reverting.
              </p>
            </Card>

            <Card glow glowColor="success" className="space-y-4">
              <div className="w-10 h-10 rounded-12 bg-[#2DD4A0]/15 border border-[#2DD4A0]/30 flex items-center justify-center text-[#2DD4A0]">
                <TrendingUp className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">3. Continuous Learning</h3>
              <p className="text-sm text-[#8A90A2] leading-relaxed">
                Every deploy check outcome and resolved incident is retained back into memory, continuously increasing prediction accuracy and reducing MTTR over time.
              </p>
            </Card>
          </div>
        </section>

        <section className="py-16 px-4 sm:px-6 lg:px-8 bg-[#12151C]/40 border-t border-[#1F2430]">
          <div className="max-w-5xl mx-auto space-y-8">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-white">Seamless Developer Integration</h2>
              <p className="text-sm text-[#8A90A2]">
                Integrate Foresight into your CI/CD pipelines, CLI workflows, or payment microservices in minutes.
              </p>
            </div>

            <Card className="p-0 border-[#1F2430] overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3 bg-[#0B0D12] border-b border-[#1F2430]">
                <div className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-[#7C5CFF]" />
                  <span className="text-xs font-mono font-bold text-[#E6E8EE]">Integration Examples</span>
                </div>
                <div className="flex items-center gap-1">
                  {(['cli', 'python', 'github', 'curl'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveSnippetTab(tab)}
                      className={`px-3 py-1 rounded-8 text-xs font-mono transition-colors ${
                        activeSnippetTab === tab
                          ? 'bg-[#7C5CFF] text-white font-bold'
                          : 'text-[#8A90A2] hover:text-[#E6E8EE]'
                      }`}
                    >
                      {tab.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-5 bg-[#0B0D12] font-mono text-xs text-[#E6E8EE] overflow-x-auto relative">
                <div className="absolute top-4 right-4">
                  <CopyButton text={snippets[activeSnippetTab]} label="Copy Code" />
                </div>
                <pre className="text-[#9E85FF] leading-relaxed whitespace-pre">
                  {snippets[activeSnippetTab]}
                </pre>
              </div>
            </Card>
          </div>
        </section>
      </main>

      <footer className="py-8 px-4 border-t border-[#1F2430] text-center text-xs text-[#8A90A2]">
        <p>Foresight | Powered by Hindsight Memory Cloud & Groq API</p>
      </footer>
    </div>
  );
}
