"use client";

import React, { useState } from "react";

interface CategoryItem {
  category: string;
  count: number;
  percentage: number;
  color: string;
}

const DEFAULT_CATEGORIES: CategoryItem[] = [
  { category: "General", count: 320, percentage: 54.7, color: "#3B82F6" },
  { category: "OBC", count: 120, percentage: 20.5, color: "#F59E0B" },
  { category: "SC", count: 60, percentage: 10.3, color: "#10B981" },
  { category: "ST", count: 35, percentage: 6.0, color: "#EF4444" },
  { category: "NRI", count: 25, percentage: 4.3, color: "#8B5CF6" },
  { category: "OCI", count: 15, percentage: 2.6, color: "#EC4899" },
  { category: "Foreign National", count: 10, percentage: 1.7, color: "#06B6D4" },
];

export function CategoryDonutChart({ items = DEFAULT_CATEGORIES }: { items?: CategoryItem[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const size = 180;
  const radius = 70;
  const strokeWidth = 22;
  const center = size / 2;

  const total = items.reduce((acc, it) => acc + it.count, 0);

  // Calculate SVG arc strokes
  let accumulatedAngle = 0;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="w-full bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
      <h3 className="text-sm font-semibold text-slate-800 mb-4">Student Category Distribution</h3>

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
                    key={item.category}
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
              <span className="text-xl font-bold text-slate-900 leading-tight">
                {hoveredIdx !== null && items[hoveredIdx] ? items[hoveredIdx].count : total}
              </span>
              <span className="text-[10px] text-slate-500 font-medium">
                {hoveredIdx !== null && items[hoveredIdx] ? items[hoveredIdx].category : "Total Students"}
              </span>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="md:col-span-7 flex flex-col justify-center space-y-1.5 pl-2">
          {items.map((item, idx) => (
            <div
              key={item.category}
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
                <span className="text-slate-700">{item.category}</span>
              </div>
              <span className="text-slate-500 font-medium ml-2">
                {item.count} ({item.percentage}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
