'use client';

import { createContext, useContext } from 'react';
import { useSimulation } from '@/hooks/useSimulation';
import { useSettings } from '@/hooks/useSettings';
import type { SimParams } from '@/lib/protocol';
import type { SimulationState } from '@/hooks/useSimulation';

interface SimContextType extends SimulationState {
  start: (params: SimParams) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  step: (count?: number) => void;
  setMutationRate: (value: number) => void;
}

const SimContext = createContext<SimContextType | null>(null);

export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const { backendUrl } = useSettings();
  const sim = useSimulation(backendUrl);
  return <SimContext.Provider value={sim}>{children}</SimContext.Provider>;
}

export function useSim(): SimContextType {
  const ctx = useContext(SimContext);
  if (!ctx) throw new Error('useSim must be used within SimulationProvider');
  return ctx;
}
