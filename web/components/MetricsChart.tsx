'use client';

import { useRef, useEffect } from 'react';
import type { MetricsPoint } from '@/lib/protocol';

interface MetricsChartProps {
  data: MetricsPoint[];
  field: 'opcode_percent' | 'shannon_entropy';
  label: string;
  color: string;
  yMin: number;
  yMax: number;
  threshold?: { value: number; color: string };
  currentValue: number;
}

export function MetricsChart({ data, field, label, color, yMin, yMax, threshold, currentValue }: MetricsChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const pad = { top: 8, right: 8, bottom: 20, left: 8 };
    const plotW = w - pad.left - pad.right;
    const plotH = h - pad.top - pad.bottom;

    // Clear
    ctx.clearRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = '#252525';
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (plotH * i) / 4;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(w - pad.right, y);
      ctx.stroke();
    }

    const maxEpoch = Math.max(...data.map(d => d.epoch), 1);
    const toX = (epoch: number) => pad.left + (epoch / maxEpoch) * plotW;
    const toY = (val: number) => pad.top + plotH - ((val - yMin) / (yMax - yMin)) * plotH;

    // Threshold line
    if (threshold) {
      ctx.strokeStyle = threshold.color;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      const ty = toY(threshold.value);
      ctx.beginPath();
      ctx.moveTo(pad.left, ty);
      ctx.lineTo(w - pad.right, ty);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Area fill
    if (data.length > 1) {
      ctx.fillStyle = color + '1A'; // 10% opacity
      ctx.beginPath();
      ctx.moveTo(toX(data[0].epoch), toY(yMin));
      data.forEach(d => ctx.lineTo(toX(d.epoch), toY(d[field])));
      ctx.lineTo(toX(data[data.length - 1].epoch), toY(yMin));
      ctx.closePath();
      ctx.fill();
    }

    // Line
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    data.forEach((d, i) => {
      const x = toX(d.epoch);
      const y = toY(d[field]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

  }, [data, field, color, yMin, yMax, threshold]);

  return (
    <div className="mb-4">
      <div className="flex justify-between items-baseline mb-1 px-1">
        <span className="text-sm text-[#888]">{label}</span>
        <span className="text-lg font-mono" style={{ color }}>{currentValue.toFixed(2)}</span>
      </div>
      <canvas
        ref={canvasRef}
        className="w-full h-[140px] rounded-lg"
      />
    </div>
  );
}
