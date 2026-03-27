'use client';

import { useSim } from '@/components/SimulationProvider';
import { ParamSlider } from '@/components/ParamSlider';
import { useSettings } from '@/hooks/useSettings';

const GRID_PRESETS = [
  { label: '80x45', width: 80, height: 45 },
  { label: '120x68', width: 120, height: 68 },
  { label: '240x135', width: 240, height: 135 },
] as const;

export default function SettingsPage() {
  const { params, backendUrl, updateParams, setBackendUrl } = useSettings();
  const sim = useSim();

  const canStart = sim.state === 'connected' || sim.state === 'completed' || sim.state === 'stopped';

  return (
    <div className="px-4 py-4 space-y-4">
      {/* Parameters */}
      <div className="bg-[#1a1a1a] rounded-xl p-4">
        <h2 className="text-xs text-[#888] uppercase tracking-wider mb-3">Parameter</h2>

        <div className="flex items-center gap-3 py-2">
          <span className="text-sm text-[#888] w-32 shrink-0">Seed</span>
          <input
            type="number"
            value={params.seed}
            onChange={e => updateParams({ seed: parseInt(e.target.value) || 0 })}
            className="flex-1 bg-[#252525] rounded-lg px-3 py-2 text-sm font-mono text-[#e8e8e8] outline-none focus:ring-1 focus:ring-[#06D6A0]"
          />
          <button
            onClick={() => updateParams({ seed: Math.floor(Math.random() * 100000) })}
            className="px-3 py-2 rounded-lg bg-[#252525] text-sm active:bg-[#333]"
          >
            Zufall
          </button>
        </div>

        <ParamSlider
          label="Epochs"
          value={params.num_epochs}
          min={500}
          max={20000}
          step={500}
          onChange={v => updateParams({ num_epochs: v })}
        />

        <ParamSlider
          label="Mutation Rate"
          value={params.mutation_rate}
          min={0}
          max={0.01}
          step={0.00001}
          format={v => `${(v * 100).toFixed(3)}%`}
          onChange={v => updateParams({ mutation_rate: v })}
        />

        <ParamSlider
          label="Repl. Threshold"
          value={params.replicator_threshold}
          min={1}
          max={20}
          step={0.5}
          format={v => `${v.toFixed(1)}%`}
          onChange={v => updateParams({ replicator_threshold: v })}
        />
      </div>

      {/* Grid Size */}
      <div className="bg-[#1a1a1a] rounded-xl p-4">
        <h2 className="text-xs text-[#888] uppercase tracking-wider mb-3">Grid Size</h2>

        <div className="flex gap-2 mb-3">
          {GRID_PRESETS.map(preset => (
            <button
              key={preset.label}
              onClick={() => updateParams({ grid_width: preset.width, grid_height: preset.height })}
              className={`flex-1 py-2 rounded-lg text-xs font-mono ${
                params.grid_width === preset.width && params.grid_height === preset.height
                  ? 'bg-[#06D6A0] text-[#0d0d0d] font-medium'
                  : 'bg-[#252525] text-[#888]'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        <ParamSlider
          label="Width"
          value={params.grid_width}
          min={40}
          max={240}
          step={1}
          onChange={v => updateParams({ grid_width: v })}
        />
        <ParamSlider
          label="Height"
          value={params.grid_height}
          min={23}
          max={135}
          step={1}
          onChange={v => updateParams({ grid_height: v })}
        />

        <div className="text-xs text-[#888] mt-1">
          Programme: {(params.grid_width * params.grid_height).toLocaleString('de-DE')}
        </div>
      </div>

      {/* Connection */}
      <div className="bg-[#1a1a1a] rounded-xl p-4">
        <h2 className="text-xs text-[#888] uppercase tracking-wider mb-3">Verbindung</h2>
        <input
          type="text"
          value={backendUrl}
          onChange={e => setBackendUrl(e.target.value)}
          placeholder="ws://localhost:8000/ws"
          className="w-full bg-[#252525] rounded-lg px-3 py-2 text-sm font-mono text-[#e8e8e8] outline-none focus:ring-1 focus:ring-[#06D6A0] mb-2"
        />
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            sim.state === 'disconnected' ? 'bg-[#ef476f]' : 'bg-[#06D6A0]'
          }`} />
          <span className="text-xs text-[#888]">
            {sim.state === 'disconnected' ? 'Getrennt' : 'Verbunden'}
          </span>
        </div>
      </div>

      {/* Start Button */}
      <button
        onClick={() => sim.start(params)}
        disabled={!canStart}
        className={`w-full py-3 rounded-xl text-sm font-medium ${
          canStart
            ? 'bg-[#06D6A0] text-[#0d0d0d] active:bg-[#05b888]'
            : 'bg-[#252525] text-[#666] cursor-not-allowed'
        }`}
      >
        Neue Simulation starten
      </button>
    </div>
  );
}
