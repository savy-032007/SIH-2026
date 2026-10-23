"use client";

import React, { useState } from "react";

interface DonutLegendItem {
  label: string;
  percentage: number;
  color: string;
}

const DEFAULT_ITEMS: DonutLegendItem[] = [
  { label: "Duplicate APAAR ID", percentage: 19.0, color: "#8B5CF6" },
  { label: "Invalid / Missing", percentage: 28.6, color: "#F97316" },
  { label: "Excess Enrolment", percentage: 11.9, color: "#EAB308" },
  { label: "Inconsistent Data", percentage: 23.8, color: "#06B6D4" },
  { label: "Cross-Institution Duplicate", percentage: 9.5, color: "#10B981" },
  { label: "Others", percentage: 7.1, color: "#1E3A8A" },
];

export function ValidationDonutChart({
  totalIssues = 42,
  items = DEFAULT_ITEMS,
}: {
  totalIssues?: number;
  items?: DonutLegendItem[];
}) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const size = 180;
  const radius = 68;
  const strokeWidth = 24;
  const center = size / 2;

  let accumulatedAngle = 0;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="w-full bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* Donut Chart with Center Text */}
        <div className="md:col-span-5 flex justify-center">
          <div className="relative w-44 h-44 flex items-center justify-center">
            <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
              {items.map((item, idx) => {
                const strokeDasharray = `${(item.percentage / 100) * circumference} ${circumference}`;
                const strokeDashoffset = -accumulatedAngle;
                accumulatedAngle += (item.percentage / 100) * circumference;

                const isHovered = hoveredIdx === idx;

                return (
                  <circle
                    key={item.label}
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="transparent"
                    stroke={item.color}
                    strokeWidth={isHovered ? strokeWidth + 4 : strokeWidth}
                    strokeDasharray={strokeDasharray}
                    strokeDashoffset={strokeDashoffset}
                    className="transition-all duration-200 cursor-pointer"
                    onMouseEnter={() => setHoveredIdx(idx)}
                    onMouseLeave={() => setHoveredIdx(null)}
                  />
                );
              })}
            </svg>

            {/* Center Text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
              <span className="text-2xl font-bold text-slate-900 leading-tight">
                {totalIssues}
              </span>
              <span className="text-[10px] text-slate-500 font-medium">
                Total Issues
              </span>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="md:col-span-7 flex flex-col justify-center space-y-1.5 pl-2">
          {items.map((item, idx) => (
            <div
              key={item.label}
              className={`flex items-center justify-between text-xs py-0.5 px-2 rounded-md transition-colors cursor-pointer ${
                hoveredIdx === idx ? "bg-slate-50 font-semibold" : ""
              }`}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-slate-700">{item.label}</span>
              </div>
              <span className="text-slate-500 font-medium ml-2">
                {item.percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
