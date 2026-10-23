"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/Sidebar";
import { TopHeader } from "@/components/TopHeader";
import {
  SearchIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
} from "@/components/icons";

interface StudentRecord {
  id: string;
  row_num: number;
  name: string;
  apaar_id: string;
  course: string;
  year: string;
  category: string;
  status: "Valid" | "Needs Correction" | "Flagged";
  student_id_college?: string;
  gender?: string;
  dob?: string;
}

const DEFAULT_RECORDS: StudentRecord[] = [
  { id: "std-001", row_num: 1, name: "Aarav Sharma", apaar_id: "123456789012", course: "B.Tech CSE", year: "2025", category: "General", status: "Valid", student_id_college: "MT001" },
  { id: "std-002", row_num: 2, name: "Neha Kapoor", apaar_id: "987654321098", course: "B.Tech ECE", year: "2025", category: "OBC", status: "Valid", student_id_college: "MT002" },
  { id: "std-003", row_num: 3, name: "Rohan Mehta", apaar_id: "111222333444", course: "B.Tech AIML", year: "2025", category: "General", status: "Needs Correction", student_id_college: "MT003" },
  { id: "std-004", row_num: 4, name: "Sneha Patel", apaar_id: "555666777888", course: "B.Tech ME", year: "2025", category: "SC", status: "Valid", student_id_college: "MT004" },
  { id: "std-005", row_num: 5, name: "Karan Singh", apaar_id: "999888777666", course: "B.Tech CE", year: "2025", category: "OBC", status: "Flagged", student_id_college: "MT005" },
  { id: "std-006", row_num: 6, name: "Isha Verma", apaar_id: "222333444555", course: "B.Pharm", year: "2025", category: "General", status: "Valid", student_id_college: "MT006" },
  { id: "std-007", row_num: 7, name: "Aditya Rao", apaar_id: "333444555666", course: "MBA", year: "2025", category: "NRI", status: "Valid", student_id_college: "MT007" },
  { id: "std-008", row_num: 8, name: "Pooja Nair", apaar_id: "444555666777", course: "B.Tech CSE", year: "2025", category: "OCI", status: "Valid", student_id_college: "MT008" },
];

