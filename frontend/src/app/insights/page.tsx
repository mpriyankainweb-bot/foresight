'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Database,
  RefreshCw,
} from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Card, Badge, Skeleton, EmptyState, ErrorBanner } from '../../components/UIComponents';
import { api, AnalyticsResponse } from '../../lib/api';

export default function InsightsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics learning curve data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const chartData =
    data?.data_points?.map((dp) => ({
      date: dp.date,
      accuracy: Math.round(dp.prediction_accuracy * 100),
      mttr: Math.round(dp.mttr_minutes),
      memories: dp.memory_count,
    })) || [];

  return (
    <div className="min-h-screen bg-[#0B0D12] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#12151C] p-6 rounded-16 border border-[#1F2430]">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-extrabold text-white">Agent Learning Curve</h1>
              <Badge variant="primary">
                <TrendingUp className="w-3.5 h-3.5 mr-1" /> Analytics & Memory Growth
              </Badge>
            </div>
            <p className="text-sm text-[#8A90A2]">
              Track risk prediction accuracy and MTTR reduction as PayNest's Hindsight memory bank grows.
            </p>
          </div>

          <button
            onClick={loadData}
            className="p-2 rounded-12 bg-[#0B0D12] border border-[#1F2430] text-[#8A90A2] hover:text-white transition-colors"
            title="Refresh analytics data"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : error ? (
          <ErrorBanner message={error} onRetry={loadData} />
        ) : !data ? (
          <EmptyState
            icon={TrendingUp}
            title="No Learning Curve Data Available"
            description="Replay the demo timeline or run deploy checks to accumulate learning curve data points."
          />
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card glow glowColor="primary" className="space-y-2">
                <div className="flex items-center justify-between text-xs text-[#8A90A2]">
                  <span>Total Memory Records</span>
                  <Database className="w-4 h-4 text-[#7C5CFF]" />
                </div>
                <div className="text-3xl font-extrabold font-mono text-white">
                  {chartData[chartData.length - 1]?.memories || 0}
                </div>
                <p className="text-xs text-[#2DD4A0]">
                  Active bank: <span className="font-mono">foresight-paynest</span>
                </p>
              </Card>

              <Card glow glowColor="success" className="space-y-2">
                <div className="flex items-center justify-between text-xs text-[#8A90A2]">
                  <span>Risk Prediction Accuracy</span>
                  <CheckCircle2 className="w-4 h-4 text-[#2DD4A0]" />
                </div>
                <div className="text-3xl font-extrabold font-mono text-[#2DD4A0]">
                  {(data.current_accuracy * 100).toFixed(1)}%
                </div>
                <p className="text-xs text-[#8A90A2]">
                  Up from {chartData[0]?.accuracy || 60}% at bank creation
                </p>
              </Card>

              <Card glow glowColor="warning" className="space-y-2">
                <div className="flex items-center justify-between text-xs text-[#8A90A2]">
                  <span>Mean Time To Resolve (MTTR)</span>
                  <Clock className="w-4 h-4 text-[#FFB020]" />
                </div>
                <div className="text-3xl font-extrabold font-mono text-[#FFB020]">
                  {data.current_mttr_minutes.toFixed(0)} mins
                </div>
                <p className="text-xs text-[#2DD4A0]">
                  Reduced by {Math.round((chartData[0]?.mttr || 90) - data.current_mttr_minutes)} mins
                </p>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#2DD4A0]" />
                    Risk Prediction Accuracy Trend (%)
                  </h3>
                  <Badge variant="success">+{(data.current_accuracy * 100 - (chartData[0]?.accuracy || 60)).toFixed(1)}% Gain</Badge>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsLineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1F2430" />
                      <XAxis dataKey="date" stroke="#8A90A2" fontSize={11} tickLine={false} />
                      <YAxis domain={[50, 100]} stroke="#8A90A2" fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#12151C',
                          borderColor: '#1F2430',
                          borderRadius: '12px',
                          color: '#E6E8EE',
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="accuracy"
                        stroke="#2DD4A0"
                        strokeWidth={3}
                        dot={{ fill: '#2DD4A0', r: 4 }}
                      />
                    </RechartsLineChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              <Card className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Clock className="w-4 h-4 text-[#FFB020]" />
                    MTTR (Mean Time To Resolve) Reduction (Mins)
                  </h3>
                  <Badge variant="warning">-42m Resolution Time</Badge>
                </div>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsLineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1F2430" />
                      <XAxis dataKey="date" stroke="#8A90A2" fontSize={11} tickLine={false} />
                      <YAxis stroke="#8A90A2" fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#12151C',
                          borderColor: '#1F2430',
                          borderRadius: '12px',
                          color: '#E6E8EE',
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="mttr"
                        stroke="#FFB020"
                        strokeWidth={3}
                        dot={{ fill: '#FFB020', r: 4 }}
                      />
                    </RechartsLineChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Flame className="w-4 h-4 text-[#FF4D6D]" />
                  Top Recurring Root Cause Classes
                </h3>

                <div className="space-y-3">
                  {data.top_recurring_causes?.map((cause, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-[#0B0D12] border border-[#1F2430] rounded-12 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[#7C5CFF] font-bold">#{idx + 1}</span>
                        <span className="font-medium text-[#E6E8EE]">{cause.cause}</span>
                      </div>
                      <Badge variant="danger">{cause.count} Incidents</Badge>
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#FFB020]" />
                  Fixes That Only Held Temporarily
                </h3>

                <div className="space-y-3">
                  {data.temporary_fixes?.map((temp, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-[#0B0D12] border border-[#1F2430] rounded-12 space-y-1.5 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[#7C5CFF] font-bold">
                          {temp.incident_id}
                        </span>
                        <span className="text-[#FFB020] font-mono font-bold">
                          Held for {temp.held_for_days} days
                        </span>
                      </div>
                      <p className="text-[#E6E8EE]">{temp.description}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}
