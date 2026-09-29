'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

export type ThemeMode = 'dark' | 'light';

interface AppStateContextType {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  memoryEnabled: boolean;
  setMemoryEnabled: (enabled: boolean) => void;
  toggleMemory: () => void;
  memoryInspectorOpen: boolean;
  setMemoryInspectorOpen: (open: boolean) => void;
  openMemoryInspectorWithQuery: (query?: string) => void;
  inspectorSearchQuery: string;
  setInspectorSearchQuery: (query: string) => void;
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
}

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  const [theme, setThemeState] = useState<ThemeMode>('dark');
  const [memoryEnabled, setMemoryEnabled] = useState<boolean>(true);
  const [memoryInspectorOpen, setMemoryInspectorOpen] = useState<boolean>(false);
  const [inspectorSearchQuery, setInspectorSearchQuery] = useState<string>('retry timeout gateway');

  useEffect(() => {
    // Check saved theme or system preference
    const saved = localStorage.getItem('foresight-theme') as ThemeMode | null;
    if (saved && (saved === 'dark' || saved === 'light')) {
      setThemeState(saved);
      document.documentElement.className = saved;
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const initialTheme: ThemeMode = prefersDark ? 'dark' : 'light';
      setThemeState(initialTheme);
      document.documentElement.className = initialTheme;
    }
  }, []);

  const setTheme = (newTheme: ThemeMode) => {
    setThemeState(newTheme);
    localStorage.setItem('foresight-theme', newTheme);
    document.documentElement.className = newTheme;
  };

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  };

  const toggleMemory = () => setMemoryEnabled((prev) => !prev);

  const openMemoryInspectorWithQuery = (query?: string) => {
    if (query) {
      setInspectorSearchQuery(query);
    }
    setMemoryInspectorOpen(true);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <AppStateContext.Provider
        value={{
          theme,
          setTheme,
          toggleTheme,
          memoryEnabled,
          setMemoryEnabled,
          toggleMemory,
          memoryInspectorOpen,
          setMemoryInspectorOpen,
          openMemoryInspectorWithQuery,
          inspectorSearchQuery,
          setInspectorSearchQuery,
        }}
      >
        {children}
      </AppStateContext.Provider>
    </QueryClientProvider>
  );
}
