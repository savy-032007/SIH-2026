"use client";

import React from "react";
import { Sidebar } from "@/components/Sidebar";
import { TopHeader } from "@/components/TopHeader";

export default function ReportsPage() {
  const reports = [
    { title: "Intake vs Enrolment Report", desc: "Detailed breakdown of approved intake against actual enrolments for academic year 2025.", format: "PDF / Excel", icon: "📊" },
    { title: "Excess Enrolment & Violations Report", desc: "Audit list of courses exceeding within-intake or supernumerary quota caps.", format: "PDF / Excel", icon: "⚠️" },
    { title: "Category Distribution Trends", desc: "Statistical distribution of General, OBC, SC, ST, NRI, OCI and Foreign National enrolments.", format: "PDF / Excel", icon: "📈" },
    { title: "Institution Accreditation Data Pack", desc: "Consolidated verifiable student data pack formatted for NBA/NAAC regulatory reviews.", format: "ZIP / PDF", icon: "📑" },
  ];

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopHeader />
        <main className="p-6 md:p-8 space-y-6 max-w-7xl">
          <div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">Reports &amp; Regulatory Exports</h2>
            <p className="text-xs text-slate-500 mt-0.5">Generate and download official AICTE-format compliance reports</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reports.map((r) => (
              <div key={r.title} className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{r.icon}</span>
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">{r.title}</h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{r.desc}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{r.format}</span>
                  <button
                    onClick={() => alert(`Generating ${r.title}... Download starting.`)}
                    className="px-3.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-lg border border-blue-200/60 transition-colors cursor-pointer"
                  >
                    Download Report
                  </button>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
