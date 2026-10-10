-- ============================================================
-- Celia database schema (SQLite)
-- Rule: dates as 'YYYY-MM-DD', times as 'HH:MM' (text sorts correctly)
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. Hospital information: exactly ONE row
CREATE TABLE hospital_info (
    id               INTEGER PRIMARY KEY CHECK (id = 1),
    name             TEXT NOT NULL,
    address          TEXT NOT NULL,
    phone            TEXT NOT NULL,
    email            TEXT,
    emergency_number TEXT NOT NULL,
    opening_hours    TEXT,
    visiting_hours   TEXT,
    departments      TEXT,      -- comma-separated list
    facilities       TEXT,      -- comma-separated list
    what_to_bring    TEXT,
    payment_methods  TEXT
);

-- 2. Doctors
CREATE TABLE doctors (
    doctor_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name        TEXT NOT NULL,
    speciality       TEXT NOT NULL,
    consultation_fee REAL NOT NULL CHECK (consultation_fee > 0),
    room             TEXT NOT NULL,
    floor            TEXT NOT NULL,
    working_days     TEXT NOT NULL          -- e.g. 'Mon,Wed,Fri'
);

-- 3. Time slots for each doctor
CREATE TABLE slots (
    slot_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id  INTEGER NOT NULL REFERENCES doctors(doctor_id),
    slot_date  TEXT NOT NULL,               -- 'YYYY-MM-DD'
    start_time TEXT NOT NULL,               -- 'HH:MM'
    status     TEXT NOT NULL DEFAULT 'free' CHECK (status IN ('free', 'booked')),
    UNIQUE (doctor_id, slot_date, start_time)   -- no duplicate slot for a doctor
);

-- 4. Patients
CREATE TABLE patients (
    patient_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    phone         TEXT NOT NULL,
    email         TEXT,
    date_of_birth TEXT NOT NULL,            -- 'YYYY-MM-DD'
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 5. Appointments
CREATE TABLE appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id     INTEGER NOT NULL REFERENCES patients(patient_id),
    doctor_id      INTEGER NOT NULL REFERENCES doctors(doctor_id),
    slot_id        INTEGER NOT NULL REFERENCES slots(slot_id),
    reason         TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 200),
    status         TEXT NOT NULL DEFAULT 'booked' CHECK (status IN ('booked', 'cancelled')),
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Only ONE active booking per slot (a cancelled one does not block re-booking)
CREATE UNIQUE INDEX one_active_booking_per_slot
    ON appointments(slot_id) WHERE status = 'booked';

-- 6. Invoices
CREATE TABLE invoices (
    invoice_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no     TEXT NOT NULL UNIQUE,    -- 'INV-0001'
    appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(appointment_id),
    amount         REAL NOT NULL CHECK (amount > 0),
    issued_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    pdf_file       TEXT NOT NULL
);

-- Speed up the most common search: free slots of one doctor
CREATE INDEX idx_slots_doctor_status ON slots(doctor_id, status, slot_date);