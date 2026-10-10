"""
Checks the database AND proves the safety rules work.
Run from the backend folder:  python -m scripts.check_db
"""
import sqlite3
from app.db import get_conn
from tabulate import tabulate


def show_counts():
    print("=== Row counts ===")
    with get_conn() as conn:
        for table in ["hospital_info", "doctors", "slots", "patients", "appointments", "invoices"]:
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:15} {n}")


def show_doctors():
    print("\n=== Doctors and free future slots ===")
    sql = """
        SELECT d.doctor_id, d.full_name, d.speciality, d.consultation_fee,
               SUM(CASE WHEN s.status = 'free' THEN 1 ELSE 0 END) AS free_slots,
               SUM(CASE WHEN s.status = 'booked' THEN 1 ELSE 0 END) AS booked_slots
        FROM doctors d
        JOIN slots s ON s.doctor_id = d.doctor_id
        GROUP BY d.doctor_id
        ORDER BY d.speciality, d.full_name
    """
    with get_conn() as conn:
        for r in conn.execute(sql):
            print(f"  [{r['doctor_id']}] {r['full_name']:24} {r['speciality']:17} "
                  f"LKR {r['consultation_fee']:>6.0f} | free={r['free_slots']} booked={r['booked_slots']}")


def expect_failure(title, sql, params):
    """Run SQL that SHOULD be rejected. PASS means the database protected itself."""
    try:
        with get_conn() as conn:
            conn.execute(sql, params)
        print(f"  FAIL  {title} -> database accepted bad data!")
    except sqlite3.IntegrityError as e:
        print(f"  PASS  {title} -> rejected ({e})")


def test_rules():
    print("\n=== Safety rule tests (all should PASS) ===")
    with get_conn() as conn:
        booked = conn.execute(
            "SELECT slot_id, doctor_id FROM appointments WHERE status = 'booked' LIMIT 1"
        ).fetchone()

    expect_failure("Slot for a doctor that does not exist",
                   "INSERT INTO slots (doctor_id, slot_date, start_time) VALUES (?, ?, ?)",
                   (999, "2030-01-01", "09:00"))
    expect_failure("Invalid slot status",
                   "UPDATE slots SET status = 'reserved' WHERE slot_id = ?", (1,))
    expect_failure("Double booking the same slot",
                   "INSERT INTO appointments (patient_id, doctor_id, slot_id, reason) VALUES (1, ?, ?, 'Test')",
                   (booked["doctor_id"], booked["slot_id"]))
    expect_failure("Second hospital row",
                   "INSERT INTO hospital_info (id, name, address, phone, emergency_number) VALUES (2, 'X', 'X', 'X', 'X')",
                   ())

def test1():
    print("All Cardiology doctors, cheapest first, showing name, fee and room.")


    with get_conn() as conn:

        cursor = conn.cursor()
        sql = """
            SELECT full_name ,consultation_fee ,room 
            FROM doctors 
           WHERE speciality = 'Cardiology'
            ORDER BY consultation_fee ASC"""

        cursor.execute(sql)
        results = cursor.fetchall()

        print(tabulate(
        results,
        headers=["Name", "fees", "Room"],
        tablefmt="grid"
        ))

def test2():
    print("All free, future slots for doctor 3 on one date you choose, ordered by time.")


    with get_conn() as conn:

        cursor = conn.cursor()
        sql = """
            SELECT  slot_id, slot_date,start_time,status
            FROM slots
            where doctor_id = 3 and status = 'free' and slot_date = '2026-10-08'
            ORDER BY start_time ASC"""

        cursor.execute(sql)
        results = cursor.fetchall()

        print(tabulate(
        results,
        headers=["Slot ID", "Date", "Start Time", "Status "],
        tablefmt="grid"
        ))
        
def test3():
    print("The number of booked appointments per speciality. This needs a JOIN between appointments and doctors, plus GROUP BY.")


    with get_conn() as conn:

        cursor = conn.cursor()
        sql = """
            Select d.speciality , count(*) AS booked_appointments 
            From appointments a
            join doctors d
            on a.doctor_id = d.doctor_id 
            where a.status = 'booked'
            group by d.speciality
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        print(f"results: {results} ")
    

        
  
        
if __name__ == "__main__":
    # show_counts()
    # show_doctors()
    # test_rules()
    test1()
    test2()
    test3()