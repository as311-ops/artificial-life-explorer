'use client';

import type { SimState } from '@/hooks/useSimulation';

interface ControlBarProps {
  state: SimState;
  epoch: number;
  numEpochs: number;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onStep: (count: number) => void;
}

export function ControlBar({ state, epoch, numEpochs, onPause, onResume, onStop, onStep }: ControlBarProps) {
  const isRunning = state === 'running';
  const isPaused = state === 'paused';
  const canControl = isRunning || isPaused;

  return (
    <div className="flex items-center gap-3 px-4 py-3">
      {canControl && (
        <>
          {isRunning ? (
            <button onClick={onPause} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1a1a1a] text-[#e8e8e8] text-sm active:bg-[#252525]">
              <span className="text-base">&#x23F8;</span> Pause
            </button>
          ) : (
            <button onClick={onResume} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#06D6A0] text-[#0d0d0d] text-sm font-medium active:bg-[#05b888]">
              <span className="text-base">&#x25B6;</span> Weiter
            </button>
          )}
          <button onClick={onStop} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1a1a1a] text-[#ef476f] text-sm active:bg-[#252525]">
            <span className="text-base">&#x23F9;</span> Stop
          </button>
          {isPaused && (
            <button onClick={() => onStep(10)} className="px-3 py-2 rounded-lg bg-[#1a1a1a] text-[#3a86ff] text-sm active:bg-[#252525]">
              +10
            </button>
          )}
        </>
      )}
      <div className="ml-auto text-right">
        <span className="text-xs text-[#888] font-mono">{epoch} / {numEpochs}</span>
      </div>
    </div>
  );
}
