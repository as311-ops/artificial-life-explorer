'use client';

import { useSim } from '@/components/SimulationProvider';
import { MetricsChart } from '@/components/MetricsChart';

export default function ChartsPage() {
  const sim = useSim();

  return (
    <div className="px-4 py-4">
      <MetricsChart
        data={sim.metrics}
        field="opcode_percent"
        label="Opcode Density"
        color="#8338EC"
        yMin={0}
        yMax={100}
        threshold={{ value: 5, color: '#EF476F' }}
        currentValue={sim.opcodePercent}
      />

      <MetricsChart
        data={sim.metrics}
        field="shannon_entropy"
        label="Shannon Entropy"
        color="#FFBE0B"
        yMin={0}
        yMax={8}
        currentValue={sim.shannonEntropy}
      />

      {sim.replicatorEpoch !== null && (
        <div className="px-3 py-2 rounded-lg bg-[#ef476f]/10 border border-[#ef476f]/30">
          <span className="text-sm text-[#ef476f]">
            Replikator aufgetaucht: Epoch {sim.replicatorEpoch}
          </span>
        </div>
      )}
    </div>
  );
}
