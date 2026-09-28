'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  AlertOctagon,
  Wrench,
  FileText,
  Sparkles,
  Plus,
} from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Card, Badge, Button, CopyButton, Skeleton, EmptyState, ErrorBanner } from '../../components/UIComponents';
import {
  api,
  CreateIncidentResponse,
  LogFixAttemptResponse,
  ResolveIncidentResponse,
} from '../../lib/api';

const EXAMPLE_INCIDENT = {
  service: 'payments-gateway',
  title: 'UPI Payment Retry Storm & Double-Debits',
  alerts: `[CRITICAL] payments-gateway success_rate < 91% (Current: 78.4%)
[HIGH] db-pool-exhaustion: payment_db active connections 100/100
[HIGH] upstream_timeout_spikes: gateway timeout 8s exceeded for 4,200 requests/min`,
  logs: `2025-09-03T17:41:02Z ERROR gateway.py:182 Timeout waiting for UPI switch response after 8000ms
2025-09-03T17:41:03Z WARN retry.py:44 Retrying payment_id=pay_982312 without idempotency lock
2025-09-03T17:41:04Z ERROR db.py:91 OperationalError: connection pool exhausted`,
};

export default function IncidentPage() {
  const [form, setForm] = useState({
    service: 'payments-gateway',
    title: 'UPI Payment Retry Storm & Double-Debits',
    alerts: EXAMPLE_INCIDENT.alerts,
    logs: EXAMPLE_INCIDENT.logs,
  });

  const [activeIncident, setActiveIncident] = useState<CreateIncidentResponse | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [fixAttemptForm, setFixAttemptForm] = useState({
    description: '',
    outcome: 'worked' as 'worked' | 'failed' | 'temporary',
    held_for_days: 0,
    notes: '',
  });
  const [fixAttempts, setFixAttempts] = useState<LogFixAttemptResponse[]>([]);
  const [isLoggingAttempt, setIsLoggingAttempt] = useState(false);

  const [resolveForm, setResolveForm] = useState({
    root_cause: 'Config drift: gateway retry timeout reduced to 8s without idempotency lock verification',
    resolution_notes: 'Reverted retry timeout to 30s and enabled Redis idempotency key lock.',
  });
  const [resolveResult, setResolveResult] = useState<ResolveIncidentResponse | null>(null);
  const [isResolving, setIsResolving] = useState(false);

  const handleCreateIncident = async () => {
    setIsCreating(true);
    setCreateError(null);
    setResolveResult(null);
    setFixAttempts([]);

    try {
      const res = await api.createIncident({
        service: form.service,
        title: form.title,
        alerts: form.alerts,
        logs: form.logs,
      });
      setActiveIncident(res);
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create incident');
    } finally {
      setIsCreating(false);
    }
  };

  const handleLogFixAttempt = async () => {
    if (!activeIncident) return;
    if (!fixAttemptForm.description.trim()) {
      alert('Please enter a fix attempt description');
      return;
    }

    setIsLoggingAttempt(true);
    try {
      const res = await api.logFixAttempt(activeIncident.incident_id, {
        description: fixAttemptForm.description,
        outcome: fixAttemptForm.outcome,
        held_for_days: fixAttemptForm.held_for_days || null,
        notes: fixAttemptForm.notes,
      });
      setFixAttempts((prev) => [res, ...prev]);
      setFixAttemptForm({ description: '', outcome: 'worked', held_for_days: 0, notes: '' });
    } catch (err: any) {
      alert(`Error logging fix attempt: ${err.message}`);
    } finally {
      setIsLoggingAttempt(false);
    }
  };

  const handleResolveIncident = async () => {
    if (!activeIncident) return;
    setIsResolving(true);
    try {
      const res = await api.resolveIncident(activeIncident.incident_id, {
        root_cause: resolveForm.root_cause,
        resolution_notes: resolveForm.resolution_notes,
      });
      setResolveResult(res);
    } catch (err: any) {
      alert(`Error resolving incident: ${err.message}`);
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0D12] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#12151C] p-6 rounded-16 border border-[#1F2430]">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-extrabold text-white">Live Incident Command</h1>
              <Badge variant="danger">
                <AlertTriangle className="w-3.5 h-3.5 mr-1" /> War Room Mode
              </Badge>
            </div>
            <p className="text-sm text-[#8A90A2]">
              Paste alerts or logs to query memory for ranked fixes, log fix attempts, and generate postmortems.
            </p>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setForm({
                service: EXAMPLE_INCIDENT.service,
                title: EXAMPLE_INCIDENT.title,
                alerts: EXAMPLE_INCIDENT.alerts,
                logs: EXAMPLE_INCIDENT.logs,
              });
            }}
            className="self-start md:self-auto gap-2"
          >
            <Sparkles className="w-4 h-4 text-[#7C5CFF]" />
            <span>Load Example Incident</span>
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6">
            <Card className="space-y-5">
              <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-[#1F2430] pb-3">
                <AlertOctagon className="w-4 h-4 text-[#FF4D6D]" />
                Incident Diagnostics Form
              </h2>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Affected Service</label>
                  <input
                    type="text"
                    value={form.service}
                    onChange={(e) => setForm({ ...form, service: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white font-mono focus:border-[#FF4D6D] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Incident Headline / Title</label>
                  <input
                    type="text"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#FF4D6D] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Alerts / Datadog Traces</label>
                  <textarea
                    rows={4}
                    value={form.alerts}
                    onChange={(e) => setForm({ ...form, alerts: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 p-3 text-xs font-mono text-[#FFB020] focus:border-[#FF4D6D] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Error Logs / Stacktraces</label>
                  <textarea
                    rows={4}
                    value={form.logs}
                    onChange={(e) => setForm({ ...form, logs: e.target.value })}
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 p-3 text-xs font-mono text-[#FF4D6D] focus:border-[#FF4D6D] focus:outline-none"
                  />
                </div>
              </div>

              <Button
                variant="danger"
                size="lg"
                className="w-full gap-2 mt-4"
                isLoading={isCreating}
                onClick={handleCreateIncident}
              >
                <Brain className="w-5 h-5" />
                <span>Search Incident Memory for Fixes</span>
              </Button>
            </Card>
          </div>

          <div className="lg:col-span-7 space-y-6">
            {isCreating ? (
              <Card className="space-y-4">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </Card>
            ) : createError ? (
              <ErrorBanner message={createError} onRetry={handleCreateIncident} />
            ) : !activeIncident ? (
              <EmptyState
                icon={AlertTriangle}
                title="No Active Incident In Context"
                description="Fill in alerts and logs on the left and click 'Search Incident Memory for Fixes' to recall historical solutions."
              />
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <Card className="space-y-4 border-[#FF4D6D]/40 bg-[#FF4D6D]/5">
                  <div className="flex items-center justify-between border-b border-[#1F2430] pb-3">
                    <div>
                      <span className="font-mono text-xs text-[#FF4D6D] font-bold">
                        {activeIncident.incident_id}
                      </span>
                      <h3 className="text-lg font-bold text-white">{activeIncident.title}</h3>
                    </div>
                    <Badge variant={resolveResult ? 'success' : 'danger'}>
                      {resolveResult ? 'RESOLVED' : 'ACTIVE INCIDENT'}
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                      <Wrench className="w-4 h-4 text-[#2DD4A0]" />
                      Ranked Fix Suggestions from Memory ({activeIncident.ranked_fix_suggestions?.length || 0})
                    </h4>

                    {activeIncident.ranked_fix_suggestions?.map((fix, idx) => (
                      <div
                        key={fix.id || idx}
                        className="p-4 bg-[#0B0D12] border border-[#1F2430] rounded-12 space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[#7C5CFF] font-bold">
                              #{idx + 1} Fix
                            </span>
                            <Badge
                              variant={
                                fix.outcome === 'worked'
                                  ? 'success'
                                  : fix.outcome === 'failed'
                                  ? 'danger'
                                  : 'warning'
                              }
                            >
                              {fix.outcome.toUpperCase()}
                            </Badge>
                          </div>
                          <span className="font-mono text-[#2DD4A0]">
                            Confidence: {(fix.confidence * 100).toFixed(0)}%
                          </span>
                        </div>

                        <p className="text-sm font-semibold text-white">{fix.description}</p>
                        <p className="text-xs text-[#8A90A2] bg-[#12151C] p-2.5 rounded-8">
                          {fix.reasoning}
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>

                {!resolveResult && (
                  <Card className="space-y-4">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Plus className="w-4 h-4 text-[#7C5CFF]" />
                      Log Fix Attempt
                    </h3>

                    <div className="space-y-3 text-xs">
                      <div>
                        <label className="block text-[#8A90A2] font-medium mb-1">Attempt Action</label>
                        <input
                          type="text"
                          placeholder="e.g. Reverted gateway retry timeout from 8s back to 30s"
                          value={fixAttemptForm.description}
                          onChange={(e) =>
                            setFixAttemptForm({ ...fixAttemptForm, description: e.target.value })
                          }
                          className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#7C5CFF] focus:outline-none"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-[#8A90A2] font-medium mb-1">Outcome</label>
                          <select
                            value={fixAttemptForm.outcome}
                            onChange={(e) =>
                              setFixAttemptForm({
                                ...fixAttemptForm,
                                outcome: e.target.value as any,
                              })
                            }
                            className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-xs text-white focus:border-[#7C5CFF] focus:outline-none"
                          >
                            <option value="worked">Worked</option>
                            <option value="failed">Failed</option>
                            <option value="temporary">Temporary Fix</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-[#8A90A2] font-medium mb-1">Held for (Days)</label>
                          <input
                            type="number"
                            value={fixAttemptForm.held_for_days}
                            onChange={(e) =>
                              setFixAttemptForm({
                                ...fixAttemptForm,
                                held_for_days: parseInt(e.target.value) || 0,
                              })
                            }
                            className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#7C5CFF] focus:outline-none"
                          />
                        </div>
                      </div>

                      <Button
                        variant="secondary"
                        size="sm"
                        className="w-full gap-2"
                        isLoading={isLoggingAttempt}
                        onClick={handleLogFixAttempt}
                      >
                        <Wrench className="w-4 h-4 text-[#7C5CFF]" />
                        <span>Log Attempt to Incident Memory</span>
                      </Button>
                    </div>

                    {fixAttempts.length > 0 && (
                      <div className="space-y-2 border-t border-[#1F2430] pt-3">
                        <span className="text-xs text-[#8A90A2] font-mono">Logged Attempts ({fixAttempts.length}):</span>
                        {fixAttempts.map((attempt) => (
                          <div
                            key={attempt.attempt_id}
                            className="flex items-center justify-between p-2.5 bg-[#0B0D12] rounded-8 border border-[#1F2430] text-xs"
                          >
                            <span className="font-mono text-[#E6E8EE]">Attempt #{attempt.attempt_id}</span>
                            <Badge
                              variant={
                                attempt.outcome === 'worked'
                                  ? 'success'
                                  : attempt.outcome === 'failed'
                                  ? 'danger'
                                  : 'warning'
                              }
                            >
                              {attempt.outcome.toUpperCase()}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                )}

                {!resolveResult ? (
                  <Card className="space-y-4 border-[#2DD4A0]/30 bg-[#2DD4A0]/5">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-[#2DD4A0]" />
                      Resolve & Generate Postmortem Draft
                    </h3>

                    <div className="space-y-3 text-xs">
                      <div>
                        <label className="block text-[#8A90A2] font-medium mb-1">Confirmed Root Cause</label>
                        <input
                          type="text"
                          value={resolveForm.root_cause}
                          onChange={(e) =>
                            setResolveForm({ ...resolveForm, root_cause: e.target.value })
                          }
                          className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-xs text-white focus:border-[#2DD4A0] focus:outline-none"
                        />
                      </div>

                      <div>
                        <label className="block text-[#8A90A2] font-medium mb-1">Resolution Notes</label>
                        <textarea
                          rows={2}
                          value={resolveForm.resolution_notes}
                          onChange={(e) =>
                            setResolveForm({ ...resolveForm, resolution_notes: e.target.value })
                          }
                          className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-xs text-white focus:border-[#2DD4A0] focus:outline-none"
                        />
                      </div>

                      <Button
                        variant="primary"
                        size="lg"
                        className="w-full gap-2 bg-[#2DD4A0] hover:bg-[#22B889] text-black font-bold"
                        isLoading={isResolving}
                        onClick={handleResolveIncident}
                      >
                        <FileText className="w-5 h-5" />
                        <span>Resolve Incident & Retain Postmortem</span>
                      </Button>
                    </div>
                  </Card>
                ) : (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="space-y-4"
                  >
                    <Card className="space-y-4 border-[#2DD4A0] bg-[#12151C]">
                      <div className="flex items-center justify-between border-b border-[#1F2430] pb-3">
                        <div className="flex items-center gap-2">
                          <FileText className="w-5 h-5 text-[#2DD4A0]" />
                          <h3 className="text-base font-bold text-white">Generated Postmortem Draft</h3>
                        </div>
                        <CopyButton
                          text={JSON.stringify(resolveResult.postmortem, null, 2)}
                          label="Copy Postmortem JSON"
                        />
                      </div>

                      <div className="space-y-3 text-xs bg-[#0B0D12] p-4 rounded-12 border border-[#1F2430]">
                        <h4 className="text-sm font-bold text-[#2DD4A0]">
                          {resolveResult.postmortem.title}
                        </h4>
                        <p className="text-[#E6E8EE] leading-relaxed">
                          {resolveResult.postmortem.summary}
                        </p>

                        <div className="pt-2 border-t border-[#1F2430] space-y-2">
                          <p className="font-bold text-[#FFB020]">
                            Root Cause: <span className="text-[#E6E8EE] font-normal">{resolveResult.postmortem.root_cause}</span>
                          </p>
                          <p className="font-bold text-[#2DD4A0]">
                            Fix That Worked: <span className="text-[#E6E8EE] font-normal">{resolveResult.postmortem.fix_that_worked}</span>
                          </p>
                        </div>

                        {resolveResult.postmortem.action_items?.length > 0 && (
                          <div className="pt-2 border-t border-[#1F2430]">
                            <span className="font-bold text-[#7C5CFF]">Action Items:</span>
                            <ul className="list-disc list-inside mt-1 space-y-1 text-[#8A90A2]">
                              {resolveResult.postmortem.action_items.map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </Card>
                  </motion.div>
                )}
              </motion.div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
