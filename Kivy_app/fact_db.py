# from kivy.uix.filechooser import error
from connect_db import create_table_attandace, create_table_store_date, create_table_student_info
from connect_db import engine, base, session
from datetime import datetime

try:
    from sqlalchemy import text
    print("ok sql is imported")
except Exception as _:
    # Fallback: session.execute accepts plain SQL strings, so provide a passthrough
    def text(sql):
        return sql


# -------------------------------------------------------------------
# Helper: normalize date strings like "1_9_2025" -> "01_09_2025"
# -------------------------------------------------------------------
def normalize_dd_mm_yyyy(date_str: str):
    """
    Normalize 'D_M_YYYY' or 'DD_MM_YYYY' to 'DD_MM_YYYY'.
    Returns normalized string or None if invalid.
    """
    try:
        parts = date_str.strip().split("_")
        if len(parts) != 3:
            return None
        d = int(parts[0])
        m = int(parts[1])
        y = int(parts[2])
        return f"{d:02d}_{m:02d}_{y:04d}"
    except Exception:
        return None


# -------------------------------------------------------------------
# Helper: check if a given table actually exists in PostgreSQL
# -------------------------------------------------------------------
def table_exists(table_name: str) -> bool:
    """
    Returns True if table exists in public schema, else False.
    Prevents UndefinedTable errors.
    """
    try:
        q = text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = :tname
            );
            """
        )
        res = session.execute(q, {"tname": table_name}).scalar()
        return bool(res)
    except Exception as e:
        print(f"Error checking table {table_name} existence: {e}")
        session.rollback()
        return False


"""fatch all the student data from database"""
def fatch_all_studebent_attandance(date: str):

    # Make sure previous failed tx (if any) is cleared
    session.rollback()

    # If table doesn't exist, we can't fetch anything from it
    if not table_exists(date):
        print(f"[fatch_all_studebent_attandance] Table {date} does not exist. Skipping.")
        return False, False

    try:
        # Use quoted identifier to be safe
        att = list(
            session.execute(text(f'SELECT student_attandace FROM "{date}"')).mappings()
        )
        all_roll = list(session.execute(text("SELECT roll_number FROM student_info")))
    except Exception as e:
        print(f"Data not found or error in fatch_all_studebent_attandance: {e}")
        session.rollback()
        return False, False

    if not att:
        return False, False

    # Extract attendance per student
    p_a = []
    for row in att:
        att_dict = row.get('student_attandace', {})
        status_list = list(att_dict.values())
        p_a.append(status_list)

    # Extract roll numbers
    roll = [i[0] for i in all_roll]

    return roll, p_a


"""fatch one student data of one date"""
def fatch_one(roll_number: int, date: str):

    session.rollback()

    if not table_exists(date):
        print(f"[fatch_one] Table {date} does not exist. Skipping.")
        return False

    try:
        # safer parameter for roll_number (table name still dynamic)
        query = text(f'SELECT student_attandace FROM "{date}" WHERE student_roll = :roll_number')
        att = session.execute(query, {"roll_number": roll_number}).mappings().first()
    except Exception as e:
        print(f"Error in fatch_one: {e}")
        session.rollback()
        return False

    list_of_a_p = []
    if att:
        row = att['student_attandace']
        list_of_a_p.append(list(row.values()))
        return list_of_a_p
    else:
        return False


def fatch_month(moth: int):

    session.rollback()

    try:
        dates = session.execute(text("SELECT date FROM store_date")).mappings()
    except Exception as e:
        print(f"Error in fatch_month while fetching all month data: {e}")
        session.rollback()
        return []

    date_list = []
    for row in dates:
        date_str = row['date']  # expected like 'date24_08_2025'
        date_parts = date_str.split('_')
        if len(date_parts) >= 2:
            month_part = date_parts[1]
            if month_part.isdigit() and int(month_part) == moth:
                date_list.append(date_str)
    return date_list


def fatch_one_month_attandance(month: int):
    """
    Calculate monthly present and absent percentage based on all dynamic date tables.
    Works with your existing structure (attandace tables per day + JSON attendance per lecture).
    """

    session.rollback()

    # Fetch all table names for given month (like ['date24_11_2025', 'date25_11_2025', ...])
    date_tables = fatch_month(month) or []
    if not date_tables:
        print(f"No date tables found for month {month}")
        return False

    total_present = 0
    total_absent = 0

    for table_name in date_tables:

        # Skip dates where table is not actually present
        if not table_exists(table_name):
            print(f"[fatch_one_month_attandance] Table {table_name} does not exist. Skipping.")

            continue

        try:
            result = session.execute(
                text(f'SELECT student_attandace FROM "{table_name}";')
            ).mappings()
        except Exception as e:
            print(f"Error reading table {table_name} in fatch_one_month_attandance: {e}")
            session.rollback()
            continue

        for row in result:
            att_data = row.get("student_attandace")
            if not att_data:
                continue

            # Count 'p' and 'a' in JSON (lecture wise)
            for value in att_data.values():
                if str(value).lower() == "p":
                    total_present += 1
                elif str(value).lower() == "a":
                    total_absent += 1

    total = total_present + total_absent
    if total == 0:
        print("No attendance data found for this month.")
        return False

    present_percent = (total_present / total) * 100
    absent_percent = (total_absent / total) * 100

    print(f"\nAttendance summary for month {month}")
    print(f"Present: {present_percent:.2f}%")
    print(f"Absent : {absent_percent:.2f}%")

    return {
        "present_percent": round(present_percent, 2),
        "absent_percent": round(absent_percent, 2)
    }

def fetch_dates_between(start_date: str, end_date: str):
    """
    Fetch all date strings from store_date table between start_date and end_date.

    - In DB, 'date' column may be like:
        'date24_08_2025'  OR  '24_08_2025'
    - start_date, end_date: strings like '24_08_2025' or '1_9_2025'

    Returns:
        List of date table names as stored in DB
        e.g. ['date24_08_2025', 'date25_08_2025', ...]
    """

    # Clear any previous failed transaction (if something crashed before)
    session.rollback()

    # 1) Normalize input dates (so '1_9_2025' -> '01_09_2025')
    norm_start = normalize_dd_mm_yyyy(start_date)
    norm_end = normalize_dd_mm_yyyy(end_date)

    if not norm_start or not norm_end:
        print(f"[fetch_dates_between] Invalid start or end date format: {start_date}, {end_date}")
        return []

    try:
        start_dt = datetime.strptime(norm_start, "%d_%m_%Y")
        end_dt = datetime.strptime(norm_end, "%d_%m_%Y")
    except ValueError as e:
        print(f"[fetch_dates_between] Invalid date after normalization: {e}")
        return []

    # Optional: if user reverses dates, swap them
    if end_dt < start_dt:
        start_dt, end_dt = end_dt, start_dt

    # 2) Fetch all stored dates from DB
    try:
        rows = session.execute(text("SELECT date FROM store_date")).mappings()
    except Exception as e:
        print(f"[fetch_dates_between] Error fetching dates from DB: {e}")
        session.rollback()
        return []

    result_dates = []

    for row in rows:
        raw = row["date"]              # could be 'date24_08_2025' or '24_08_2025'

        if not isinstance(raw, str):
            continue

        # Try to extract actual DD_MM_YYYY part
        # Case 1: value starts with 'date' prefix
        if raw.startswith("date"):
            date_part = raw[4:]        # remove 'date', keep '24_08_2025'
        else:
            date_part = raw            # already like '24_08_2025'

        try:
            row_dt = datetime.strptime(date_part, "%d_%m_%Y")
        except Exception:
            # If format is wrong, just skip this row
            continue

        if start_dt <= row_dt <= end_dt:
            # We append the original string as stored in DB,
            # because that's what you use as table name.
            result_dates.append(raw)

    print(f"[fetch_dates_between] Found dates in range {start_date} -> {end_date}: {result_dates}")
    return result_dates


# def fetch_dates_between(start_date: str, end_date: str):
#     """
#     Fetch all date strings from store_date table between start_date and end_date.
#     Dates in DB are stored as 'dateDD_MM_YYYY'.

