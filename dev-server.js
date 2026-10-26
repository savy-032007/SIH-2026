/**
 * AICTE APAAR Platform - Unified Localhost Development Server
 * Serves the web frontend on port 3000 and the mock API backend on port 8000 (and 3000).
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const FRONTEND_PORT = 3000;
const API_PORT = 8000;

// In-Memory Data Store (Initialized with standard demo records)
const store = {
  profile: {
    institution_name: "MIT Academy of Engineering",
    institution_id: "INST001",
    aicte_approval_no: "1-12345678901",
    address: "Alandi Road, Pune, Maharashtra, India - 412105",
    contact_email: "admin@mitaoe.ac.in",
    contact_number: "+91 9876543210",
    academic_year: "2026",
    approved_intake: 600,
    logo_url: "/logo.png"
  },
  students: [
    {
      id: "std-001",
      row_num: 1,
      name: "Aarav Sharma",
      student_name: "Aarav Sharma",
      apaar_id: "123456789012",
      apaar: "123456789012",
      course: "B.Tech CSE",
      course_name: "B.Tech CSE",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "General",
      status: "Verified",
      apaar_status: "Verified",
      college_student_id: "MIT001",
      studentId: "MIT001",
      gender: "Male",
      dob: "2005-06-15",
      date_of_birth: "2005-06-15"
    },
    {
      id: "std-002",
      row_num: 2,
      name: "Neha Kapoor",
      student_name: "Neha Kapoor",
      apaar_id: "987654321098",
      apaar: "987654321098",
      course: "B.Tech ECE",
      course_name: "B.Tech ECE",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "OBC",
      status: "Verified",
      apaar_status: "Verified",
      college_student_id: "MIT002",
      studentId: "MIT002",
      gender: "Female",
      dob: "2005-08-22",
      date_of_birth: "2005-08-22"
    },
    {
      id: "std-003",
      row_num: 3,
      name: "Rohan Mehta",
      student_name: "Rohan Mehta",
      apaar_id: "111222333444",
      apaar: "111222333444",
      course: "B.Tech AIML",
      course_name: "B.Tech AIML",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "General",
      status: "Needs Correction",
      apaar_status: "Needs Correction",
      college_student_id: "MIT003",
      studentId: "MIT003",
      gender: "Male",
      dob: "2005-03-10",
      date_of_birth: "2005-03-10"
    },
    {
      id: "std-004",
      row_num: 4,
      name: "Sneha Patel",
      student_name: "Sneha Patel",
      apaar_id: "555666777888",
      apaar: "555666777888",
      course: "B.Tech Mechanical",
      course_name: "B.Tech Mechanical",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "SC",
      status: "Verified",
      apaar_status: "Verified",
      college_student_id: "MIT004",
      studentId: "MIT004",
      gender: "Female",
      dob: "2005-11-05",
      date_of_birth: "2005-11-05"
    },
    {
      id: "std-005",
      row_num: 5,
      name: "Karan Singh",
      student_name: "Karan Singh",
      apaar_id: "999888777666",
      apaar: "999888777666",
      course: "B.Tech CSE",
      course_name: "B.Tech CSE",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "OBC",
      status: "Flagged",
      apaar_status: "Flagged",
      college_student_id: "MIT005",
      studentId: "MIT005",
      gender: "Male",
      dob: "2004-12-18",
      date_of_birth: "2004-12-18"
    },
    {
      id: "std-006",
      row_num: 6,
      name: "Isha Verma",
      student_name: "Isha Verma",
      apaar_id: "222333444555",
      apaar: "222333444555",
      course: "B.Pharm",
      course_name: "B.Pharm",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "General",
      status: "Verified",
      apaar_status: "Verified",
      college_student_id: "MIT006",
      studentId: "MIT006",
      gender: "Female",
      dob: "2005-04-30",
      date_of_birth: "2005-04-30"
    },
    {
      id: "std-007",
      row_num: 7,
      name: "Aditya Rao",
      student_name: "Aditya Rao",
      apaar_id: "333444555666",
      apaar: "333444555666",
      course: "MBA",
      course_name: "MBA",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "NRI",
      status: "Verified",
      apaar_status: "Verified",
      college_student_id: "MIT007",
      studentId: "MIT007",
      gender: "Male",
      dob: "2003-09-14",
      date_of_birth: "2003-09-14"
    },
    {
      id: "std-008",
      row_num: 8,
      name: "Pooja Nair",
      student_name: "Pooja Nair",
      apaar_id: "444555666777",
      apaar: "444555666777",
      course: "B.Tech CSE",
      course_name: "B.Tech CSE",
      year: "2026",
      academic_year: "2026",
      admission_year: "2026",
      category: "OCI",
      status: "Verified",
      apaar_status: "Verified",
      college_student_id: "MIT008",
      studentId: "MIT008",
      gender: "Female",
      dob: "2005-01-25",
      date_of_birth: "2005-01-25"
    }
  ],
  activities: [
    { activity: "Batch Upload Validated", details: "540 student records processed", time: "Today, 02:15 PM" },
    { activity: "APAAR Verified", details: "Rohan Deshmukh (918273645012)", time: "Today, 11:30 AM" },
    { activity: "AICTE Compliance Sync", details: "Approved intake capacity verified", time: "Yesterday, 04:45 PM" }
  ],
  users: [
    { id: "usr-01", name: "Priya Verma", email: "admin@mitaoe.ac.in", role: "Institution Admin", status: "Active" },
    { id: "usr-02", name: "Rajesh Sharma", email: "registrar@mitaoe.ac.in", role: "Registrar / Verifier", status: "Active" },
    { id: "usr-03", name: "Ananya Joshi", email: "exam@mitaoe.ac.in", role: "Data Operator", status: "Active" }
  ],
  batches: [
    { id: "bat-01", filename: "aicte_2026_first_year.xlsx", records: 540, status: "Processed", date: "2026-10-24 14:15" },
    { id: "bat-02", filename: "lateral_entry_direct_sy.csv", records: 45, status: "Processed", date: "2026-10-22 10:30" }
  ],
  notifications: {
    validation_anomalies: true,
    data_upload_updates: true,
    security_alerts: true
  },
  security: {
    mfa_enforced: true,
    session_timeout_minutes: 15,
    field_level_encryption: "AES-256-GCM Active"
  }
};

// MIME Types
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf',
  '.ico': 'image/x-icon'
};

function readBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        resolve(JSON.parse(body || '{}'));
      } catch {
        // try URLSearchParams
        try {
          const params = new URLSearchParams(body);
          const obj = {};
          params.forEach((v, k) => obj[k] = v);
          resolve(obj);
        } catch {
          resolve({});
        }
      }
    });
  });
}

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  });
  res.end(JSON.stringify(data));
}

// Request Handler
async function handleRequest(req, res) {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;
  const method = req.method.toUpperCase();

  // CORS Preflight
  if (method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400'
    });
    res.end();
    return;
  }

  // Health
  if (pathname === '/health') {
    return sendJson(res, 200, {
      status: "ok",
      environment: "development",
      database: "up",
      adapters: { abc_registry: "mock", digilocker: "apisetu_sandbox" }
    });
  }

  // Auth: Token & Login
  if (pathname === '/api/v1/auth/token' || pathname === '/api/v1/auth/login') {
    const body = await readBody(req);
    const email = (body.username || body.email || "admin@xyzcollege.ac.in").toLowerCase();
    let role = body.role || "INST_ADMIN";
    let name = "Priya Verma";
    let roleName = "Institution Admin";

    if (email.includes("aicte") || role === "AICTE_ADMIN" || role === "AICTE_SUPER_ADMIN" || role === "AICTE Admin") {
      role = "AICTE_SUPER_ADMIN";
      roleName = "AICTE Admin";
      name = "Dr. Ramesh Unnikrishnan";
    } else if (email.includes("verifier") || role === "VERIFIER" || role.includes("Verifier")) {
      role = "VERIFIER";
      roleName = "Verifier / Employer";
      name = "Vikram Malhotra";
    }

    return sendJson(res, 200, {
      access_token: "dev-jwt-token-" + Date.now(),
      token_type: "bearer",
      role: role,
      user: {
        id: "usr-" + Date.now(),
        name: name,
        email: email,
        role: roleName
      }
    });
  }

  // Institution Profile
  if (pathname === '/api/v1/institution/profile') {
    if (method === 'PUT') {
      const body = await readBody(req);
      Object.assign(store.profile, body);
      return sendJson(res, 200, store.profile);
    }
    return sendJson(res, 200, store.profile);
  }

  // Institution Dashboard
  if (pathname === '/api/v1/institution/dashboard') {
    const intake = store.profile.approved_intake || 600;
    const actual = 585 + (store.students.length - 8);
    const remaining = Math.max(0, intake - actual);
    return sendJson(res, 200, {
      stats: {
        approved_intake: intake,
        actual_enrolment: actual,
        remaining_seats: remaining,
        total_students: actual
      },
      approved_intake: intake,
      actual_enrolment: actual,
      remaining_seats: remaining,
      total_students: actual,
      enrolment_trend: [
        { year: "2022", actual: 450, approved: intake },
        { year: "2023", actual: 485, approved: intake },
        { year: "2024", actual: 520, approved: intake },
        { year: "2025", actual: 565, approved: intake },
        { year: "2026", actual: actual, approved: intake }
      ],
      categories: { General: 280, OBC: 195, "SC / ST": 87, Other: 23 },
      activities: store.activities,
      recent_activities: store.activities
    });
  }

  // Verify APAAR
  if (pathname === '/api/v1/institution/students/verify-apaar') {
    const body = await readBody(req);
    const apaarId = String(body.apaar_id || '').trim();
    const isValid = /^\d{12}$/.test(apaarId) || apaarId.startsWith('EXEMPT-');
    if (!isValid) {
      return sendJson(res, 400, {
        valid: false,
        exists: false,
        message: "Invalid APAAR format: Must be 12 digits or approved exemption"
      });
    }
    return sendJson(res, 200, {
      valid: true,
      exists: true,
      status: "ACTIVE",
      masked_name: body.student_name ? body.student_name.slice(0, 1) + '****' : 'S****',
      sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      message: "Verified in ABC Registry: Name & DOB Match"
    });
  }

  // Students List / Create
  if (pathname === '/api/v1/institution/students') {
    if (method === 'POST') {
      const body = await readBody(req);
      const newStudent = {
        id: `std-${Date.now()}`,
        row_num: store.students.length + 1,
        ...body,
        name: body.student_name || body.name,
        apaar: body.apaar_id || body.apaar,
        status: "Verified",
        apaar_status: "Verified"
      };
      store.students.unshift(newStudent);
      store.activities.unshift({
        activity: "Student Added",
        details: `${newStudent.name} (${newStudent.apaar})`,
        time: "Just now"
      });
      return sendJson(res, 201, newStudent);
    }

    // Filter students
    let list = [...store.students];
    const q = (parsedUrl.query.q || '').toLowerCase();
    const course = parsedUrl.query.course;
    const cat = parsedUrl.query.category;
    const status = parsedUrl.query.status;

    if (q) {
      list = list.filter(s =>
        (s.name || '').toLowerCase().includes(q) ||
        (s.apaar || s.apaar_id || '').includes(q) ||
        (s.college_student_id || '').toLowerCase().includes(q)
      );
    }
    if (course) list = list.filter(s => s.course === course || s.course_name === course);
    if (cat) list = list.filter(s => s.category === cat);
    if (status) list = list.filter(s => s.status === status || s.apaar_status === status);

    return sendJson(res, 200, {
      total: list.length,
      items: list,
      students: list
    });
  }

  // Student Update / Delete
  if (pathname.startsWith('/api/v1/institution/students/')) {
    const studentId = pathname.replace('/api/v1/institution/students/', '');
    const idx = store.students.findIndex(s => String(s.id) === String(studentId));

    if (method === 'DELETE') {
      if (idx >= 0) {
        const removed = store.students.splice(idx, 1)[0];
        store.activities.unshift({
          activity: "Student Removed",
          details: `${removed.name} (${removed.apaar || ''})`,
          time: "Just now"
        });
      }
      return sendJson(res, 200, { message: "Student deleted" });
    }

    if (method === 'PUT') {
      const body = await readBody(req);
      if (idx >= 0) {
        store.students[idx] = { ...store.students[idx], ...body };
        store.activities.unshift({
          activity: "Student Updated",
          details: `${body.student_name || store.students[idx].name}`,
          time: "Just now"
        });
        return sendJson(res, 200, store.students[idx]);
      }
      return sendJson(res, 404, { error: "Student not found" });
    }
  }

  // Validation Results
  if (pathname === '/api/v1/institution/validation') {
    return sendJson(res, 200, {
      total_records: 585,
      valid: 571,
      needs_correction: 10,
      flagged: 4,
      issues: [
        { type: "Duplicate APAAR ID", rule: "V1.1", count: 2, severity: "High", status: "Under Review" },
        { type: "Missing / Invalid APAAR", rule: "V2.1", count: 5, severity: "High", status: "Under Review" },
        { type: "Approved Intake Cap", rule: "V3.1", count: 4, severity: "Critical", status: "Under Review" },
        { type: "Data Inconsistencies", rule: "V4.2", count: 3, severity: "Medium", status: "Under Review" }
      ],
      flagged_records: [
        { id: "flg-1", student_name: "Rohan Mehta", apaar_id: "111222333444", issue: "Missing APAAR ID", status: "Needs Correction" },
        { id: "flg-2", student_name: "Karan Singh", apaar_id: "999888777666", issue: "Duplicate APAAR ID", status: "Flagged" },
        { id: "flg-3", student_name: "Priya Desai", apaar_id: "123456789012", issue: "Excess Enrolment", status: "Flagged" },
        { id: "flg-4", student_name: "Amit Kumar", apaar_id: "777888999000", issue: "Inconsistent Data", status: "Needs Correction" }
      ]
    });
  }

  // Users
  if (pathname === '/api/v1/institution/users') {
    if (method === 'POST') {
      const body = await readBody(req);
      const newUser = { id: `usr-${Date.now()}`, ...body, status: "Active" };
      store.users.push(newUser);
      return sendJson(res, 201, newUser);
    }
    return sendJson(res, 200, store.users);
  }

  // Upload Batches
  if (pathname === '/api/v1/institution/upload-batches') {
    return sendJson(res, 200, store.batches);
  }

  // Notifications
  if (pathname === '/api/v1/institution/notifications') {
    if (method === 'PUT') {
      const body = await readBody(req);
      Object.assign(store.notifications, body);
      return sendJson(res, 200, store.notifications);
    }
    return sendJson(res, 200, store.notifications);
  }

  // Security
  if (pathname === '/api/v1/institution/security') {
    return sendJson(res, 200, store.security);
  }

  // Change Password
  if (pathname === '/api/v1/institution/change-password') {
    return sendJson(res, 200, { message: "Password updated successfully" });
  }

  // Static File Serving
  let filePath = path.join(process.cwd(), pathname === '/' ? 'index.html' : pathname);
  
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      // Fallback to index.html for single-page routing
      filePath = path.join(process.cwd(), 'index.html');
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    fs.readFile(filePath, (readErr, content) => {
      if (readErr) {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('500 Internal Server Error: ' + readErr.message);
        return;
      }
      res.writeHead(200, {
        'Content-Type': contentType,
        'Access-Control-Allow-Origin': '*'
      });
      res.end(content);
    });
  });
}

// Start Frontend Server on 3000
const server3000 = http.createServer(handleRequest);
server3000.listen(FRONTEND_PORT, '0.0.0.0', () => {
  console.log(`[Frontend + API] http://localhost:${FRONTEND_PORT}`);
});

// Start API Server on 8000
const server8000 = http.createServer(handleRequest);
server8000.listen(API_PORT, '0.0.0.0', () => {
  console.log(`[Backend API]    http://localhost:${API_PORT}`);
});
