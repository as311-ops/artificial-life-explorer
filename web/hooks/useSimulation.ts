'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import type { SimParams, ServerMessage, MetricsPoint } from '@/lib/protocol';

export type SimState = 'disconnected' | 'connected' | 'warming_up' | 'running' | 'paused' | 'completed' | 'stopped';

export interface SimulationState {
  state: SimState;
  epoch: number;
  opcodePercent: number;
  shannonEntropy: number;
  metrics: MetricsPoint[];
  replicatorEpoch: number | null;
  gridWidth: number;
  gridHeight: number;
  numEpochs: number;
  lastFrame: Uint8Array | null;
}

export function useSimulation(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [state, setState] = useState<SimulationState>({
    state: 'disconnected',
    epoch: 0,
    opcodePercent: 0,
    shannonEntropy: 0,
    metrics: [],
    replicatorEpoch: null,
    gridWidth: 0,
    gridHeight: 0,
    numEpochs: 0,
    lastFrame: null,
  });

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      setState(s => ({ ...s, state: 'connected' }));
    };

    ws.onclose = () => {
      setState(s => ({ ...s, state: 'disconnected' }));
      // Reconnect after 3s
      setTimeout(connect, 3000);
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Binary frame: 4 bytes epoch (uint32 BE) + grid data
        const view = new DataView(event.data);
        const epoch = view.getUint32(0, false); // big-endian
        const frameData = new Uint8Array(event.data, 4);
        setState(s => ({ ...s, epoch, lastFrame: frameData }));
        return;
      }

      const msg: ServerMessage = JSON.parse(event.data);
      switch (msg.type) {
        case 'metrics':
          setState(s => ({
            ...s,
            epoch: msg.epoch,
            opcodePercent: msg.opcode_percent,
            shannonEntropy: msg.shannon_entropy,
            metrics: [...s.metrics, { epoch: msg.epoch, opcode_percent: msg.opcode_percent, shannon_entropy: msg.shannon_entropy }],
          }));
          break;
        case 'status':
          setState(s => ({ ...s, state: msg.state }));
          break;
        case 'replicator':
          setState(s => ({ ...s, replicatorEpoch: msg.epoch }));
          break;
        case 'config':
          setState(s => ({ ...s, gridWidth: msg.grid_width, gridHeight: msg.grid_height, numEpochs: msg.num_epochs, metrics: [], replicatorEpoch: null }));
          break;
        case 'error':
          console.error('Simulation error:', msg.message);
          break;
      }
    };

    wsRef.current = ws;
  }, [url]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const send = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const start = useCallback((params: SimParams) => {
    send({ type: 'start', params });
  }, [send]);

  const pause = useCallback(() => send({ type: 'pause' }), [send]);
  const resume = useCallback(() => send({ type: 'resume' }), [send]);
  const stop = useCallback(() => send({ type: 'stop' }), [send]);
  const step = useCallback((count = 1) => send({ type: 'step', count }), [send]);
  const setMutationRate = useCallback((value: number) => send({ type: 'set_mutation_rate', value }), [send]);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { ...state, start, pause, resume, stop, step, setMutationRate, connect, disconnect };
}
