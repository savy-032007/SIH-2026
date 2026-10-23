"use client";

import React, { useState } from "react";

interface TrendPoint {
  year: string;
  actual: number;
  approved: number;
}

const DEFAULT_DATA: TrendPoint[] = [
  { year: "2021", actual: 395, approved: 600 },
  { year: "2022", actual: 450, approved: 600 },
  { year: "2023", actual: 485, approved: 600 },
  { year: "2024", actual: 520, approved: 600 },
  { year: "2025", actual: 570, approved: 600 },
];

export function EnrolmentTrendChart({ data = DEFAULT_DATA }: { data?: TrendPoint[] }) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const width = 520;
  const height = 220;
  const paddingLeft = 45;
  const paddingRight = 35;
  const paddingTop = 25;
  const paddingBottom = 35;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const maxY = 800;

  const getY = (val: number) => paddingTop + chartHeight - (val / maxY) * chartHeight;
  const getX = (idx: number) => paddingLeft + (idx / (data.length - 1)) * chartWidth;

  // Build SVG path
  const points = data.map((d, i) => `${getX(i)},${getY(d.actual)}`).join(" ");
  const approvedY = getY(600);

  return (
    <div className="w-full bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-800">Enrolment Trend</h3>
        <div className="flex items-center gap-4 text-xs font-medium text-slate-600">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600 inline-block"></span>
            <span>Actual Enrolment</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 border-t border-dashed border-sky-400 inline-block"></span>
            <span>Approved Intake</span>
          </div>
        </div>
      </div>

      <div className="relative w-full overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none">
          {/* Horizontal Grid lines */}
          {[0, 200, 400, 600, 800].map((tick) => {
            const y = getY(tick);
            return (
              <g key={tick}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={width - paddingRight}
                  y2={y}
                  stroke="#F1F5F9"
                  strokeWidth="1"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 3}
                  textAnchor="end"
                  className="fill-slate-400 text-[10px] font-sans"
                >
                  {tick}
                </text>
              </g>
            );
          })}

          {/* Approved Intake dashed line */}
          <line
            x1={paddingLeft}
            y1={approvedY}
            x2={width - paddingRight}
            y2={approvedY}
            stroke="#93C5FD"
            strokeWidth="1.5"
            strokeDasharray="4 3"
          />

          {/* Actual Enrolment Line */}
          <polyline
            fill="none"
            stroke="#2563EB"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />

          {/* Data Points */}
          {data.map((d, i) => {
            const cx = getX(i);
            const cy = getY(d.actual);
            const isHovered = hoveredIndex === i;
            const isLast = i === data.length - 1;

            return (
              <g key={d.year}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6 : 4}
                  fill="#FFFFFF"
                  stroke="#2563EB"
                  strokeWidth="2.5"
                  className="transition-all cursor-pointer"
                  onMouseEnter={() => setHoveredIndex(i)}
                  onMouseLeave={() => setHoveredIndex(null)}
                />

                {/* X-axis labels */}
                <text
                  x={cx}
                  y={height - 10}
                  textAnchor="middle"
                  className="fill-slate-500 text-[11px] font-medium font-sans"
                >
                  {d.year}
                </text>

                {/* Peak callout badge on 2025 (matching mockup) */}
                {isLast && (
                  <g transform={`translate(${cx - 16}, ${cy - 24})`}>
                    <rect
                      x="0"
                      y="0"
                      width="32"
                      height="18"
                      rx="4"
                      fill="#1D4ED8"
                    />
                    <text
                      x="16"
                      y="12"
                      textAnchor="middle"
                      fill="#FFFFFF"
                      className="text-[10px] font-bold font-sans"
                    >
                      {d.actual}
                    </text>
                    {/* Small downward triangle pointer */}
                    <polygon
                      points="12,18 20,18 16,22"
                      fill="#1D4ED8"
                    />
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
