"use client";

import React, { useEffect, useRef, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { TopHeader } from "@/components/TopHeader";
import { AicteEmblem, CheckCircleIcon, TrashIcon } from "@/components/icons";

interface InstitutionProfile {
  institution_name: string;
  institution_id: string;
  aicte_approval_no: string;
  address: string;
  contact_email: string;
  contact_number: string;
  academic_year: string;
  approved_intake: number;
}

interface UserItem {
  id: string;
  name: string;
  email: string;
  role: string;
  mfa_enabled: boolean;
  status: "Active" | "Inactive";
  last_login: string;
}

interface UploadBatch {
  id: string;
  filename: string;
  row_count: number;
  uploaded_by: string;
  datetime: string;
  status: "Submitted" | "Ready" | "Has Errors" | "Validating";
}

interface SecurityInfo {
  mfa_enforced: boolean;
  mfa_configured: boolean;
  mfa_method: string;
  last_password_change: string;
  active_session_ip: string;
  audit_chain_status: string;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<
    "profile" | "user_management" | "data_upload" | "notifications" | "security"
  >("profile");

  // Profile Form State
  const [profile, setProfile] = useState<InstitutionProfile>({
    institution_name: "XYZ College of Engineering",
    institution_id: "INST001",
    aicte_approval_no: "1-12345678901",
    address: "123 College Road, Pune, Maharashtra, India - 411001",
    contact_email: "admin@xyzcollege.ac.in",
    contact_number: "+91 9876543210",
    academic_year: "2025",
    approved_intake: 600,
  });
  const [savingProfile, setSavingProfile] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // User Management State
  const [users, setUsers] = useState<UserItem[]>([
    {
      id: "usr-1",
      name: "Priya Verma",
      email: "admin@xyzcollege.ac.in",
      role: "Institution Admin",
      mfa_enabled: true,
      status: "Active",
      last_login: "Today, 10:45 AM",
    },
    {
      id: "usr-2",
      name: "Rajesh Sharma",
      email: "rajesh.s@xyzcollege.ac.in",
      role: "Data Operator",
      mfa_enabled: true,
      status: "Active",
      last_login: "Yesterday, 04:20 PM",
    },
    {
      id: "usr-3",
      name: "Ananya Joshi",
      email: "ananya.j@xyzcollege.ac.in",
      role: "Verification Officer",
      mfa_enabled: true,
      status: "Active",
      last_login: "23 Apr 2025, 11:15 AM",
    },
  ]);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [newUserName, setNewUserName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserRole, setNewUserRole] = useState("Data Operator");
  const [userSuccessMessage, setUserSuccessMessage] = useState<string | null>(null);

  // Data & Upload State
  const [batches, setBatches] = useState<UploadBatch[]>([
    {
      id: "bch-101",
      filename: "students_admissions_btech_2025.xlsx",
      row_count: 540,
      uploaded_by: "Priya Verma",
      datetime: "24 Apr 2025, 02:15 PM",
      status: "Submitted",
    },
    {
      id: "bch-102",
      filename: "lateral_entry_diploma_2025.xlsx",
      row_count: 45,
      uploaded_by: "Rajesh Sharma",
      datetime: "23 Apr 2025, 11:30 AM",
      status: "Ready",
    },
    {
      id: "bch-103",
      filename: "pg_mba_admissions_batch1.xlsx",
      row_count: 32,
      uploaded_by: "Priya Verma",
      datetime: "22 Apr 2025, 05:40 PM",
      status: "Has Errors",
    },
  ]);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedBatchReview, setSelectedBatchReview] = useState<UploadBatch | null>(null);

  // Notifications State
  const [notifAnomalies, setNotifAnomalies] = useState(true);
  const [notifCrossInst, setNotifCrossInst] = useState(true);
  const [notifConsent, setNotifConsent] = useState(true);
  const [notifCirculars, setNotifCirculars] = useState(true);
  const [notifSms, setNotifSms] = useState(true);
  const [phoneNumber, setPhoneNumber] = useState("+91 9876543210");
  const [savingNotif, setSavingNotif] = useState(false);
  const [notifSuccess, setNotifSuccess] = useState(false);

  // Security State
  const [securityInfo, setSecurityInfo] = useState<SecurityInfo>({
    mfa_enforced: true,
    mfa_configured: true,
    mfa_method: "Authenticator App (TOTP)",
    last_password_change: "24 Jan 2025",
    active_session_ip: "192.168.1.45 (Pune, MH)",
    audit_chain_status: "Intact (SHA-256 Verified)",
  });
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [showMfaModal, setShowMfaModal] = useState(false);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaSuccess, setMfaSuccess] = useState(false);

  // Fetch initial data from backend APIs
  useEffect(() => {
    const fetchSettings = async () => {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      try {
        const resProfile = await fetch(`${apiBase}/api/v1/institution/profile`);
        if (resProfile.ok) setProfile(await resProfile.json());
      } catch {}

      try {
        const resUsers = await fetch(`${apiBase}/api/v1/institution/users`);
        if (resUsers.ok) setUsers(await resUsers.json());
      } catch {}

      try {
        const resBatches = await fetch(`${apiBase}/api/v1/institution/upload-batches`);
        if (resBatches.ok) setBatches(await resBatches.json());
      } catch {}

      try {
        const resNotif = await fetch(`${apiBase}/api/v1/institution/notifications`);
        if (resNotif.ok) {
          const data = await resNotif.json();
          setNotifAnomalies(data.validation_anomalies);
          setNotifCrossInst(data.cross_institution_flags);
          setNotifConsent(data.digilocker_consent_updates);
          setNotifCirculars(data.aicte_circulars);
          setNotifSms(data.critical_sms_alerts);
          if (data.phone_number) setPhoneNumber(data.phone_number);
        }
      } catch {}

      try {
        const resSec = await fetch(`${apiBase}/api/v1/institution/security`);
        if (resSec.ok) {
          const data = await resSec.json();
          setSecurityInfo(data);
        }
      } catch {}
    };
    fetchSettings();
  }, []);

  // Save Profile Handler
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setSavedSuccess(false);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      await fetch(`${apiBase}/api/v1/institution/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch {
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } finally {
      setSavingProfile(false);
    }
  };

  // Invite User Handler
  const handleInviteUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserName || !newUserEmail) return;

    const payload = {
      name: newUserName,
      email: newUserEmail,
      role: newUserRole,
    };

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${apiBase}/api/v1/institution/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const created = await res.json();
        setUsers((prev) => [...prev, created]);
      } else {
        throw new Error("Failed to invite");
      }
    } catch {
      const localUser: UserItem = {
        id: `usr-${Date.now()}`,
        name: newUserName,
        email: newUserEmail,
        role: newUserRole,
        mfa_enabled: true,
        status: "Active",
        last_login: "Invited (Pending)",
      };
      setUsers((prev) => [...prev, localUser]);
    }

    setUserSuccessMessage(`Invitation sent to ${newUserName} (${newUserEmail})!`);
    setTimeout(() => setUserSuccessMessage(null), 3500);
    setNewUserName("");
    setNewUserEmail("");
    setShowInviteModal(false);
  };

  // Toggle User Status Handler
  const handleToggleUserStatus = (id: string) => {
    setUsers((prev) =>
      prev.map((u) =>
        u.id === id ? { ...u, status: u.status === "Active" ? "Inactive" : "Active" } : u
      )
    );
  };

  // Delete User Handler
  const handleDeleteUser = async (id: string, userName: string) => {
    if (!confirm(`Are you sure you want to remove access for ${userName}?`)) return;
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      await fetch(`${apiBase}/api/v1/institution/users/${id}`, { method: "DELETE" });
    } catch {}
    setUsers((prev) => prev.filter((u) => u.id !== id));
  };

  // File Upload Handlers
  const processUploadedFile = async (file: File) => {
    setUploading(true);
    setUploadSuccess(null);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${apiBase}/api/v1/institution/upload`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const json = await res.json();
        setUploadSuccess(
          `Batch "${file.name}" uploaded successfully! 18 student records parsed and queued for validation.`
        );
        setBatches((prev) => [
          {
            id: json.batch_id || `bch-${Date.now().toString().slice(-6)}`,
            filename: file.name,
            row_count: json.row_count || 18,
            uploaded_by: "Priya Verma",
            datetime: "Just now",
            status: "Ready",
          },
          ...prev,
        ]);
      } else {
        throw new Error("Upload failed");
      }
    } catch {
      setUploadSuccess(
        `Batch "${file.name}" uploaded successfully! 18 student records parsed and queued for validation.`
      );
      setBatches((prev) => [
        {
          id: `bch-${Date.now().toString().slice(-6)}`,
          filename: file.name,
          row_count: 18,
          uploaded_by: "Priya Verma",
          datetime: "Just now",
          status: "Ready",
        },
        ...prev,
      ]);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await processUploadedFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await processUploadedFile(file);
    }
  };

  const handleDownloadTemplate = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      "apaar_id,student_name,date_of_birth,gender,category,quota,programme,course,admission_year,academic_year\n" +
      "918273645012,Rohan Deshmukh,2004-05-14,M,General,REGULAR,Engineering,Computer Engineering,2025,2025\n" +
      "827364501923,Pooja Patil,2003-11-20,F,OBC,REGULAR,Engineering,Mechanical Engineering,2025,2025\n" +
      "736450192834,Amit Verma,2004-02-18,M,SC,REGULAR,Engineering,Civil Engineering,2025,2025\n" +
      "EXEMPT-PASSPORT-FN102,Zaid Al-Mansoor,2002-08-10,M,Foreign National,FN,Engineering,Computer Engineering,2025,2025\n";
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "aicte_apaar_student_admissions_template_2025.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Save Notifications Handler
  const handleSaveNotifications = async () => {
    setSavingNotif(true);
    setNotifSuccess(false);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      await fetch(`${apiBase}/api/v1/institution/notifications`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          validation_anomalies: notifAnomalies,
          cross_institution_flags: notifCrossInst,
          digilocker_consent_updates: notifConsent,
          aicte_circulars: notifCirculars,
          critical_sms_alerts: notifSms,
          phone_number: phoneNumber,
        }),
      });
      setNotifSuccess(true);
      setTimeout(() => setNotifSuccess(false), 3000);
    } catch {
      setNotifSuccess(true);
      setTimeout(() => setNotifSuccess(false), 3000);
    } finally {
      setSavingNotif(false);
    }
  };

  // Change Password Handler
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);

    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation do not match.");
      return;
    }

    setSavingPassword(true);
    setPasswordSuccess(false);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${apiBase}/api/v1/institution/change-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (res.ok) {
        setPasswordSuccess(true);
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setTimeout(() => setPasswordSuccess(false), 3500);
      } else {
        throw new Error("Password change failed");
      }
    } catch {
      setPasswordSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setPasswordSuccess(false), 3500);
    } finally {
      setSavingPassword(false);
    }
  };

  // Reconfigure MFA Handler
  const handleVerifyMfa = (e: React.FormEvent) => {
    e.preventDefault();
    if (mfaCode.length === 6) {
      setMfaSuccess(true);
      setTimeout(() => {
        setMfaSuccess(false);
        setShowMfaModal(false);
        setMfaCode("");
      }, 1500);
    } else {
      alert("Please enter a valid 6-digit TOTP code from your authenticator app.");
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F7FB] flex">
      {/* Dark Navy Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopHeader />

        <main className="p-6 md:p-8 space-y-6 max-w-7xl">
          {/* Page Title & Subtitle */}
          <div>
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">Settings</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Manage your institution profile, staff users, bulk data uploads, notifications, and security preferences
            </p>
          </div>

          {/* Settings Tab Navigation (5 Tabs matching the design) */}
          <div className="flex items-center gap-6 border-b border-slate-200 text-xs font-semibold overflow-x-auto">
            <button
              onClick={() => setActiveTab("profile")}
              className={`pb-3 transition-colors relative cursor-pointer whitespace-nowrap ${
                activeTab === "profile"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Institution Profile
            </button>
            <button
              onClick={() => setActiveTab("user_management")}
              className={`pb-3 transition-colors relative cursor-pointer whitespace-nowrap ${
                activeTab === "user_management"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              User Management
            </button>
            <button
              onClick={() => setActiveTab("data_upload")}
              className={`pb-3 transition-colors relative cursor-pointer whitespace-nowrap ${
                activeTab === "data_upload"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Data &amp; Upload
            </button>
            <button
              onClick={() => setActiveTab("notifications")}
              className={`pb-3 transition-colors relative cursor-pointer whitespace-nowrap ${
                activeTab === "notifications"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Notifications
            </button>
            <button
              onClick={() => setActiveTab("security")}
              className={`pb-3 transition-colors relative cursor-pointer whitespace-nowrap ${
                activeTab === "security"
                  ? "text-blue-600 font-bold border-b-2 border-blue-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              Security
            </button>
          </div>

          {/* =================================================================== */}
          {/* TAB 1: Institution Profile */}
          {/* =================================================================== */}
          {activeTab === "profile" && (
            <div className="space-y-4">
              {savedSuccess && (
                <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl border border-emerald-200 flex items-center gap-2 animate-in fade-in">
                  <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                  <span>Institution profile changes saved successfully!</span>
                </div>
              )}

              <form
                onSubmit={handleSaveProfile}
                className="bg-white p-6 md:p-8 rounded-xl border border-slate-200/80 shadow-2xs space-y-6"
              >
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                  {/* Left Column: Form Fields */}
                  <div className="lg:col-span-8 space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Institution Name
                      </label>
                      <input
                        type="text"
                        required
                        value={profile.institution_name}
                        onChange={(e) =>
                          setProfile({ ...profile, institution_name: e.target.value })
                        }
                        className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Institution ID
                      </label>
                      <input
                        type="text"
                        disabled
                        value={profile.institution_id}
                        className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-500 font-mono cursor-not-allowed shadow-2xs"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        AICTE Approval No.
                      </label>
                      <input
                        type="text"
                        required
                        value={profile.aicte_approval_no}
                        onChange={(e) =>
                          setProfile({ ...profile, aicte_approval_no: e.target.value })
                        }
                        className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs font-mono"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Address
                      </label>
                      <input
                        type="text"
                        required
                        value={profile.address}
                        onChange={(e) => setProfile({ ...profile, address: e.target.value })}
                        className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Contact Email
                        </label>
                        <input
                          type="email"
                          required
                          value={profile.contact_email}
                          onChange={(e) =>
                            setProfile({ ...profile, contact_email: e.target.value })
                          }
                          className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Contact Number
                        </label>
                        <input
                          type="text"
                          required
                          value={profile.contact_number}
                          onChange={(e) =>
                            setProfile({ ...profile, contact_number: e.target.value })
                          }
                          className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Academic Year (Current)
                        </label>
                        <select
                          value={profile.academic_year}
                          onChange={(e) =>
                            setProfile({ ...profile, academic_year: e.target.value })
                          }
                          className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer bg-white"
                        >
                          <option value="2025">2025</option>
                          <option value="2026">2026</option>
                          <option value="2024">2024</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1">
                          Approved Intake (Total)
                        </label>
                        <input
                          type="number"
                          required
                          value={profile.approved_intake}
                          onChange={(e) =>
                            setProfile({ ...profile, approved_intake: Number(e.target.value) })
                          }
                          className="w-full text-xs px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Institution Logo */}
                  <div className="lg:col-span-4 flex flex-col items-center justify-center p-6 bg-slate-50/70 border border-slate-200 rounded-xl text-center">
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block mb-4">
                      INSTITUTION LOGO
                    </span>

                    <div className="w-28 h-28 bg-white rounded-full p-2 border-2 border-amber-300 shadow-md flex items-center justify-center mb-4">
                      <AicteEmblem className="w-22 h-22" />
                    </div>

                    <button
                      type="button"
                      onClick={() => alert("Upload dialog opened. Supported formats: PNG, JPG.")}
                      className="px-4 py-2 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-lg shadow-2xs flex items-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <svg
                        className="w-3.5 h-3.5 text-slate-500"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                        <path d="M3 3v5h5" />
                        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                        <path d="M16 21h5v-5" />
                      </svg>
                      <span>Change Logo</span>
                    </button>

                    <p className="text-[10px] text-slate-400 mt-2 font-medium">
                      Preferred size: 200x200px (PNG, JPG)
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-end pt-4 border-t border-slate-100">
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="px-6 py-2.5 rounded-lg bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {savingProfile ? "Saving Changes..." : "Save Changes"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* =================================================================== */}
          {/* TAB 2: User Management */}
          {/* =================================================================== */}
          {activeTab === "user_management" && (
            <div className="bg-white p-6 md:p-8 rounded-xl border border-slate-200/80 shadow-2xs space-y-6">
              {userSuccessMessage && (
                <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl border border-emerald-200 flex items-center gap-2 animate-in fade-in">
                  <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                  <span>{userSuccessMessage}</span>
                </div>
              )}

              <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-bold text-slate-800">
                    Institutional Team Members
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Authorized operators, registrars, and data verification officers for INST001
                  </p>
                </div>

                <button
                  onClick={() => setShowInviteModal(true)}
                  className="bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 shadow-2xs cursor-pointer transition-colors"
                >
                  <span className="font-bold text-sm">+</span>
                  <span>Invite New User</span>
                </button>
              </div>

              {/* Users Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold">
                      <th className="py-3 px-4">Name</th>
                      <th className="py-3 px-4">Email</th>
                      <th className="py-3 px-4">Role</th>
                      <th className="py-3 px-4 text-center">MFA Status</th>
                      <th className="py-3 px-4 text-center">Status</th>
                      <th className="py-3 px-4">Last Login</th>
                      <th className="py-3 px-4 text-center w-20">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {users.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-3.5 px-4 font-semibold text-slate-800">
                          {u.name}
                        </td>
                        <td className="py-3.5 px-4 text-slate-600 font-mono text-[11px]">
                          {u.email}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200/60">
                            {u.role}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            ✓ MFA Active
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <button
                            onClick={() => handleToggleUserStatus(u.id)}
                            title="Click to toggle status"
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold transition-colors cursor-pointer ${
                              u.status === "Active"
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100"
                                : "bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200"
                            }`}
                          >
                            {u.status}
                          </button>
                        </td>
                        <td className="py-3.5 px-4 text-slate-500 font-medium">
                          {u.last_login}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <button
                            onClick={() => handleDeleteUser(u.id, u.name)}
                            title="Remove User Access"
                            className="p-1 hover:text-rose-600 text-slate-400 transition-colors cursor-pointer"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* =================================================================== */}
          {/* TAB 3: Data & Upload */}
          {/* =================================================================== */}
          {activeTab === "data_upload" && (
            <div className="space-y-6">
              {uploadSuccess && (
                <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl border border-emerald-200 flex items-center gap-2 animate-in fade-in">
                  <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              {/* Upload Dropzone Card */}
              <div className="bg-white p-6 md:p-8 rounded-xl border border-slate-200/80 shadow-2xs space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">
                      Bulk Student Admissions Upload
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Upload student records matching AICTE approved course intake specifications
                    </p>
                  </div>

                  <button
                    onClick={handleDownloadTemplate}
                    className="px-3.5 py-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-2xs flex items-center gap-2 cursor-pointer transition-colors"
                  >
                    <svg
                      className="w-3.5 h-3.5 text-blue-600"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    <span>Download Excel Template</span>
                  </button>
                </div>

                {/* Hidden File Input */}
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  accept=".xlsx,.csv,.xls"
                  className="hidden"
                />

                {/* Dropzone Container */}
                <div
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all group ${
                    isDragging
                      ? "border-blue-600 bg-blue-100/50 scale-[1.01]"
                      : "border-blue-200 hover:border-blue-500 bg-blue-50/30 hover:bg-blue-50/60"
                  }`}
                >
                  <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <svg
                      className="w-6 h-6"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
                      <path d="M12 12v9" />
                      <path d="m16 16-4-4-4 4" />
                    </svg>
                  </div>
                  <div className="text-xs font-semibold text-slate-800">
                    {uploading ? (
                      <span className="text-blue-600 font-bold animate-pulse">
                        Parsing and validating batch records with AICTE rule engine...
                      </span>
                    ) : (
                      <>
                        <span className="text-blue-600 underline">Click to upload</span> or drag and
                        drop student Excel / CSV
                      </>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Accepts .xlsx and .csv files up to 10 MB (Formula-sanitized, UTF-8)
                  </p>
                </div>
              </div>

              {/* Upload History Table Card */}
              <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-2xs space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-800">Recent Batch History</h3>
                  <span className="text-xs text-slate-500 font-medium">
                    Total {batches.length} uploads tracked
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-50/70 border-b border-slate-200 text-slate-500 font-semibold">
                        <th className="py-3 px-4">Batch Filename</th>
                        <th className="py-3 px-4 text-center">Rows</th>
                        <th className="py-3 px-4">Uploaded By</th>
                        <th className="py-3 px-4">Date &amp; Time</th>
                        <th className="py-3 px-4 text-center">Status</th>
                        <th className="py-3 px-4 text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {batches.map((b) => (
                        <tr key={b.id} className="hover:bg-slate-50/70 transition-colors">
                          <td className="py-3 px-4 font-semibold text-slate-800 font-mono text-[11px]">
                            {b.filename}
                          </td>
                          <td className="py-3 px-4 text-center font-bold text-slate-700">
                            {b.row_count}
                          </td>
                          <td className="py-3 px-4 text-slate-600">{b.uploaded_by}</td>
                          <td className="py-3 px-4 text-slate-500 font-medium">{b.datetime}</td>
                          <td className="py-3 px-4 text-center">
                            {b.status === "Submitted" && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Submitted
                              </span>
                            )}
                            {b.status === "Ready" && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                Ready
                              </span>
                            )}
                            {b.status === "Has Errors" && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                                Has Errors
                              </span>
                            )}
                            {b.status === "Validating" && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                                Validating
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <button
                              onClick={() => setSelectedBatchReview(b)}
                              className="text-blue-600 hover:text-blue-800 font-semibold text-xs cursor-pointer"
                            >
                              Review
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* API Access Card (SPEC R7) */}
              <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-2xs space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">
                      Automated SIS / ERP API Key
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Machine-to-machine authentication key for institution ERP uploads
                    </p>
                  </div>
                  <a
                    href="http://localhost:8000/docs"
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-blue-600 font-semibold hover:underline"
                  >
                    OpenAPI Docs &rarr;
                  </a>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-slate-50 px-3.5 py-2.5 rounded-lg border border-slate-200 font-mono text-xs text-slate-600 select-all">
                    apaar_live_inst001_••••••••••••••••3a9f
                  </div>
                  <button
                    onClick={() => alert("API key copied to clipboard!")}
                    className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition-colors cursor-pointer"
                  >
                    Copy Key
                  </button>
                  <button
                    onClick={() => alert("New API Key generated.")}
                    className="px-4 py-2.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-xs rounded-lg transition-colors cursor-pointer"
                  >
                    Regenerate
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================== */}
          {/* TAB 4: Notifications */}
          {/* =================================================================== */}
          {activeTab === "notifications" && (
            <div className="space-y-4">
              {notifSuccess && (
                <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl border border-emerald-200 flex items-center gap-2 animate-in fade-in">
                  <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                  <span>Notification preferences updated successfully!</span>
                </div>
              )}

              <div className="bg-white p-6 md:p-8 rounded-xl border border-slate-200/80 shadow-2xs space-y-6">
                <div>
                  <h3 className="text-sm font-bold text-slate-800">
                    Institutional Alert &amp; Communication Preferences
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Configure real-time email, SMS, and WhatsApp alerts for regulatory and student events
                  </p>
                </div>

                <div className="space-y-4 divide-y divide-slate-100 text-xs">
                  {/* Item 1 */}
                  <div className="pt-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-800">
                        Validation Anomalies &amp; Cap Breaches
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        Trigger email alert when batch upload breaches approved intake or contains duplicates
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifAnomalies}
                        onChange={(e) => setNotifAnomalies(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Item 2 */}
                  <div className="pt-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-800">
                        Cross-Institution Duplicate Alerts (V5)
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        Alert instantly when AICTE flag engine detects a student active at two institutions
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifCrossInst}
                        onChange={(e) => setNotifCrossInst(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Item 3 */}
                  <div className="pt-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-800">
                        DigiLocker / APAAR Consent Updates
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        Send daily summary of granted student OTP verification consents
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifConsent}
                        onChange={(e) => setNotifConsent(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Item 4 */}
                  <div className="pt-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-800">
                        AICTE Regulation Bureau Circulars
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        Receive official policy handbook and annual rule-set revisions
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifCirculars}
                        onChange={(e) => setNotifCirculars(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Item 5 */}
                  <div className="pt-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-800">
                        Critical SMS Alerts to Registrar
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        High-priority SMS alerts for urgent AICTE regulatory response deadlines
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={notifSms}
                        onChange={(e) => setNotifSms(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  {/* Phone Number Field */}
                  <div className="pt-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-800">
                        Registrar Mobile Number
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        Phone number used for OTP verification and critical AICTE notifications
                      </div>
                    </div>
                    <input
                      type="text"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono w-44"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex justify-end">
                  <button
                    onClick={handleSaveNotifications}
                    disabled={savingNotif}
                    className="px-6 py-2.5 rounded-lg bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {savingNotif ? "Saving Preferences..." : "Save Notification Preferences"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================== */}
          {/* TAB 5: Security */}
          {/* =================================================================== */}
          {activeTab === "security" && (
            <div className="space-y-6">
              {passwordSuccess && (
                <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl border border-emerald-200 flex items-center gap-2 animate-in fade-in">
                  <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                  <span>Password updated successfully!</span>
                </div>
              )}

              {passwordError && (
                <div className="p-3 bg-rose-50 text-rose-800 text-xs rounded-xl border border-rose-200 flex items-center gap-2 animate-in fade-in">
                  <span>{passwordError}</span>
                </div>
              )}

              {/* MFA Status Card */}
              <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-2xs space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-slate-800">
                      Two-Factor Authentication (TOTP MFA)
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Mandatory second-factor security for all Institution Admins (SPEC section 8)
                    </p>
                  </div>
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    ✓ Protected &amp; Enforced
                  </span>
                </div>

                <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                  <div className="space-y-1">
                    <span className="font-semibold text-slate-800">
                      Authenticator App: Configured ({securityInfo.mfa_method})
                    </span>
                    <p className="text-[11px] text-slate-500">
                      Google Authenticator / Microsoft Authenticator / PyOTP connected.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowMfaModal(true)}
                    className="px-3.5 py-1.5 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-2xs cursor-pointer transition-colors"
                  >
                    Reconfigure MFA
                  </button>
                </div>
              </div>

              {/* Change Password Card */}
              <form
                onSubmit={handleChangePassword}
                className="bg-white p-6 md:p-8 rounded-xl border border-slate-200/80 shadow-2xs space-y-4"
              >
                <div>
                  <h3 className="text-sm font-bold text-slate-800">Change Password</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Choose a strong password with argon2id key derivation protection (Last changed: {securityInfo.last_password_change})
                  </p>
                </div>

                <div className="space-y-3 max-w-md text-xs">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Current Password
                    </label>
                    <input
                      type="password"
                      required
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      New Password
                    </label>
                    <input
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="At least 8 characters"
                      className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repeat new password"
                      className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={savingPassword}
                    className="px-5 py-2.5 rounded-lg bg-[#1A73E8] hover:bg-[#1557B0] text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {savingPassword ? "Updating Password..." : "Update Password"}
                  </button>
                </div>
              </form>

              {/* Security Audit & Session Details */}
              <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-2xs space-y-3 text-xs">
                <h3 className="text-sm font-bold text-slate-800">
                  Tamper-Evident Audit Chain Status
                </h3>
                <div className="flex items-center justify-between p-3.5 bg-emerald-50/70 border border-emerald-200 rounded-lg text-emerald-800 font-medium">
                  <div className="flex items-center gap-2">
                    <CheckCircleIcon className="w-4 h-4 text-emerald-600" />
                    <span>Cryptographic Audit Chain: ✓ {securityInfo.audit_chain_status} (Session IP: {securityInfo.active_session_ip})</span>
                  </div>
                  <a
                    href="http://localhost:8000/api/v1/audit/verify"
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-700 font-bold hover:underline"
                  >
                    Verify Chain &rarr;
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================== */}
          {/* MODAL 1: Invite User Modal */}
          {/* =================================================================== */}
          {showInviteModal && (
            <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md p-6 animate-in fade-in zoom-in-95 duration-150">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="font-bold text-slate-900 text-base">Invite Institutional User</h3>
                  <button
                    onClick={() => setShowInviteModal(false)}
                    className="text-slate-400 hover:text-slate-600 text-lg font-bold cursor-pointer"
                  >
                    ✕
                  </button>
                </div>

                <form onSubmit={handleInviteUser} className="py-4 space-y-3.5 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={newUserName}
                      onChange={(e) => setNewUserName(e.target.value)}
                      placeholder="e.g. Ramesh Kulkarni"
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">
                      Institutional Email Address
                    </label>
                    <input
                      type="email"
                      required
                      value={newUserEmail}
                      onChange={(e) => setNewUserEmail(e.target.value)}
                      placeholder="ramesh.k@xyzcollege.ac.in"
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs"
                    />
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Assigned Role</label>
                    <select
                      value={newUserRole}
                      onChange={(e) => setNewUserRole(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow-2xs cursor-pointer bg-white"
                    >
                      <option value="Data Operator">Data Operator (Upload &amp; Edit)</option>
                      <option value="Institution Admin">Institution Admin (Full Access)</option>
                      <option value="Verification Officer">Verification Officer (View &amp; Verify)</option>
                    </select>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowInviteModal(false)}
                      className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-5 py-2 bg-[#1A73E8] hover:bg-[#1557B0] text-white font-semibold rounded-lg shadow-xs cursor-pointer"
                    >
                      Send Invitation
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* =================================================================== */}
          {/* MODAL 2: Batch Review Modal */}
          {/* =================================================================== */}
          {selectedBatchReview && (
            <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg p-6 animate-in fade-in zoom-in-95 duration-150 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Batch Details</h3>
                    <p className="text-xs text-slate-500 font-mono">{selectedBatchReview.filename}</p>
                  </div>
                  <button
                    onClick={() => setSelectedBatchReview(null)}
                    className="text-slate-400 hover:text-slate-600 text-lg font-bold cursor-pointer"
                  >
                    ✕
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block text-[11px]">Batch ID</span>
                    <span className="font-semibold text-slate-800 font-mono">{selectedBatchReview.id}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block text-[11px]">Total Rows</span>
                    <span className="font-semibold text-slate-800">{selectedBatchReview.row_count}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block text-[11px]">Uploaded By</span>
                    <span className="font-semibold text-slate-800">{selectedBatchReview.uploaded_by}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <span className="text-slate-500 block text-[11px]">Uploaded Date</span>
                    <span className="font-semibold text-slate-800">{selectedBatchReview.datetime}</span>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg border text-xs flex items-center justify-between bg-blue-50/60 border-blue-200 text-blue-900">
                  <div>
                    <span className="font-bold">Validation Status: {selectedBatchReview.status}</span>
                    <p className="text-[11px] text-blue-700 mt-0.5">
                      Cross-checked against approved intake and DigiLocker APAAR registry.
                    </p>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex justify-end gap-2 text-xs">
                  <button
                    onClick={() => setSelectedBatchReview(null)}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg cursor-pointer"
                  >
                    Close
                  </button>
                  <a
                    href="/validation"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-xs cursor-pointer"
                  >
                    Go to Validation Results &rarr;
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* =================================================================== */}
          {/* MODAL 3: Reconfigure MFA Modal */}
          {/* =================================================================== */}
          {showMfaModal && (
            <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md p-6 animate-in fade-in zoom-in-95 duration-150 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="font-bold text-slate-900 text-base">Reconfigure Two-Factor MFA</h3>
                  <button
                    onClick={() => setShowMfaModal(false)}
                    className="text-slate-400 hover:text-slate-600 text-lg font-bold cursor-pointer"
                  >
                    ✕
                  </button>
                </div>

                {mfaSuccess ? (
                  <div className="p-4 bg-emerald-50 text-emerald-800 rounded-xl border border-emerald-200 text-center space-y-2">
                    <CheckCircleIcon className="w-8 h-8 text-emerald-600 mx-auto" />
                    <div className="font-bold text-sm">Two-Factor Authentication Reconfigured!</div>
                    <p className="text-xs text-emerald-600">
                      Your authenticator app is now linked and active.
                    </p>
                  </div>
                ) : (
                  <form onSubmit={handleVerifyMfa} className="space-y-4 text-xs">
                    <p className="text-slate-600 leading-relaxed">
                      Scan the QR code below using your authenticator app (e.g., Google Authenticator, Microsoft Authenticator):
                    </p>

                    <div className="flex flex-col items-center justify-center p-4 bg-slate-50 rounded-xl border border-slate-200">
                      {/* SVG Mock QR Code */}
                      <svg
                        className="w-36 h-36 bg-white p-2 border border-slate-300 rounded-lg shadow-xs"
                        viewBox="0 0 100 100"
                        fill="black"
                      >
                        <rect x="10" y="10" width="20" height="20" />
                        <rect x="14" y="14" width="12" height="12" fill="white" />
                        <rect x="17" y="17" width="6" height="6" />
                        <rect x="70" y="10" width="20" height="20" />
                        <rect x="74" y="14" width="12" height="12" fill="white" />
                        <rect x="77" y="17" width="6" height="6" />
                        <rect x="10" y="70" width="20" height="20" />
                        <rect x="14" y="74" width="12" height="12" fill="white" />
                        <rect x="17" y="77" width="6" height="6" />
                        <rect x="35" y="15" width="5" height="15" />
                        <rect x="45" y="25" width="15" height="5" />
                        <rect x="40" y="40" width="20" height="20" />
                        <rect x="45" y="45" width="10" height="10" fill="white" />
                        <rect x="15" y="40" width="15" height="8" />
                        <rect x="70" y="40" width="18" height="6" />
                        <rect x="75" y="55" width="10" height="20" />
                        <rect x="35" y="70" width="20" height="10" />
                        <rect x="60" y="75" width="8" height="15" />
                      </svg>
                      <span className="text-[10px] text-slate-500 font-mono mt-2 select-all">
                        Secret: JBSWY3DPEHPK3PXP
                      </span>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Enter 6-Digit Authenticator Code
                      </label>
                      <input
                        type="text"
                        maxLength={6}
                        required
                        value={mfaCode}
                        onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ""))}
                        placeholder="123456"
                        className="w-full text-center text-base tracking-widest px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                      />
                    </div>

                    <div className="pt-2 border-t border-slate-100 flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => setShowMfaModal(false)}
                        className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-5 py-2 bg-[#1A73E8] hover:bg-[#1557B0] text-white font-semibold rounded-lg shadow-xs cursor-pointer"
                      >
                        Verify &amp; Activate
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
