"use client";

import React, { useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { TopHeader } from "@/components/TopHeader";
import { ValidationDonutChart } from "@/components/charts/ValidationDonutChart";

interface FlaggedRecord {
  id: string;
  row_num: number;
  student_name: string;
  apaar_id: string;
  issue: string;
  status: "Needs Correction" | "Flagged";
  details?: string;
}

export default function ValidationResultsPage() {
  const [activeTab, setActiveTab] = useState("issues_breakdown");
  const [dateRange, setDateRange] = useState("24 Apr 2025 - 25 Apr 2025");
  const [selectedRecord, setSelectedRecord] = useState<FlaggedRecord | null>(null);

  const stats = {
    total_records: 585,
    valid_count: 540,
    valid_percentage: 92.3,
    needs_correction_count: 28,
    needs_correction_percentage: 4.8,
    flagged_count: 17,
    flagged_percentage: 2.9,
  };

  const issuesList = [
    { type: "Duplicate APAAR ID", count: 8, percentage: 1.4, color: "#8B5CF6" },
    { type: "Invalid / Missing APAAR ID", count: 12, percentage: 2.1, color: "#F97316" },
    { type: "Excess Enrolment", count: 5, percentage: 0.9, color: "#EAB308" },
    { type: "Inconsistent Data", count: 10, percentage: 1.7, color: "#06B6D4" },
    { type: "Possible Cross-Institution Duplicate", count: 4, percentage: 0.7, color: "#10B981" },
    { type: "Others", count: 3, percentage: 0.5, color: "#1E3A8A" },
  ];

  const flaggedRecords: FlaggedRecord[] = [
    { id: "flg-1", row_num: 1, student_name: "Rohan Mehta", apaar_id: "111222333444", issue: "Missing APAAR ID", status: "Needs Correction", details: "APAAR ID field was left blank for non-exempt category student." },
    { id: "flg-2", row_num: 2, student_name: "Karan Singh", apaar_id: "999888777666", issue: "Duplicate APAAR ID", status: "Flagged", details: "APAAR ID is already flagged as active at another institution for academic year 2025." },
    { id: "flg-3", row_num: 3, student_name: "Priya Desai", apaar_id: "123456789012", issue: "Excess Enrolment", status: "Flagged", details: "Approved intake limit of 60 for course B.Tech CSE has been exceeded." },
    { id: "flg-4", row_num: 4, student_name: "Amit Kumar", apaar_id: "777888999000", issue: "Inconsistent Course Data", status: "Needs Correction", details: "Supernumerary NRI quota claimed without valid NRI sponsorship affidavit document." },
  ];

  const handleExport = () => {
    alert("Exporting validation report to Excel (XLSX)...");
  };

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex">
      {/* Dark Navy Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopHeader />

        <main className="p-6 md:p-8 space-y-6 max-w-7xl">
          {/* Header Row: Title & Date Selector + Export */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-slate-800 tracking-tight">
                Validation Results
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Summary of data validation checks
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Date Range Selector */}
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="text-xs text-slate-700 bg-white border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer"
              >
                <option value="24 Apr 2025 - 25 Apr 2025">24 Apr 2025 - 25 Apr 2025</option>
                <option value="Last 7 Days">Last 7 Days</option>
                <option value="Full Academic Year 2025">Full Academic Year 2025</option>
              </select>

              {/* Export Button */}
              <button
                onClick={handleExport}
                className="bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2 shadow-2xs transition-colors cursor-pointer"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                <span>Export</span>
              </button>
            </div>
          </div>

          {/* Top 4 Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Records */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Total Records
                </span>
                <span className="text-2xl font-bold text-slate-900 mt-1 block">
                  {stats.total_records}
                </span>
              </div>
              <div className="w-11 h-11 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>
            </div>

            {/* Valid */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Valid
                </span>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className="text-2xl font-bold text-slate-900">
                    {stats.valid_count}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">
                    ({stats.valid_percentage}%)
                  </span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                  <path d="m9 12 2 2 4-4" />
                </svg>
              </div>
            </div>

            {/* Needs Correction */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Needs Correction
                </span>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className="text-2xl font-bold text-slate-900">
                    {stats.needs_correction_count}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">
                    ({stats.needs_correction_percentage}%)
                  </span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-full bg-amber-50 text-amber-500 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
            </div>

            {/* Flagged */}
            <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                  Flagged
                </span>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className="text-2xl font-bold text-slate-900">
                    {stats.flagged_count}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">
                    ({stats.flagged_percentage}%)
                  </span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                  <line x1="4" y1="22" x2="4" y2="15" />
                </svg>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-6 border-b border-slate-200 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("issues_breakdown")}
              className={`pb-3 transition-colors relative ${
                activeTab === "issues_breakdown"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Issues Breakdown
            </button>
            <button
              onClick={() => setActiveTab("invalid_apaar")}
              className={`pb-3 transition-colors relative ${
                activeTab === "invalid_apaar"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Invalid / Missing APAAR ID
            </button>
            <button
              onClick={() => setActiveTab("duplicate_records")}
              className={`pb-3 transition-colors relative ${
                activeTab === "duplicate_records"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Duplicate Records
            </button>
            <button
              onClick={() => setActiveTab("excess_enrolment")}
              className={`pb-3 transition-colors relative ${
                activeTab === "excess_enrolment"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Excess Enrolment
            </button>
            <button
              onClick={() => setActiveTab("inconsistent_data")}
              className={`pb-3 transition-colors relative ${
                activeTab === "inconsistent_data"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Inconsistent Data
            </button>
          </div>

          {/* Middle Row: Left Table & Right Donut Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Left Column: Issues Breakdown Table */}
            <div className="lg:col-span-7 bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 font-semibold">
                    <th className="pb-2.5">Issue Type</th>
                    <th className="pb-2.5 text-center w-24">Count</th>
                    <th className="pb-2.5 text-right w-28">Percentage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {issuesList.map((item) => (
                    <tr key={item.type} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-2.5 flex items-center gap-2.5">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="font-semibold text-slate-700">{item.type}</span>
                      </td>
                      <td className="py-2.5 text-center font-bold text-slate-800">
                        {item.count}
                      </td>
                      <td className="py-2.5 text-right font-medium text-slate-500">
                        {item.percentage}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Right Column: Donut Chart with Total Issues */}
            <div className="lg:col-span-5">
              <ValidationDonutChart totalIssues={42} />
            </div>
          </div>

          {/* Bottom Row: Flagged Records Table */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-2xs overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-100">
              <h3 className="text-sm font-semibold text-slate-800">Flagged Records</h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold">
                    <th className="py-3 px-4 w-12 text-center">#</th>
                    <th className="py-3 px-4">Student Name</th>
                    <th className="py-3 px-4">APAAR ID</th>
                    <th className="py-3 px-4">Issue</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center w-24">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {flaggedRecords.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 text-center font-medium text-slate-500">
                        {rec.row_num}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-800">
                        {rec.student_name}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-600">
                        {rec.apaar_id}
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {rec.issue}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {rec.status === "Needs Correction" ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                            Needs Correction
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            Flagged
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => setSelectedRecord(rec)}
                          className="text-blue-600 hover:text-blue-800 font-semibold text-xs cursor-pointer"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>

      {/* Flagged Issue Detail Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">
                Validation Issue Details
              </h3>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Student Name:</span>
                <span className="font-bold text-slate-800">{selectedRecord.student_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">APAAR ID:</span>
                <span className="font-mono text-blue-600 font-semibold">{selectedRecord.apaar_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Detected Issue:</span>
                <span className="font-semibold text-red-600">{selectedRecord.issue}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-medium">Severity Status:</span>
                <span
                  className={`px-2 py-0.5 rounded-full font-bold ${
                    selectedRecord.status === "Needs Correction"
                      ? "bg-amber-100 text-amber-800"
                      : "bg-rose-100 text-rose-800"
                  }`}
                >
                  {selectedRecord.status}
                </span>
              </div>
              <div className="pt-2">
                <span className="text-slate-500 font-medium block mb-1">Issue Explanation:</span>
                <p className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-slate-700 leading-relaxed">
                  {selectedRecord.details}
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg cursor-pointer"
              >
                Dismiss
              </button>
              <button
                onClick={() => {
                  alert(`Correction workflow initiated for ${selectedRecord.student_name}`);
                  setSelectedRecord(null);
                }}
                className="px-4 py-2 bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold rounded-lg cursor-pointer"
              >
                Resolve Issue
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
