'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

interface AppStateContextType {
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

  const [memoryEnabled, setMemoryEnabled] = useState<boolean>(true);
  const [memoryInspectorOpen, setMemoryInspectorOpen] = useState<boolean>(false);
  const [inspectorSearchQuery, setInspectorSearchQuery] = useState<string>('retry timeout gateway');

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
