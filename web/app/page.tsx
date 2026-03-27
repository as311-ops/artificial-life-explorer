'use client';

import { useSim } from '@/components/SimulationProvider';
import { SimGrid } from '@/components/SimGrid';
import { ControlBar } from '@/components/ControlBar';

export default function SimulationPage() {
  const sim = useSim();

  return (
    <div className="flex flex-col h-full">
      {/* HUD */}
      <div className="flex justify-between items-start px-4 py-2">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            sim.state === 'disconnected' ? 'bg-[#ef476f]' :
            sim.state === 'running' ? 'bg-[#06D6A0] animate-pulse' :
            sim.state === 'warming_up' ? 'bg-[#ffbe0b] animate-pulse' :
            'bg-[#888]'
          }`} />
          <span className="text-xs text-[#888]">
            {sim.state === 'disconnected' ? 'Getrennt' :
             sim.state === 'warming_up' ? 'JIT Warmup...' :
             sim.state === 'running' ? 'Läuft' :
             sim.state === 'paused' ? 'Pausiert' :
             sim.state === 'completed' ? 'Fertig' :
             sim.state === 'stopped' ? 'Gestoppt' :
             'Verbunden'}
          </span>
        </div>
        <div className="text-right">
          <div className="text-xs text-[#888] font-mono">Epoch {sim.epoch}</div>
          <div className="text-sm font-mono text-[#8338EC]">{sim.opcodePercent.toFixed(1)}%</div>
        </div>
      </div>

      {/* Grid */}
      <div className="px-2">
        <SimGrid
          frameData={sim.lastFrame}
          gridWidth={sim.gridWidth}
          gridHeight={sim.gridHeight}
        />
      </div>

      {/* Controls */}
      <ControlBar
        state={sim.state}
        epoch={sim.epoch}
        numEpochs={sim.numEpochs}
        onPause={sim.pause}
        onResume={sim.resume}
        onStop={sim.stop}
        onStep={sim.step}
      />

      {/* Replicator event */}
      {sim.replicatorEpoch !== null && (
        <div className="mx-4 px-3 py-2 rounded-lg bg-[#ef476f]/10 border border-[#ef476f]/30">
          <span className="text-xs text-[#ef476f]">
            Replikator aufgetaucht: Epoch {sim.replicatorEpoch}
          </span>
        </div>
      )}
    </div>
  );
}