#     start_date, end_date: strings like '24_08_2025' or '1_9_2025'
#     Returns: List of date table names like ['date24_08_2025', ...]
#     """

#     # Clear any previous failed transaction
#     session.rollback()

#     try:
#         # Fetch all dates from store_date table
#         dates = session.execute(text("SELECT date FROM store_date")).mappings()
#     except Exception as e:
#         print(f"Error fetching dates from DB in fetch_dates_between: {e}")
#         session.rollback()
#         return []

#     # Normalize input dates
#     norm_start = normalize_dd_mm_yyyy(start_date)
#     norm_end = normalize_dd_mm_yyyy(end_date)

#     if not norm_start or not norm_end:
#         print(f"Invalid start or end date format: {start_date}, {end_date}")
#         return []

#     try:
#         start_dt = datetime.strptime(norm_start, "%d_%m_%Y")
#         end_dt = datetime.strptime(norm_end, "%d_%m_%Y")
#     except ValueError as e:
#         print(f"Invalid date format after normalization: {e}")
#         return []

#     date_list = []
#     for row in dates:
#         date_str = row['date']  # should be like 'date24_08_2025'
#         # Extract actual date part
#         try:
#             prefix = date_str[:4]    # 'date'
#             date_part = date_str[4:]  # '24_08_2025'
#             row_dt = datetime.strptime(date_part, "%d_%m_%Y")
#         except Exception:
#             continue

