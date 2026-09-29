'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitPullRequest,
  Brain,
  AlertTriangle,
  CheckCircle2,
  AlertOctagon,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ShieldAlert,
  Database,
  Clock,
} from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { RiskGauge } from '../../components/RiskGauge';
import { Card, Badge, Button, CopyButton, Skeleton, EmptyState, ErrorBanner } from '../../components/UIComponents';
import { useAppState } from '../providers';
import { api, DeployCheckResponse } from '../../lib/api';

const FRIDAY_540_EXAMPLE = {
  service: 'payments-gateway',
  title: 'Lower gateway retry timeout from 30s to 8s',
  description:
    'Lowering gateway retry timeout from 30s to 8s to improve user-perceived responsiveness during upstream latency spikes.',
  config_changes: ['PAYMENT_GATEWAY_RETRY_TIMEOUT_MS=8000'],
  diff: `- const GATEWAY_RETRY_TIMEOUT_MS = 30000;
+ const GATEWAY_RETRY_TIMEOUT_MS = 8000;`,
  environment: 'production',
  author: 'Arjun',
};

const CERT_EXPIRY_EXAMPLE = {
  service: 'auth-service',
  title: 'Rotate TLS certs for auth domain',
  description: 'Updating expired TLS certificates across internal auth proxies.',
  config_changes: ['TLS_CERT_PATH=/etc/ssl/certs/2026_auth.pem'],
  diff: `- TLS_CERT_VALID_UNTIL=2025-08-01
+ TLS_CERT_VALID_UNTIL=2026-08-01`,
  environment: 'production',
  author: 'Priya',
};

