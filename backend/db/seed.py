"""
Creates a FRESH celia.db with dummy data.
Run from the backend folder:  python -m db.seed
Warning: this DELETES the old database each time (fine for development).
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent      # -> backend/
DB_PATH = BASE_DIR / "data" / "celia.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SLOT_TIMES = ["09:00", "09:30", "10:00", "10:30", "11:00"]
DAYS_AHEAD = 14

HOSPITAL = {
    "name": "Lotus Care Hospital",
    "address": "No. 25, Lake Road, Colombo 05",
    "phone": "011 234 5678",
    "email": "frontdesk@lotuscare.example",
    "emergency_number": "011 234 9999",
    "opening_hours": "OPD: Mon-Sat 8:00 AM - 8:00 PM, Sun 8:00 AM - 1:00 PM",
    "visiting_hours": "Daily 12:00 PM - 1:00 PM and 5:00 PM - 7:00 PM",
    "departments": "Cardiology, Dermatology, Paediatrics, General Medicine, ENT",
    "facilities": "24/7 Emergency, Pharmacy, Laboratory, X-ray and Scan, Parking, Cafeteria",
    "what_to_bring": "National ID or passport, previous medical reports, current medicine list",
    "payment_methods": "Cash, Credit/Debit card, Bank transfer",
}

# (full_name, speciality, fee_lkr, room, floor, working_days)
DOCTORS = [
    ("Dr. Nimal Perera",      "Cardiology",       4500, "201", "2nd Floor",    "Mon,Wed,Fri"),
    ("Dr. Ayesha Fernando",   "Cardiology",       4800, "203", "2nd Floor",    "Tue,Thu,Sat"),
    ("Dr. Sarah Adams",       "Dermatology",      3000, "105", "1st Floor",    "Mon,Tue,Thu"),
    ("Dr. Kasun Silva",       "Paediatrics",      2500, "110", "1st Floor",    "Mon,Wed,Fri,Sat"),
    ("Dr. Dilani Jayawardena","General Medicine", 2000, "G12", "Ground Floor", "Mon,Tue,Wed,Thu,Fri"),
    ("Dr. Malini de Silva",   "General Medicine", 2000, "G14", "Ground Floor", "Sat,Sun"),
    ("Dr. Ravi Gunasekara",   "ENT",              3500, "305", "3rd Floor",    "Tue,Thu"),
]


def create_database(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)   # create folder if missing
    if db_path.exists():
        db_path.unlink()                                 # delete old database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def insert_hospital(conn):
    columns = ", ".join(HOSPITAL.keys())
    placeholders = ", ".join("?" for _ in HOSPITAL)
    conn.execute(
        f"INSERT INTO hospital_info (id, {columns}) VALUES (1, {placeholders})",
        tuple(HOSPITAL.values()),
    )


def insert_doctors(conn):
    conn.executemany(
        """INSERT INTO doctors (full_name, speciality, consultation_fee, room, floor, working_days)
           VALUES (?, ?, ?, ?, ?, ?)""",
        DOCTORS,
    )


def insert_slots(conn):
    """Create slots for the next 14 days, only on each doctor's working days."""
    today = date.today()
    doctors = conn.execute("SELECT doctor_id, working_days FROM doctors").fetchall()
    rows = []
    for doctor_id, working_days in doctors:
        days = working_days.split(",")
        for offset in range(1, DAYS_AHEAD + 1):          # start TOMORROW -> always future
            day = today + timedelta(days=offset)
            if WEEKDAYS[day.weekday()] in days:
                for t in SLOT_TIMES:
                    rows.append((doctor_id, day.isoformat(), t))
    conn.executemany(
        "INSERT INTO slots (doctor_id, slot_date, start_time) VALUES (?, ?, ?)", rows
    )


def insert_existing_bookings(conn):
    """Book the FIRST slot of each doctor for a demo patient.
    Purpose: prove in the demo that booked slots are never offered (FR4)."""
    cur = conn.execute(
        """INSERT INTO patients (full_name, phone, email, date_of_birth)
           VALUES ('Demo Patient', '0770000000', NULL, '1985-06-15')"""
    )
    patient_id = cur.lastrowid
    first_slots = conn.execute(
        """SELECT doctor_id, MIN(slot_id) FROM slots GROUP BY doctor_id"""
    ).fetchall()
    for doctor_id, slot_id in first_slots:
        conn.execute("UPDATE slots SET status = 'booked' WHERE slot_id = ?", (slot_id,))
        conn.execute(
            """INSERT INTO appointments (patient_id, doctor_id, slot_id, reason)
               VALUES (?, ?, ?, 'Follow-up visit')""",
            (patient_id, doctor_id, slot_id),
        )


def main(db_path: Path = DB_PATH):
    conn = create_database(db_path)
    try:
        insert_hospital(conn)
        insert_doctors(conn)
        insert_slots(conn)
        insert_existing_bookings(conn)
        conn.commit()
    finally:
        conn.close()
    print(f"Database created: {db_path}")


if __name__ == "__main__":
    main()