#         if start_dt <= row_dt <= end_dt:
#             date_list.append(date_str)

#     return date_list


def fetch_attendance_between(start_date: str, end_date: str):
    """
    Calculate attendance percentages for all students between two dates.

    start_date, end_date: strings like '24_08_2025' or '1_9_2025'
    Returns: Dict with present_percent and absent_percent.
    """

    # Clear any previous failed transaction
    session.rollback()

    date_tables = fetch_dates_between(start_date, end_date)

    if not date_tables:
        print(f"No date tables found in this range: {start_date} to {end_date}")
        return {"present_percent": 0.0, "absent_percent": 0.0}

    total_present = 0
    total_absent = 0

    for table_name in date_tables:

        # Check existence to avoid UndefinedTable error
        if not table_exists(table_name):
            print(f"[fetch_attendance_between] Table {table_name} does not exist. Skipping.")
            continue

        try:
            result = session.execute(
                text(f'SELECT student_attandace FROM "{table_name}";')
            ).mappings()
        except Exception as e:
            print(f"Error reading table {table_name} in fetch_attendance_between: {e}")
            session.rollback()
            continue

        for row in result:
            att_data = row.get("student_attandace")
            if not att_data:
                continue

            # Count 'p' and 'a' lecture-wise
            for status in att_data.values():
                if str(status).lower() == "p":
                    total_present += 1
                elif str(status).lower() == "a":
                    total_absent += 1

    total = total_present + total_absent
    if total == 0:
        print(f"No attendance data found between {start_date} and {end_date}.")
        return {"present_percent": 0.0, "absent_percent": 0.0}

    present_percent = (total_present / total) * 100
    absent_percent = (total_absent / total) * 100

    print(f"\nAttendance summary from {start_date} to {end_date}:")
    print(f"Present: {present_percent:.2f}%")
    print(f"Absent : {absent_percent:.2f}%")

    return {
        "present_percent": round(present_percent, 2),
        "absent_percent": round(absent_percent, 2)
    }
def fatch_roll_number():
    try:
        roll=session.execute(text("select roll_number from student_info")).mappings()
    except:
        print("error in fatching roll number")
        return
    roll_list=[]
    for row in roll:
        roll_list.append(row['roll_number'])
    return roll_list

# Example test:
# print(fetch_attendance_between("24_08_2025", "31_10_2025"))

import requests

def kivy_login(roll, password):

    # ---------------- Input Validation ---------------- #
    if not roll.strip():
        return False, "⚠ Roll number is required."

    if not password.strip():
        return False, "⚠ Password is required."

    try:
        r = requests.post("http://127.0.0.1:8000/login", data={
            "roll_number": roll,
            "password": password
        })

        # ---------------- Server Response ---------------- #
        if r.status_code == 200:
            return True, "✔ Login Successful!"

        else:
            msg = r.json().get("detail", "Login Failed")
            return False, f"❌ {msg}"

    except Exception as e:
        return False, f"⚠ Unable to connect to server: {e}"

# print(kivy_login("102","102"))