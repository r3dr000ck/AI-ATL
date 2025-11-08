'use client';

import { useMemo } from 'react';

interface MiniChartProps {
  data: { time: string; price: number }[];
  positive?: boolean;
  width?: number;
  height?: number;
}

export default function MiniChart({ data, positive = true, width = 120, height = 40 }: MiniChartProps) {
  const { path, minY, maxY } = useMemo(() => {
    if (data.length === 0) return { path: '', minY: 0, maxY: 0 };

    const prices = data.map(d => d.price);
    const minY = Math.min(...prices);
    const maxY = Math.max(...prices);
    const range = maxY - minY || 1;

    const points = data.map((point, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((point.price - minY) / range) * height;
      return `${x},${y}`;
    });

    return {
      path: `M ${points.join(' L ')}`,
      minY,
      maxY
    };
  }, [data, width, height]);

  const strokeColor = positive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)';
  const fillColor = positive
    ? 'rgba(34, 197, 94, 0.1)'
    : 'rgba(239, 68, 68, 0.1)';

  return (
    <svg width={width} height={height} className="overflow-visible">
      {/* Fill area under the line */}
      <path
        d={`${path} L ${width},${height} L 0,${height} Z`}
        fill={fillColor}
        opacity="0.3"
      />

      {/* Line */}
      <path
        d={path}
        fill="none"
        stroke={strokeColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