export default function DeployCheckPage() {
  const { memoryEnabled, toggleMemory, openMemoryInspectorWithQuery } = useAppState();

  const [form, setForm] = useState({
    service: 'payments-gateway',
    title: 'Lower gateway retry timeout from 30s to 8s',
    description:
      'Lowering gateway retry timeout from 30s to 8s to improve user-perceived responsiveness during upstream latency spikes.',
    diff: `- const GATEWAY_RETRY_TIMEOUT_MS = 30000;
+ const GATEWAY_RETRY_TIMEOUT_MS = 8000;`,
    config_changes_input: 'PAYMENT_GATEWAY_RETRY_TIMEOUT_MS=8000',
    environment: 'production',
    author: 'Arjun',
  });

  const [result, setResult] = useState<DeployCheckResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedIncidents, setExpandedIncidents] = useState<Record<string, boolean>>({});

  const [outcomeLogged, setOutcomeLogged] = useState<string | null>(null);
  const [outcomeNotes, setOutcomeNotes] = useState('');
  const [isLoggingOutcome, setIsLoggingOutcome] = useState(false);

  const handleExampleSelect = (exampleName: string) => {
    if (exampleName === 'friday_540') {
      setForm({
        service: FRIDAY_540_EXAMPLE.service,
        title: FRIDAY_540_EXAMPLE.title,
        description: FRIDAY_540_EXAMPLE.description,
        diff: FRIDAY_540_EXAMPLE.diff,
        config_changes_input: FRIDAY_540_EXAMPLE.config_changes[0],
        environment: FRIDAY_540_EXAMPLE.environment,
        author: FRIDAY_540_EXAMPLE.author,
      });
    } else if (exampleName === 'cert_expiry') {
      setForm({
        service: CERT_EXPIRY_EXAMPLE.service,
        title: CERT_EXPIRY_EXAMPLE.title,
        description: CERT_EXPIRY_EXAMPLE.description,
        diff: CERT_EXPIRY_EXAMPLE.diff,
        config_changes_input: CERT_EXPIRY_EXAMPLE.config_changes[0],
        environment: CERT_EXPIRY_EXAMPLE.environment,
        author: CERT_EXPIRY_EXAMPLE.author,
      });
    }
  };

  const runCheck = async (overrideMemory?: boolean) => {
    setIsLoading(true);
    setError(null);
    setOutcomeLogged(null);

    const useMem = overrideMemory !== undefined ? overrideMemory : memoryEnabled;
    const configChanges = form.config_changes_input
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      const res = await api.checkDeploy({
        service: form.service,
        title: form.title,
        description: form.description,
        diff: form.diff,
        config_changes: configChanges,
        environment: form.environment,
        author: form.author,
        memory_enabled: useMem,
      });
      setResult(res);

      const initialExpanded: Record<string, boolean> = {};
      res.similar_incidents?.forEach((inc) => {
        initialExpanded[inc.id] = true;
      });
      setExpandedIncidents(initialExpanded);
    } catch (err: any) {
      setError(err.message || 'Failed to run deploy check');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogOutcome = async (outcome: 'clean' | 'degraded' | 'incident') => {
    if (!result?.check_id) return;
    setIsLoggingOutcome(true);
    try {
      await api.recordOutcome(result.check_id, {
        outcome,
        notes: outcomeNotes || `Recorded ${outcome} outcome via UI`,
      });
      setOutcomeLogged(outcome);
    } catch (err: any) {
      alert(`Error recording outcome: ${err.message}`);
    } finally {
      setIsLoggingOutcome(false);
    }
  };

  const toggleIncidentExpand = (id: string) => {
    setExpandedIncidents((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="min-h-screen bg-[#0B0D12] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#12151C] p-6 rounded-16 border border-[#1F2430]">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-extrabold text-white">Deploy Safety Guard</h1>
              <Badge variant="primary">
                <GitPullRequest className="w-3.5 h-3.5 mr-1" /> Check Engine
              </Badge>
            </div>
            <p className="text-sm text-[#8A90A2]">
              Simulate or evaluate PR changes against PayNest&apos;s incident memory bank.
            </p>
          </div>

          <div className="flex items-center gap-4 bg-[#0B0D12] p-2 rounded-12 border border-[#1F2430]">
            <div className="flex items-center gap-2 px-2 text-xs text-[#8A90A2]">
              <Brain className={`w-4 h-4 ${memoryEnabled ? 'text-[#7C5CFF]' : 'text-[#8A90A2]'}`} />
              <span>Memory Recall:</span>
            </div>
            <button
              onClick={() => {
                toggleMemory();
                if (result) {
                  runCheck(!memoryEnabled);
                }
              }}
              className={`px-3 py-1.5 rounded-8 text-xs font-bold transition-all ${
                memoryEnabled
                  ? 'bg-[#7C5CFF] text-white shadow-glow'
                  : 'bg-[#1F2430] text-[#8A90A2] hover:text-white'
              }`}
            >
              {memoryEnabled ? 'ON (Cited Answers)' : 'OFF (Generic Advice)'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6">
            <Card className="space-y-5">
              <div className="flex items-center justify-between border-b border-[#1F2430] pb-4">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#7C5CFF]" />
                  Change Parameters
                </h2>

                <div className="relative">
                  <select
                    onChange={(e) => handleExampleSelect(e.target.value)}
                    className="bg-[#0B0D12] border border-[#1F2430] text-xs font-mono text-[#9E85FF] rounded-8 px-2.5 py-1.5 cursor-pointer focus:border-[#7C5CFF] focus:outline-none"
                    defaultValue="friday_540"
                  >
                    <option value="" disabled>
                      Load Example Scenario...
                    </option>
                    <option value="friday_540">Friday 5:40 PM Retry Timeout (INC-809)</option>
                    <option value="cert_expiry">TLS Cert Expiry Rotation (INC-302)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Service Name</label>
                  <input
                    type="text"
                    value={form.service}
                    onChange={(e) => setForm({ ...form, service: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white font-mono focus:border-[#7C5CFF] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">PR / Change Title</label>
                  <input
                    type="text"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#7C5CFF] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Change Description</label>
                  <textarea
                    rows={2}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#7C5CFF] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Config Key Changes (comma separated)</label>
                  <input
                    type="text"
                    value={form.config_changes_input}
                    onChange={(e) => setForm({ ...form, config_changes_input: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm font-mono text-[#9E85FF] focus:border-[#7C5CFF] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Git Diff / Code Context</label>
                  <textarea
                    rows={4}
                    value={form.diff}
                    onChange={(e) => setForm({ ...form, diff: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 p-3 text-xs font-mono text-[#2DD4A0] focus:border-[#7C5CFF] focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[#8A90A2] font-medium mb-1">Environment</label>
                    <input
                      type="text"
                      value={form.environment}
                      onChange={(e) => setForm({ ...form, environment: e.target.value })}
                      className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#7C5CFF] focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[#8A90A2] font-medium mb-1">Author</label>
                    <input
                      type="text"
                      value={form.author}
                      onChange={(e) => setForm({ ...form, author: e.target.value })}
                      className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#7C5CFF] focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <Button
                variant="primary"
                size="lg"
                className="w-full gap-2 mt-4"
                isLoading={isLoading}
                onClick={() => runCheck()}
              >
                <ShieldAlert className="w-5 h-5" />
                <span>Run Safety Check</span>
              </Button>
            </Card>
          </div>

          <div className="lg:col-span-7 space-y-6">
            {isLoading ? (
              <Card className="space-y-6">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-8 w-40" />
                  <Skeleton className="h-8 w-24" />
                </div>
                <div className="flex justify-center my-6">
                  <Skeleton className="h-44 w-44 rounded-full" />
                </div>
                <Skeleton className="h-20 w-full" />
                <Skeleton className="h-32 w-full" />
              </Card>
            ) : error ? (
              <ErrorBanner message={error} onRetry={() => runCheck()} />
            ) : !result ? (
              <EmptyState
                icon={GitPullRequest}
                title="Ready for Deploy Check"
                description="Click 'Run Safety Check' or select an example scenario from the dropdown to analyze risks against incident memory."
                action={
                  <Button variant="primary" onClick={() => runCheck()}>
                    Run Friday 5:40 PM Scenario
                  </Button>
                }
              />
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-6"
              >
                <Card
                  glow
                  glowColor={
                    result.verdict === 'HOLD'
                      ? 'danger'
                      : result.verdict === 'CANARY'
                      ? 'warning'
                      : 'success'
                  }
                  className="space-y-6"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1F2430] pb-5">
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-3 rounded-16 border ${
                          result.verdict === 'HOLD'
                            ? 'bg-[#FF4D6D]/15 text-[#FF4D6D] border-[#FF4D6D]/30'
                            : result.verdict === 'CANARY'
                            ? 'bg-[#FFB020]/15 text-[#FFB020] border-[#FFB020]/30'
                            : 'bg-[#2DD4A0]/15 text-[#2DD4A0] border-[#2DD4A0]/30'
                        }`}
                      >
                        {result.verdict === 'HOLD' ? (
                          <AlertOctagon className="w-8 h-8" />
                        ) : result.verdict === 'CANARY' ? (
                          <AlertTriangle className="w-8 h-8" />
                        ) : (
                          <CheckCircle2 className="w-8 h-8" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-2xl font-black tracking-tight font-mono ${
                              result.verdict === 'HOLD'
                                ? 'text-[#FF4D6D]'
                                : result.verdict === 'CANARY'
                                ? 'text-[#FFB020]'
                                : 'text-[#2DD4A0]'
                            }`}
                          >
                            VERDICT: {result.verdict}
                          </span>
                        </div>
                        <p className="text-xs text-[#8A90A2]">
                          Deploy Check ID: <span className="font-mono text-[#E6E8EE]">{result.check_id}</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge variant={result.memory_used ? 'primary' : 'outline'}>
                        <Brain className="w-3.5 h-3.5 mr-1" />
                        {result.memory_used ? 'Memory Recalled' : 'Memory OFF'}
                      </Badge>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-6 items-center">
                    <div className="sm:col-span-5 flex justify-center">
                      <RiskGauge score={result.risk_score} verdict={result.verdict} size={190} />
                    </div>

                    <div className="sm:col-span-7 space-y-3">
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider text-[#8A90A2]">
                        Verdict Summary
                      </h3>
                      <p className="text-sm text-[#E6E8EE] leading-relaxed bg-[#0B0D12] p-4 rounded-12 border border-[#1F2430]">
                        {result.summary}
                      </p>
                    </div>
                  </div>

                  {result.reasons && result.reasons.length > 0 && (
                    <div className="space-y-2 border-t border-[#1F2430] pt-4">
                      <h4 className="text-xs font-bold text-[#8A90A2] uppercase tracking-wider">
                        Risk Factor Analysis ({result.reasons.length})
                      </h4>
                      <ul className="space-y-1.5 text-xs text-[#E6E8EE]">
                        {result.reasons.map((reason, idx) => (
                          <li key={idx} className="flex items-start gap-2 bg-[#12151C] p-2.5 rounded-8 border border-[#1F2430]/60">
                            <span className="text-[#FF4D6D] font-bold">•</span>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Card>

                <Card className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Clock className="w-4 h-4 text-[#7C5CFF]" />
                      Similar Past Incidents ({result.similar_incidents?.length || 0})
                    </h3>
                    {result.memory_citations?.length > 0 && (
                      <button
                        onClick={() => openMemoryInspectorWithQuery(form.title)}
                        className="text-xs text-[#7C5CFF] hover:underline flex items-center gap-1 font-mono"
                      >
                        <Database className="w-3.5 h-3.5" />
                        View in Inspector ({result.memory_citations.length})
                      </button>
                    )}
                  </div>

                  {result.similar_incidents?.length === 0 ? (
                    <p className="text-xs text-[#8A90A2] italic">
                      No similar past incidents recorded for this change.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {result.similar_incidents?.map((inc) => {
                        const isExpanded = !!expandedIncidents[inc.id];
                        return (
                          <div
                            key={inc.id}
                            className="bg-[#0B0D12] border border-[#1F2430] rounded-12 overflow-hidden transition-all"
                          >
                            <button
                              onClick={() => toggleIncidentExpand(inc.id)}
                              className="w-full p-3.5 flex items-center justify-between text-left hover:bg-[#12151C] transition-colors"
                            >
                              <div className="space-y-0.5">
                                <div className="flex items-center gap-2">
                                  <span className="font-mono text-xs text-[#7C5CFF] font-bold">
                                    {inc.id}
                                  </span>
                                  <span className="text-xs font-semibold text-[#E6E8EE]">
                                    {inc.title}
                                  </span>
                                </div>
                                <p className="text-[11px] text-[#8A90A2]">
                                  {inc.date} | {inc.similarity_reason}
                                </p>
                              </div>
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4 text-[#8A90A2]" />
                              ) : (
                                <ChevronDown className="w-4 h-4 text-[#8A90A2]" />
                              )}
                            </button>

                            <AnimatePresence>
                              {isExpanded && (
                                <motion.div
                                  initial={{ height: 0, opacity: 0 }}
                                  animate={{ height: 'auto', opacity: 1 }}
                                  exit={{ height: 0, opacity: 0 }}
                                  className="px-4 pb-4 pt-1 border-t border-[#1F2430]/60 space-y-2.5 text-xs"
                                >
                                  <div className="p-2.5 rounded-8 bg-[#2DD4A0]/10 border border-[#2DD4A0]/30 space-y-1">
                                    <span className="font-bold text-[#2DD4A0] uppercase text-[10px] tracking-wider block">
                                      ✓ Fix That Worked
                                    </span>
                                    <p className="text-[#E6E8EE]">{inc.fix_that_worked}</p>
                                  </div>

                                  {inc.fix_that_failed && (
                                    <div className="p-2.5 rounded-8 bg-[#FF4D6D]/10 border border-[#FF4D6D]/30 space-y-1">
                                      <span className="font-bold text-[#FF4D6D] uppercase text-[10px] tracking-wider block">
                                        ✗ Fix That Failed
                                      </span>
                                      <p className="text-[#E6E8EE]">{inc.fix_that_failed}</p>
                                    </div>
                                  )}

                                  {inc.held_for_days && (
                                    <p className="text-[11px] text-[#8A90A2] font-mono">
                                      Fix held for {inc.held_for_days} days before config drift recurred.
                                    </p>
                                  )}
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </Card>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Card className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-[#2DD4A0]" />
                        Canary Plan
                      </h4>
                      <CopyButton text={result.canary_plan} />
                    </div>
                    <p className="text-xs text-[#E6E8EE] bg-[#0B0D12] p-3 rounded-12 border border-[#1F2430] leading-relaxed font-mono">
                      {result.canary_plan}
                    </p>
                  </Card>

                  <Card className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                        <AlertOctagon className="w-4 h-4 text-[#FF4D6D]" />
                        Rollback Plan
                      </h4>
                      <CopyButton text={result.rollback_plan} />
                    </div>
                    <p className="text-xs text-[#E6E8EE] bg-[#0B0D12] p-3 rounded-12 border border-[#1F2430] leading-relaxed font-mono">
                      {result.rollback_plan}
                    </p>
                  </Card>
                </div>

                <Card className="space-y-4 border-[#7C5CFF]/30 bg-[#7C5CFF]/5">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Database className="w-4 h-4 text-[#7C5CFF]" />
                        Deploy Outcome Tracker
                      </h3>
                      <p className="text-xs text-[#8A90A2]">
                        Retain actual deploy outcome to improve future risk scoring accuracy
                      </p>
                    </div>

                    {outcomeLogged && (
                      <Badge variant="success">
                        Outcome Saved: {outcomeLogged.toUpperCase()}
                      </Badge>
                    )}
                  </div>

                  {!outcomeLogged ? (
                    <div className="space-y-3 pt-2">
                      <input
                        type="text"
                        placeholder="Optional notes (e.g. Success rate held at 99.98%, no retry storms)..."
                        value={outcomeNotes}
                        onChange={(e) => setOutcomeNotes(e.target.value)}
                        className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-xs text-white focus:border-[#7C5CFF] focus:outline-none"
                      />

                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          className="hover:border-[#2DD4A0] hover:text-[#2DD4A0]"
                          isLoading={isLoggingOutcome}
                          onClick={() => handleLogOutcome('clean')}
                        >
                          Report Clean (0 Outage)
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          className="hover:border-[#FFB020] hover:text-[#FFB020]"
                          isLoading={isLoggingOutcome}
                          onClick={() => handleLogOutcome('degraded')}
                        >
                          Report Degraded
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          className="hover:border-[#FF4D6D] hover:text-[#FF4D6D]"
                          isLoading={isLoggingOutcome}
                          onClick={() => handleLogOutcome('incident')}
                        >
                          Report Incident Caused
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-[#2DD4A0] bg-[#0B0D12] p-3 rounded-12 border border-[#2DD4A0]/30 font-mono">
                      ✓ Deploy outcome retained in Hindsight memory. The learning curve has been updated.
                    </p>
                  )}
                </Card>
              </motion.div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