export default function StudentListPage() {
  const [students, setStudents] = useState<StudentRecord[]>(DEFAULT_RECORDS);
  const [search, setSearch] = useState("");
  const [course, setCourse] = useState("All Courses");
  const [category, setCategory] = useState("All Categories");
  const [statusFilter, setStatusFilter] = useState("All Status");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(585);
  const [viewStudent, setViewStudent] = useState<StudentRecord | null>(null);

  const fetchStudents = async () => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (course && course !== "All Courses") params.append("course", course);
      if (category && category !== "All Categories") params.append("category", category);
      if (statusFilter && statusFilter !== "All Status") params.append("status", statusFilter);
      params.append("page", String(page));
      params.append("page_size", "8");

      const res = await fetch(`${apiBase}/api/v1/institution/students?${params.toString()}`);
      if (res.ok) {
        const json = await res.json();
        setStudents(json.students);
        setTotalCount(json.total);
      }
    } catch {
      // Offline fallback: filter locally
      let filtered = DEFAULT_RECORDS;
      if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter(
          (s) =>
            s.name.toLowerCase().includes(q) ||
            s.apaar_id.includes(q) ||
            (s.student_id_college && s.student_id_college.toLowerCase().includes(q))
        );
      }
      if (course !== "All Courses") filtered = filtered.filter((s) => s.course === course);
      if (category !== "All Categories") filtered = filtered.filter((s) => s.category === category);
      if (statusFilter !== "All Status") filtered = filtered.filter((s) => s.status === statusFilter);
      setStudents(filtered);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchStudents();
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete student ${name}?`)) return;
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      await fetch(`${apiBase}/api/v1/institution/students/${id}`, { method: "DELETE" });
    } catch (err) {
      console.warn("Delete call failed", err);
    }
    setStudents(students.filter((s) => s.id !== id));
  };

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex">
      {/* Dark Navy Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopHeader />

        <main className="p-6 md:p-8 space-y-6 max-w-7xl">
          {/* Header Row: Title & + Add Student Button */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-800 tracking-tight">
                Student Records
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Manage and update student information
              </p>
            </div>

            <Link
              href="/students/new"
              className="bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold px-4 py-2.5 rounded-lg flex items-center gap-2 shadow-xs transition-colors"
            >
              <span className="text-sm font-bold leading-none">+</span>
              <span>Add Student</span>
            </Link>
          </div>

          {/* Search & Filter Bar */}
          <form
            onSubmit={handleSearchSubmit}
            className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs flex flex-wrap items-center gap-3"
          >
            {/* Search Input */}
            <div className="relative flex-1 min-w-[240px]">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <SearchIcon className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, APAAR ID, or student ID..."
                className="w-full text-xs pl-9 pr-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Course Filter Dropdown */}
            <select
              value={course}
              onChange={(e) => setCourse(e.target.value)}
              className="text-xs text-slate-700 bg-white border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer min-w-[130px]"
            >
              <option value="All Courses">All Courses</option>
              <option value="B.Tech CSE">B.Tech CSE</option>
              <option value="B.Tech ECE">B.Tech ECE</option>
              <option value="B.Tech AIML">B.Tech AIML</option>
              <option value="B.Tech ME">B.Tech ME</option>
              <option value="B.Tech CE">B.Tech CE</option>
              <option value="B.Pharm">B.Pharm</option>
              <option value="MBA">MBA</option>
            </select>

            {/* Category Filter Dropdown */}
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="text-xs text-slate-700 bg-white border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer min-w-[130px]"
            >
              <option value="All Categories">All Categories</option>
              <option value="General">General</option>
              <option value="OBC">OBC</option>
              <option value="SC">SC</option>
              <option value="ST">ST</option>
              <option value="NRI">NRI</option>
              <option value="OCI">OCI</option>
              <option value="FN">Foreign National</option>
            </select>

            {/* Status Filter Dropdown */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs text-slate-700 bg-white border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer min-w-[120px]"
            >
              <option value="All Status">All Status</option>
              <option value="Valid">Valid</option>
              <option value="Needs Correction">Needs Correction</option>
              <option value="Flagged">Flagged</option>
            </select>

            {/* Search Button */}
            <button
              type="submit"
              className="bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold px-5 py-2 rounded-lg shadow-2xs transition-colors cursor-pointer"
            >
              Search
            </button>
          </form>

          {/* Student Table Card */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-2xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold">
                    <th className="py-3 px-4 w-12 text-center">#</th>
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">APAAR ID</th>
                    <th className="py-3 px-4">Course</th>
                    <th className="py-3 px-4">Year</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center w-28">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {students.map((student, idx) => (
                    <tr
                      key={student.id}
                      className="hover:bg-slate-50/80 transition-colors"
                    >
                      <td className="py-3 px-4 text-center font-medium text-slate-500">
                        {student.row_num || idx + 1}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-800">
                        {student.name}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-600 tracking-wider">
                        {student.apaar_id}
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {student.course}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {student.year}
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {student.category}
                      </td>

                      {/* Status Badges */}
                      <td className="py-3 px-4 text-center">
                        {student.status === "Valid" && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Valid
                          </span>
                        )}
                        {student.status === "Needs Correction" && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                            Needs Correction
                          </span>
                        )}
                        {student.status === "Flagged" && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            Flagged
                          </span>
                        )}
                      </td>

                      {/* Actions: Eye, Pencil, Trash */}
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-2 text-slate-400">
                          <button
                            onClick={() => setViewStudent(student)}
                            title="View Student"
                            className="p-1 hover:text-blue-600 transition-colors cursor-pointer"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                          <Link
                            href="/students/new"
                            title="Edit Student"
                            className="p-1 hover:text-blue-600 transition-colors"
                          >
                            <PencilIcon className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() => handleDelete(student.id, student.name)}
                            title="Delete Record"
                            className="p-1 hover:text-rose-600 transition-colors cursor-pointer"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Footer */}
            <div className="px-4 py-3 bg-slate-50/50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <div>
                Showing 1-{students.length} of {totalCount}
              </div>

              <div className="flex items-center gap-1 font-medium">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="px-2 py-1 rounded-md border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  &lt;
                </button>
                <button
                  onClick={() => setPage(1)}
                  className={`px-2.5 py-1 rounded-md font-semibold ${
                    page === 1
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  1
                </button>
                <button
                  onClick={() => setPage(2)}
                  className={`px-2.5 py-1 rounded-md ${
                    page === 2
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  2
                </button>
                <button
                  onClick={() => setPage(3)}
                  className={`px-2.5 py-1 rounded-md ${
                    page === 3
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  3
                </button>
                <button
                  onClick={() => setPage(4)}
                  className={`px-2.5 py-1 rounded-md ${
                    page === 4
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  4
                </button>
                <button
                  onClick={() => setPage(5)}
                  className={`px-2.5 py-1 rounded-md ${
                    page === 5
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  5
                </button>
                <span className="px-1 text-slate-400">...</span>
                <button
                  onClick={() => setPage(74)}
                  className={`px-2 py-1 rounded-md ${
                    page === 74
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  74
                </button>
                <button
                  disabled={page >= 74}
                  onClick={() => setPage(page + 1)}
                  className="px-2 py-1 rounded-md border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  &gt;
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* View Student Modal */}
      {viewStudent && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">
                Student Record Details
              </h3>
              <button
                onClick={() => setViewStudent(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Name:</span>
                <span className="font-bold text-slate-800">{viewStudent.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">APAAR ID:</span>
                <span className="font-mono text-blue-600 font-semibold">{viewStudent.apaar_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Course:</span>
                <span className="text-slate-800 font-semibold">{viewStudent.course}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Admission Year:</span>
                <span className="text-slate-800">{viewStudent.year}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">College Student ID:</span>
                <span className="text-slate-800 font-mono">{viewStudent.student_id_college || "MT001"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Category:</span>
                <span className="text-slate-800 font-semibold">{viewStudent.category}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 font-medium">Verification Status:</span>
                <span
                  className={`px-2 py-0.5 rounded-full font-bold ${
                    viewStudent.status === "Valid"
                      ? "bg-emerald-100 text-emerald-800"
                      : viewStudent.status === "Needs Correction"
                      ? "bg-amber-100 text-amber-800"
                      : "bg-rose-100 text-rose-800"
                  }`}
                >
                  {viewStudent.status}
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setViewStudent(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
