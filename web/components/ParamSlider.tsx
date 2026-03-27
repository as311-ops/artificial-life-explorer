'use client';

interface ParamSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  format?: (v: number) => string;
  onChange: (v: number) => void;
}

export function ParamSlider({ label, value, min, max, step, format, onChange }: ParamSliderProps) {
  return (
    <div className="flex items-center gap-3 py-2">
      <span className="text-sm text-[#888] w-32 shrink-0">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="flex-1 h-1 rounded-full appearance-none bg-[#252525] accent-[#06D6A0]"
      />
      <span className="text-sm text-[#e8e8e8] font-mono w-20 text-right">
        {format ? format(value) : value}
      </span>
    </div>
  );
}
