'use client';

import { useRef, useEffect, useMemo } from 'react';
import { buildColorLUT } from '@/lib/colors';

interface SimGridProps {
  frameData: Uint8Array | null;
  gridWidth: number;
  gridHeight: number;
}

export function SimGrid({ frameData, gridWidth, gridHeight }: SimGridProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const colorLUT = useMemo(() => buildColorLUT(), []);

  useEffect(() => {
    if (!frameData || !gridWidth || !gridHeight || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas internal resolution to grid dimensions
    canvas.width = gridWidth;
    canvas.height = gridHeight;

    const imageData = ctx.createImageData(gridWidth, gridHeight);
    const pixels = imageData.data;

    for (let i = 0; i < frameData.length && i < gridWidth * gridHeight; i++) {
      const byte = frameData[i];
      const pi = i * 4;
      pixels[pi] = colorLUT[byte * 3];
      pixels[pi + 1] = colorLUT[byte * 3 + 1];
      pixels[pi + 2] = colorLUT[byte * 3 + 2];
      pixels[pi + 3] = 255;
    }

    ctx.putImageData(imageData, 0, 0);
  }, [frameData, gridWidth, gridHeight, colorLUT]);

  if (!gridWidth || !gridHeight) {
    return (
      <div className="w-full aspect-video bg-[#141414] rounded-lg flex items-center justify-center">
        <span className="text-[#888] text-sm">Warte auf Simulation...</span>
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      className="w-full rounded-lg"
      style={{
        aspectRatio: `${gridWidth} / ${gridHeight}`,
        imageRendering: 'pixelated',
      }}
    />
  );
}
