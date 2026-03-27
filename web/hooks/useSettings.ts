'use client';

import { useState, useEffect } from 'react';
import type { SimParams } from '@/lib/protocol';

const STORAGE_KEY = 'alife-settings';

const DEFAULT_PARAMS: SimParams = {
  seed: 1,
  num_epochs: 7500,
  mutation_rate: 0.00024,
  grid_width: 120,
  grid_height: 68,
  replicator_threshold: 5.0,
};

const DEFAULT_BACKEND_URL = 'ws://localhost:8000/ws';

interface Settings {
  params: SimParams;
  backendUrl: string;
}

export function useSettings() {
  const [settings, setSettings] = useState<Settings>({
    params: DEFAULT_PARAMS,
    backendUrl: DEFAULT_BACKEND_URL,
  });

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setSettings(JSON.parse(stored));
      } catch {}
    }
  }, []);

  const updateParams = (partial: Partial<SimParams>) => {
    setSettings(s => {
      const next = { ...s, params: { ...s.params, ...partial } };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const setBackendUrl = (url: string) => {
    setSettings(s => {
      const next = { ...s, backendUrl: url };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  return { ...settings, updateParams, setBackendUrl };
}
