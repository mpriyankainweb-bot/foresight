'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search, Database, Tag, Cpu, RefreshCw, Sparkles } from 'lucide-react';
import { useAppState } from '../app/providers';
import { api, MemorySearchResultItem } from '../lib/api';
import { Badge, Skeleton, EmptyState } from './UIComponents';

export function MemoryInspectorDrawer() {
  const {
    memoryInspectorOpen,
    setMemoryInspectorOpen,
    inspectorSearchQuery,
  } = useAppState();

  const [query, setQuery] = useState(inspectorSearchQuery);
  const [results, setResults] = useState<MemorySearchResultItem[]>([]);
  const [backendMode, setBackendMode] = useState<string>('mock');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setQuery(inspectorSearchQuery);
  }, [inspectorSearchQuery]);

  const handleSearch = async (searchStr: string) => {
    if (!searchStr.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.searchMemory(searchStr);
      setResults(res.results || []);
      setBackendMode(res.memory_backend || 'mock');
    } catch (err: any) {
      setError(err.message || 'Failed to query memory bank');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (memoryInspectorOpen && query) {
      handleSearch(query);
    }
  }, [memoryInspectorOpen, inspectorSearchQuery]);

  return (
    <AnimatePresence>
      {memoryInspectorOpen && (
        <>
          <motion.div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMemoryInspectorOpen(false)}
          />

          <motion.div
            className="fixed top-0 right-0 bottom-0 w-full max-w-xl bg-[#0B0D12] border-l border-[#1F2430] z-50 flex flex-col shadow-2xl overflow-hidden"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          >
            <div className="p-5 border-b border-[#1F2430] bg-[#12151C] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-12 bg-[#7C5CFF]/15 border border-[#7C5CFF]/30 text-[#9E85FF]">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-[#E6E8EE] flex items-center gap-2">
                    Memory Inspector
                    <span className="text-xs px-2 py-0.5 rounded-full bg-[#1F2430] text-[#8A90A2] font-mono">
                      bank: foresight-paynest
                    </span>
                  </h2>
                  <p className="text-xs text-[#8A90A2]">
                    Inspect live Hindsight memories recalled for deploys & incidents
                  </p>
                </div>
              </div>
              <button
                onClick={() => setMemoryInspectorOpen(false)}
                className="p-2 rounded-lg text-[#8A90A2] hover:text-[#E6E8EE] hover:bg-[#1A1E29] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 bg-[#12151C]/50 border-b border-[#1F2430]">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSearch(query);
                }}
                className="flex items-center gap-2"
              >
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8A90A2]" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search memories by keyword, service, or incident..."
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 pl-9 pr-3 py-2 text-sm text-[#E6E8EE] placeholder:text-[#5A6072] focus:border-[#7C5CFF] focus:ring-1 focus:ring-[#7C5CFF]"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-[#7C5CFF] hover:bg-[#6B47FF] text-white text-sm font-medium rounded-12 transition-colors flex items-center gap-1.5"
                >
                  {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Recall'}
                </button>
              </form>

              <div className="flex items-center justify-between mt-3 text-xs text-[#8A90A2]">
                <div className="flex items-center gap-2">
                  <span>Memory Backend:</span>
                  <Badge variant={backendMode === 'hindsight' ? 'success' : 'primary'}>
                    <Cpu className="w-3 h-3 mr-1" />
                    {backendMode === 'hindsight' ? 'Hindsight Cloud' : 'In-Memory Bank'}
                  </Badge>
                </div>
                <span>{results.length} memories retrieved</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ) : error ? (
                <div className="p-4 bg-[#FF4D6D]/10 border border-[#FF4D6D]/30 rounded-12 text-sm text-[#FF4D6D]">
                  {error}
                </div>
              ) : results.length === 0 ? (
                <EmptyState
                  icon={Sparkles}
                  title="No Memories Found"
                  description="Try searching for terms like 'retry timeout', 'payments-gateway', 'database failover', or 'canary'."
                />
              ) : (
                results.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 bg-[#12151C] border border-[#1F2430] hover:border-[#7C5CFF]/40 rounded-16 transition-all space-y-2.5"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2 font-mono text-[#8A90A2]">
                        <Tag className="w-3.5 h-3.5 text-[#7C5CFF]" />
                        <span>ID: {item.id}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-[#2DD4A0]/10 text-[#2DD4A0] border border-[#2DD4A0]/20 font-medium">
                        Relevance: {(item.score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <p className="text-sm text-[#E6E8EE] leading-relaxed font-sans bg-[#0B0D12]/60 p-3 rounded-12 border border-[#1F2430]/60">
                      {item.content}
                    </p>

                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {item.tags?.map((tag) => (
                        <span
                          key={tag}
                          className="text-[11px] px-2 py-0.5 rounded-md bg-[#1F2430] text-[#8A90A2] font-mono"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
