"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/Sidebar";
import { TopHeader } from "@/components/TopHeader";
import { EnrolmentTrendChart } from "@/components/charts/EnrolmentTrendChart";
import { CategoryDonutChart } from "@/components/charts/CategoryDonutChart";

interface DashboardData {
  institution_name: string;
  institution_id: string;
  aicte_approval: string;
  academic_year: string;
  admin_name: string;
  admin_role: string;
  stats: {
    approved_intake: number;
    actual_enrolment: number;
    remaining_seats: number;
    total_students: number;
  };
  enrolment_trend: Array<{ year: string; actual: number; approved: number }>;
  category_distribution: Array<{ category: string; count: number; percentage: number; color: string }>;
  recent_activities: Array<{ id: number; activity: string; details: string; datetime: string; type: "success" | "info" | "alert" }>;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
        const res = await fetch(`${apiBase}/api/v1/institution/dashboard`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (err) {
        console.warn("Could not reach backend dashboard API, using local values", err);
      }
    };
    fetchDashboard();
  }, []);

  const stats = data?.stats || {
    approved_intake: 600,
    actual_enrolment: 570,
    remaining_seats: 30,
    total_students: 585,
  };

  const activities = data?.recent_activities || [
    { id: 1, activity: "Student Added", details: "Aarav Sharma (APAAR ID: 123456789012)", datetime: "25 Apr 2025, 10:45 AM", type: "success" },
    { id: 2, activity: "Student Updated", details: "Neha Kapoor (Course: B.Tech CSE)", datetime: "25 Apr 2025, 09:30 AM", type: "info" },
    { id: 3, activity: "Validation Alert", details: "Duplicate APAAR ID detected", datetime: "24 Apr 2025, 05:20 PM", type: "alert" },
  ];

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex">
      {/* Dark Navy Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopHeader
          institutionName={data?.institution_name || "XYZ College of Engineering"}
          institutionId={data?.institution_id || "INST001"}
          adminName={data?.admin_name || "Priya Verma"}
          adminRole={data?.admin_role || "Institution Admin"}
          selectedYear={data?.academic_year || "2025"}
        />

        <main className="p-6 md:p-8 space-y-6 max-w-7xl">
          {/* Page Title & Subtitle */}
          <div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">
              Dashboard
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Overview of student data for admission year {data?.academic_year || "2025"}
            </p>
          </div>

          {/* Top 4 KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Approved Intake */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Approved Intake
                </span>
                <span className="text-2xl font-bold text-slate-900 mt-1 block">
                  {stats.approved_intake}
                </span>
              </div>
              <div className="w-11 h-11 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 22h16" />
                  <path d="M4 18h16" />
                  <path d="M6 18V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12" />
                  <path d="M10 8h4" />
                  <path d="M10 12h4" />
                </svg>
              </div>
            </div>

            {/* Card 2: Actual Enrolment */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Actual Enrolment
                </span>
                <span className="text-2xl font-bold text-slate-900 mt-1 block">
                  {stats.actual_enrolment}
                </span>
              </div>
              <div className="w-11 h-11 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
                  <path d="M6 12v5c3 3 9 3 12 0v-5" />
                </svg>
              </div>
            </div>

            {/* Card 3: Remaining Seats */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Remaining Seats
                </span>
                <span className="text-2xl font-bold text-slate-900 mt-1 block">
                  {stats.remaining_seats}
                </span>
              </div>
              <div className="w-11 h-11 rounded-full bg-amber-50 text-amber-500 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              </div>
            </div>

            {/* Card 4: Total Students */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Total Students
                </span>
                <span className="text-2xl font-bold text-slate-900 mt-1 block">
                  {stats.total_students}
                </span>
              </div>
              <div className="w-11 h-11 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
              </div>
            </div>
          </div>

          {/* Middle Row: 2 Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-6">
              <EnrolmentTrendChart data={data?.enrolment_trend} />
            </div>
            <div className="lg:col-span-6">
              <CategoryDonutChart items={data?.category_distribution} />
            </div>
          </div>

          {/* Bottom Row: Recent Activities & Quick Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Recent Activities */}
            <div className="lg:col-span-8 bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
              <h3 className="text-sm font-semibold text-slate-800 mb-4">Recent Activities</h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 text-slate-400 font-semibold">
                      <th className="pb-2.5 pl-1 w-10">#</th>
                      <th className="pb-2.5 w-36">Activity</th>
                      <th className="pb-2.5">Details</th>
                      <th className="pb-2.5 text-right pr-2">Date &amp; Time</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {activities.map((act) => (
                      <tr key={act.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 pl-1 font-medium text-slate-500">{act.id}</td>
                        <td className="py-3 font-semibold">
                          <span
                            className={
                              act.type === "alert"
                                ? "text-red-500 font-bold"
                                : "text-slate-800"
                            }
                          >
                            {act.activity}
                          </span>
                        </td>
                        <td className="py-3 text-slate-600">{act.details}</td>
                        <td className="py-3 text-right pr-2 text-slate-500 font-medium">
                          {act.datetime}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right: Quick Actions */}
            <div className="lg:col-span-4 bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between">
              <h3 className="text-sm font-semibold text-slate-800 mb-4">Quick Actions</h3>

              <div className="space-y-2.5 flex-1 flex flex-col justify-center">
                <Link
                  href="/students/new"
                  className="w-full flex items-center gap-3 px-3.5 py-2.5 bg-blue-50/70 hover:bg-blue-100/70 text-blue-700 text-xs font-semibold rounded-lg border border-blue-200/60 transition-all shadow-2xs"
                >
                  <div className="w-6 h-6 rounded-md bg-blue-600 text-white flex items-center justify-center text-sm font-bold">
                    +
                  </div>
                  <span>Add New Student</span>
                </Link>

                <Link
                  href="/students"
                  className="w-full flex items-center gap-3 px-3.5 py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 transition-all shadow-2xs"
                >
                  <svg className="w-4 h-4 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="8" y1="6" x2="21" y2="6" />
                    <line x1="8" y1="12" x2="21" y2="12" />
                    <line x1="8" y1="18" x2="21" y2="18" />
                    <line x1="3" y1="6" x2="3.01" y2="6" />
                    <line x1="3" y1="12" x2="3.01" y2="12" />
                    <line x1="3" y1="18" x2="3.01" y2="18" />
                  </svg>
                  <span>View Student List</span>
                </Link>

                <Link
                  href="/validation"
                  className="w-full flex items-center gap-3 px-3.5 py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 transition-all shadow-2xs"
                >
                  <svg className="w-4 h-4 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                    <path d="m9 12 2 2 4-4" />
                  </svg>
                  <span>Check Validation Results</span>
                </Link>

                <Link
                  href="/reports"
                  className="w-full flex items-center gap-3 px-3.5 py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold rounded-lg border border-slate-200 transition-all shadow-2xs"
                >
                  <svg className="w-4 h-4 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>Download Reports</span>
                </Link>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
