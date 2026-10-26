"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BellIcon } from "./icons";
import { clearAccessToken } from "../lib/api";

interface TopHeaderProps {
  institutionName?: string;
  institutionId?: string;
  adminName?: string;
  adminRole?: string;
  selectedYear?: string;
  onYearChange?: (year: string) => void;
}

export function TopHeader({
  institutionName = "XYZ College of Engineering",
  institutionId = "INST001",
  adminName = "Priya Verma",
  adminRole = "Institution Admin",
  selectedYear = "2025",
  onYearChange,
}: TopHeaderProps) {
  const [year, setYear] = useState(selectedYear);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const [displayName, setDisplayName] = useState(adminName);
  const [displayRole, setDisplayRole] = useState(adminRole);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("apaar_user");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.name) setDisplayName(parsed.name);
        if (parsed.role) setDisplayRole(parsed.role);
      }
    } catch {}
  }, []);


  useEffect(() => {
    if (!showProfileMenu) return;

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!profileMenuRef.current?.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setShowProfileMenu(false);
    };

    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [showProfileMenu]);

  const handleLogout = () => {
    clearAccessToken();
    setShowProfileMenu(false);
    router.replace("/");
  };

  const handleYearSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setYear(val);
    if (onYearChange) onYearChange(val);
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      {/* Left Breadcrumb & Institution Branding */}
      <div>
        <h1 className="text-sm font-bold text-slate-800 leading-tight">
          {institutionName}
        </h1>
        <p className="text-[11px] text-slate-500 font-medium">
          Institution ID: {institutionId} | AICTE Approved
        </p>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Academic Year Selector */}
        <div className="relative">
          <select
            value={year}
            onChange={handleYearSelect}
            className="text-xs font-semibold text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 pr-7 appearance-none focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer shadow-2xs"
          >
            <option value="2025">2025</option>
            <option value="2026">2026</option>
            <option value="2024">2024</option>
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
            <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        </div>

        {/* Notifications Icon with Indicator Dot */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-full transition-colors relative"
            title="Notifications"
          >
            <BellIcon className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white"></span>
          </button>

          {/* Quick Notifications Popover */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-lg border border-slate-200 p-3 z-50 text-xs">
              <div className="font-semibold text-slate-800 pb-2 border-b border-slate-100">
                Recent Alerts
              </div>
              <div className="py-2 space-y-2">
                <div className="p-2 bg-red-50 rounded-lg text-red-800">
                  <div className="font-semibold">Validation Alert</div>
                  <div className="text-[11px] text-red-600">Duplicate APAAR ID detected in batch upload.</div>
                </div>
                <div className="p-2 bg-blue-50 rounded-lg text-blue-800">
                  <div className="font-semibold">Verification Update</div>
                  <div className="text-[11px] text-blue-600">540 of 585 records successfully validated.</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Card */}
        <div className="relative pl-2 border-l border-slate-200" ref={profileMenuRef}>
          <button
            type="button"
            onClick={() => setShowProfileMenu((open) => !open)}
            aria-haspopup="menu"
            aria-expanded={showProfileMenu}
            aria-label={`Open profile menu for ${displayName}`}
            className="flex items-center gap-2.5 rounded-lg text-left group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            <span className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 to-rose-400 p-0.5 shadow-2xs">
              <span className="w-full h-full rounded-full bg-white flex items-center justify-center font-bold text-xs text-rose-600 overflow-hidden">
                {displayName.split(/\s+/).map((part) => part[0]).slice(0, 2).join("").toUpperCase()}
              </span>
            </span>
            <span>
              <span className="block text-xs font-bold text-slate-800 group-hover:text-blue-600 transition-colors">
                {displayName}
              </span>
              <span className="block text-[10px] text-slate-500 leading-none">
                {displayRole}
              </span>
            </span>
          </button>

          {showProfileMenu && (
            <div
              role="menu"
              aria-label="Profile menu"
              className="absolute right-0 mt-3 w-56 rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl ring-1 ring-black/5 z-50"
            >
              <div className="px-3 py-2 border-b border-slate-100">
                <p className="text-xs font-semibold text-slate-800">{displayName}</p>
                <p className="text-[11px] text-slate-500">{displayRole}</p>
              </div>
              <Link
                href="/settings"
                role="menuitem"
                onClick={() => setShowProfileMenu(false)}
                className="mt-1 block rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                Account settings
              </Link>
              <button
                type="button"
                role="menuitem"
                onClick={handleLogout}
                className="mt-0.5 w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-rose-600 hover:bg-rose-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
              >
                Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
