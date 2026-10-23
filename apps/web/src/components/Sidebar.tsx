"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ApaarBrandIcon,
  DashboardIcon,
  StudentsIcon,
  ValidationIcon,
  ReportsIcon,
  SettingsIcon,
} from "./icons";

export function Sidebar() {
  const pathname = usePathname();
  const [studentsOpen, setStudentsOpen] = useState(
    pathname.startsWith("/students") || pathname === "/students/new"
  );

  const isDashboard = pathname === "/dashboard" || pathname === "/";
  const isStudentsList = pathname === "/students";
  const isAddStudent = pathname === "/students/new";
  const isValidation = pathname.startsWith("/validation");
  const isReports = pathname.startsWith("/reports");
  const isSettings = pathname.startsWith("/settings");

  return (
    <aside className="w-56 shrink-0 bg-[#0B2240] text-slate-300 min-h-screen flex flex-col justify-between select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center gap-3 px-5 border-b border-white/5">
          <div className="w-8 h-8 rounded-lg bg-blue-600/30 border border-blue-400/30 flex items-center justify-center text-blue-400">
            <ApaarBrandIcon className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-white text-base tracking-wide">
            APAAR
          </span>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1.5 text-xs font-medium">
          {/* 1. Dashboard */}
          <Link
            href="/dashboard"
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg transition-all ${
              isDashboard
                ? "bg-[#1D68BD] text-white font-semibold shadow-xs"
                : "text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
          >
            <DashboardIcon className="w-4 h-4 shrink-0" />
            <span>Dashboard</span>
          </Link>

          {/* 2. Students Group */}
          <div>
            <div
              onClick={() => setStudentsOpen(!studentsOpen)}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg cursor-pointer transition-all ${
                isStudentsList && !studentsOpen
                  ? "bg-[#1D68BD] text-white font-semibold"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <div className="flex items-center gap-3">
                <StudentsIcon className="w-4 h-4 shrink-0" />
                <span>Students</span>
              </div>
              <svg
                className={`w-3.5 h-3.5 transition-transform opacity-70 ${
                  studentsOpen ? "rotate-180" : ""
                }`}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>

            {/* Submenu (Screen 2 & Screen 3) */}
            {studentsOpen && (
              <div className="ml-5 mt-1 pl-3 border-l border-white/10 space-y-1">
                <Link
                  href="/students"
                  className={`block px-3 py-1.5 rounded-md transition-all ${
                    isStudentsList
                      ? "text-white font-semibold bg-white/10"
                      : "text-slate-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  Student List
                </Link>
                <Link
                  href="/students/new"
                  className={`block px-3 py-1.5 rounded-md transition-all ${
                    isAddStudent
                      ? "bg-[#1D68BD] text-white font-semibold"
                      : "text-slate-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  Add Student
                </Link>
              </div>
            )}
          </div>

          {/* 3. Validation Results */}
          <Link
            href="/validation"
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg transition-all ${
              isValidation
                ? "bg-[#1D68BD] text-white font-semibold shadow-xs"
                : "text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
          >
            <ValidationIcon className="w-4 h-4 shrink-0" />
            <span>Validation Results</span>
          </Link>

          {/* 4. Reports */}
          <Link
            href="/reports"
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg transition-all ${
              isReports
                ? "bg-[#1D68BD] text-white font-semibold shadow-xs"
                : "text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
          >
            <ReportsIcon className="w-4 h-4 shrink-0" />
            <span>Reports</span>
          </Link>

          {/* 5. Settings */}
          <Link
            href="/settings"
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg transition-all ${
              isSettings
                ? "bg-[#1D68BD] text-white font-semibold shadow-xs"
                : "text-slate-300 hover:bg-white/5 hover:text-white"
            }`}
          >
            <SettingsIcon className="w-4 h-4 shrink-0" />
            <span>Settings</span>
          </Link>
        </nav>
      </div>

      {/* Bottom system status indicator */}
      <div className="p-4 border-t border-white/5 text-[11px] text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
          <span>Platform Synchronized</span>
        </div>
      </div>
    </aside>
  );
}
