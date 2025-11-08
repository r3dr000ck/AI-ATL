'use client';

import { useMemo } from 'react';

interface PortfolioChartProps {
  data: { date: string; value: number }[];
  width?: number;
  height?: number;
}

export default function PortfolioChart({ data, width = 800, height = 300 }: PortfolioChartProps) {
  const { path, points, minY, maxY, gridLines } = useMemo(() => {
    if (data.length === 0) return { path: '', points: [], minY: 0, maxY: 0, gridLines: [] };

    const values = data.map(d => d.value);
    const minY = Math.min(...values);
    const maxY = Math.max(...values);
    const range = maxY - minY || 1;

    // Create path points
    const pathPoints = data.map((point, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((point.value - minY) / range) * height;
      return { x, y, value: point.value, date: point.date };
    });

    const path = `M ${pathPoints.map(p => `${p.x},${p.y}`).join(' L ')}`;

    // Create grid lines
    const gridCount = 5;
    const gridLines = Array.from({ length: gridCount }, (_, i) => {
      const value = minY + (range * i) / (gridCount - 1);
      const y = height - ((value - minY) / range) * height;
      return { y, value };
    });

    return { path, points: pathPoints, minY, maxY, gridLines };
  }, [data, width, height]);

  const isPositive = data.length > 1 && data[data.length - 1].value >= data[0].value;

  return (
    <div className="relative" style={{ width, height: height + 60 }}>
      <svg width={width} height={height} className="overflow-visible">
        {/* Grid lines */}
        {gridLines.map((line, i) => (
          <g key={i}>
            <line
              x1={0}
              y1={line.y}
              x2={width}
              y2={line.y}
              stroke="rgba(255, 255, 255, 0.05)"
              strokeWidth="1"
            />
            <text
              x={-10}
              y={line.y}
              fill="rgba(255, 255, 255, 0.4)"
              fontSize="12"
              textAnchor="end"
              dominantBaseline="middle"
            >
              ${(line.value / 1000).toFixed(0)}k
            </text>
          </g>
        ))}

        {/* Gradient fill */}
        <defs>
          <linearGradient id="portfolioGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop
              offset="0%"
              style={{
                stopColor: isPositive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                stopOpacity: 0.3
              }}
            />
            <stop
              offset="100%"
              style={{
                stopColor: isPositive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                stopOpacity: 0
              }}
            />
          </linearGradient>
        </defs>

        {/* Fill area */}
        <path
          d={`${path} L ${width},${height} L 0,${height} Z`}
          fill="url(#portfolioGradient)"
        />

        {/* Line */}
        <path
          d={path}
          fill="none"
          stroke={isPositive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {points.map((point, i) => (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r="4"
            fill={isPositive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'}
            className="opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
          />
        ))}
      </svg>

      {/* X-axis labels */}
      <div className="flex justify-between mt-4 px-2">
        {data.filter((_, i) => i % Math.ceil(data.length / 6) === 0).map((point, i) => (
          <span key={i} className="text-xs text-gray-400">
            {point.date}
          </span>
        ))}
      </div>
    </div>
  );
}
