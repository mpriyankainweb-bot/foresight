'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Navbar } from '../../components/Navbar';
import { MemoryCitationItem } from '../../lib/api';
import {
  Send,
  Bot,
  User,
  Sparkles,
  Database,
  Tag,
  Loader2,
  Brain,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    if (process.env.NEXT_PUBLIC_API_BASE_URL) {
      return process.env.NEXT_PUBLIC_API_BASE_URL;
    }
    const host = window.location.hostname;
    const protocol = window.location.protocol;
    if (host.includes('app.github.dev')) {
      const backendHost = host.replace(/-3000\./, '-8000.');
      return `${protocol}//${backendHost}`;
    }
    return `${protocol}//${host}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'foresight-secret-key-123';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: MemoryCitationItem[];
  isStreaming?: boolean;
}

function FormattedMarkdown({ content }: { content: string }) {
  if (!content) return null;

  const lines = content.split('\n');

  return (
    <div className="space-y-2 leading-relaxed">
      {lines.map((line, lIdx) => {
        if (!line.trim()) return <div key={lIdx} className="h-1" />;

        // Parse bold **text**
        const parts = line.split(/(\*\*.*?\*\*)/g);
        const formattedLine = parts.map((part, pIdx) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return (
              <strong key={pIdx} className="font-semibold text-white">
                {part.slice(2, -2)}
              </strong>
            );
          }
          return part;
        });

        if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
          return (
            <div key={lIdx} className="flex items-start gap-2 pl-2">
              <span className="text-[#7C5CFF] font-bold select-none">•</span>
              <div>{formattedLine}</div>
            </div>
          );
        }

        return <p key={lIdx}>{formattedLine}</p>;
      })}
    </div>
  );
}

export default function AskPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I am Foresight. Ask me anything about PayNest’s deploy history, past outages, fix attempts, and Hindsight incident memory.',
      citations: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedChips = [
    'What broke last time we changed retry timeouts?',
    'Which fixes only held temporarily?',
    'What caused the payment gateway double debit outages?',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (questionText?: string) => {
    const question = questionText || input;
    if (!question.trim() || isGenerating) return;

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    const userMsg: Message = {
      id: userMsgId,
      role: 'user',
      content: question,
    };

    const initialAssistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      citations: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setInput('');
    setIsGenerating(true);

    try {
      const apiKey = typeof window !== 'undefined' ? (localStorage.getItem('foresight_api_key') || API_KEY) : API_KEY;
      const response = await fetch(`${API_BASE_URL}/api/v1/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No readable stream available');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'citations') {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, citations: data.citations } : msg
                )
              );
            } else if (data.type === 'delta') {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, content: msg.content + data.text } : msg
                )
              );
            } else if (data.type === 'done') {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg
                )
              );
            }
          } catch (e) {
            console.error('Error parsing line:', line, e);
          }
        }
      }
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content: `An error occurred while recalling memory: ${err.message || 'Network error'}`,
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsGenerating(false);
      setMessages((prev) =>
        prev.map((msg) => (msg.id === assistantMsgId ? { ...msg, isStreaming: false } : msg))
      );
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0D12] text-[#E6E8EE] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col">
        {/* Header */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1F2430] pb-6">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-12 bg-[#7C5CFF]/10 border border-[#7C5CFF]/30 text-[#9E85FF]">
                <Brain className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  Ask Foresight
                </h1>
                <p className="text-sm text-[#8A90A2]">
                  Interactive AI reasoning powered by Hindsight incident memory recall
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs px-3 py-1.5 rounded-full bg-[#12151C] border border-[#1F2430] text-[#8A90A2] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#2DD4A0]" />
              Zero Hardcoded Rules
            </span>
            <button
              onClick={() =>
                setMessages([
                  {
                    id: 'welcome',
                    role: 'assistant',
                    content:
                      'Hello! I am Foresight. Ask me anything about PayNest’s deploy history, past outages, fix attempts, and Hindsight incident memory.',
                    citations: [],
                  },
                ])
              }
              className="p-2 rounded-12 bg-[#12151C] hover:bg-[#1A1E29] border border-[#1F2430] text-[#8A90A2] hover:text-white transition-all text-xs flex items-center gap-1.5"
              title="Clear chat"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset Chat
            </button>
          </div>
        </div>

        {/* Prompt Chips */}
        <div className="mb-6">
          <p className="text-xs font-semibold text-[#8A90A2] uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#7C5CFF]" />
            Suggested Prompts
          </p>
          <div className="flex flex-wrap gap-2">
            {suggestedChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(chip)}
                disabled={isGenerating}
                className="text-xs px-3.5 py-2 rounded-12 bg-[#12151C] hover:bg-[#1A1E29] border border-[#1F2430] hover:border-[#7C5CFF]/50 text-[#E6E8EE] transition-all text-left flex items-center gap-2 group disabled:opacity-50"
              >
                <span>{chip}</span>
                <Sparkles className="w-3 h-3 text-[#7C5CFF] opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ))}
          </div>
        </div>

        {/* Chat Messages Container */}
        <div className="flex-1 min-h-[400px] max-h-[600px] overflow-y-auto bg-[#12151C]/60 border border-[#1F2430] rounded-16 p-4 sm:p-6 space-y-6 flex flex-col mb-4">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex gap-3 sm:gap-4 ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-12 bg-[#7C5CFF]/20 border border-[#7C5CFF]/40 flex items-center justify-center text-[#9E85FF] shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-16 p-4 space-y-3 ${
                    msg.role === 'user'
                      ? 'bg-[#7C5CFF] text-white rounded-tr-none font-medium'
                      : 'bg-[#12151C] border border-[#1F2430] text-[#E6E8EE] rounded-tl-none shadow-md'
                  }`}
                >
                  {/* Content */}
                  <div className="text-sm">
                    <FormattedMarkdown content={msg.content} />
                    {msg.isStreaming && (
                      <span className="inline-block w-2 h-4 ml-1 bg-[#7C5CFF] animate-pulse" />
                    )}
                  </div>

                  {/* Memory Citations Section */}
                  {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-[#1F2430] space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-[#7C5CFF]">
                        <Database className="w-3.5 h-3.5" />
                        <span>Hindsight Memory Citations ({msg.citations.length})</span>
                      </div>

                      <div className="grid grid-cols-1 gap-2">
                        {msg.citations.map((cit, cIdx) => (
                          <div
                            key={cIdx}
                            className="p-2.5 rounded-10 bg-[#0B0D12]/60 border border-[#1F2430] text-xs space-y-1 hover:border-[#7C5CFF]/30 transition-colors"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-mono text-[#9E85FF] font-semibold">
                                {cit.id}
                              </span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#2DD4A0]/10 text-[#2DD4A0] border border-[#2DD4A0]/20 font-mono">
                                relevance {(cit.score * 100).toFixed(0)}%
                              </span>
                            </div>

                            <p className="text-[#8A90A2] line-clamp-2 leading-tight">
                              {cit.text}
                            </p>

                            {cit.tags && cit.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 pt-1">
                                {cit.tags.map((t, tIdx) => (
                                  <span
                                    key={tIdx}
                                    className="text-[9px] px-1.5 py-0.2 rounded bg-[#1F2430] text-[#8A90A2] flex items-center gap-0.5"
                                  >
                                    <Tag className="w-2.5 h-2.5 text-[#7C5CFF]" />
                                    {t}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-12 bg-[#1F2430] border border-[#2A3040] flex items-center justify-center text-[#8A90A2] shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Foresight about past outages, retry timeouts, or temporary fixes..."
            disabled={isGenerating}
            className="flex-1 bg-[#12151C] border border-[#1F2430] focus:border-[#7C5CFF] rounded-12 px-4 py-3 text-sm text-[#E6E8EE] placeholder-[#8A90A2] outline-none transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isGenerating}
            className="px-5 py-3 rounded-12 bg-[#7C5CFF] hover:bg-[#6843EC] text-white font-medium text-sm transition-all flex items-center gap-2 disabled:opacity-50 shadow-glow shrink-0"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Ask</span>
              </>
            )}
          </button>
        </form>
      </main>
    </div>
  );
}
