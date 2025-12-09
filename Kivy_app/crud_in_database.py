from datetime import date
import json

import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import text, desc, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from connect_db import (
    create_table_attandace,
    create_table_store_date,
    create_table_student_info,
    create_table_setting,
    create_table_lacture_time,
    session,
    base,
    engine,
)

# =====================================================================
# STUDENT INFO & SETTINGS
# =====================================================================

def insert_into_student_info(roll_number: int, name: str, mobli_number: str, photo: bytes):
    """Insert new student into student_info table."""
    Student_info = create_table_student_info()
    base.metadata.create_all(bind=engine)
    student_info = Student_info(
        roll_number=roll_number,
        name=name,
        mobile_number=mobli_number,
        photo=photo,
    )
    session.add(student_info)
    session.commit()


def update_into_setting_theam(theme: str):
    """Update theme setting (create default row if not exists)."""
    Setting = create_table_setting()
    get_t = session.query(Setting).filter(Setting.id == 1)

    if get_t.count() == 0:
        base.metadata.create_all(bind=engine)
        setting = Setting(teame=theme, auto=False)
        session.add(setting)
    else:
        try:
            get_t.update({"teame": theme, "auto": False})
        except Exception as e:
            print(f"Error updating setting: {e}")

    try:
        session.commit()
    except Exception:
        print("Error in commit (update_into_setting_theam)")


def get_theme_form_setting():
    """Return current theme from setting table; create default if missing."""
    SessionLocal = sessionmaker(bind=engine)
    l_session = SessionLocal()
    try:
        Setting = create_table_setting()
        get_t = l_session.query(Setting).filter(Setting.id == 1)
        if get_t.count() == 0:
            data = Setting(teame="Light", auto=False)
            l_session.add(data)
            l_session.commit()

        re = l_session.execute(text("SELECT setting.teame FROM setting WHERE id=1;"))
        for i in re:
            return i.teame
    finally:
        l_session.close()


def update_into_setting_auto(auto: bool, n: int = 0):
    """Update auto flag and number_of_lacture."""
    Setting = create_table_setting()
    base.metadata.create_all(bind=engine)
    get_t = session.query(Setting).filter(Setting.id == 1)

    if get_t.count() == 0:
        setting = Setting(teame="Light", auto=auto, number_of_lacture=n)
        session.add(setting)
    else:
        get_t.update(
            {Setting.auto: auto, Setting.number_of_lacture: n},
            synchronize_session=False,
        )

    session.commit()


def create_row_for_lacture(n: int):
    """Create n rows in lacture_time table."""
    Lacture_time = create_table_lacture_time()
    base.metadata.create_all(bind=engine)
    session.commit()

    for i in range(1, n + 1):
        new = Lacture_time(id=i, start=text("CURRENT_TIME"), end=text("CURRENT_TIME"))
        session.add(new)
        session.commit()


# =====================================================================
# DATE & ATTENDANCE TABLE CREATION
# =====================================================================

def _today_table_name() -> str:
    return date.today().strftime("date%d_%m_%Y")


def add_to_not():
    """
    Ensure today's attendance table and store_date row exist.

    Returns:
        (AttendanceTableClass, current_date_table_name)
    """
    current_date = _today_table_name()
    Db_date = create_table_store_date()

    # Ensure metadata
    base.metadata.create_all(bind=engine)

    # 1) Ensure a row exists in store_date for today
    try:
        existing = session.query(Db_date).filter(Db_date.date == current_date).first()
    except SQLAlchemyError:
        existing = None

    if not existing:
        try:
            new_row = Db_date(date=current_date, latcure=0)
            session.add(new_row)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print("Error inserting into store_date:", e)

    # 2) Ensure today's attendance table exists
    TodayTable = create_table_attandace(current_date)
    base.metadata.create_all(bind=engine)

    # 3) Ensure all student_roll base rows exist
    Student_info = create_table_student_info()
    rolls = session.query(Student_info.roll_number).all()

    for r in rolls:
        session.execute(
            text(
                f"""
                INSERT INTO {current_date} (student_roll, student_attandace)
                VALUES (:roll, '{{}}'::jsonb)
                ON CONFLICT (student_roll) DO NOTHING;
                """
            ),
            {"roll": r[0]},
        )
    session.commit()

    return TodayTable, current_date


# =====================================================================
# LECTURE NUMBER LOGIC (based on JSON keys, not store_date.latcure)
# =====================================================================

def _get_next_lecture_number(date_table_name: str) -> int:
    """
    Look at existing JSON data in date_table_name and return next lecture number.
    Example: if max key is l_3, this returns 4.
    If table is empty or has no l_x -> returns 1.
    """
    rows = session.execute(
        text(f"SELECT student_attandace FROM {date_table_name}")
    ).fetchall()

    max_lecture = 0
    for (j,) in rows:
        if j is None:
            continue
        if isinstance(j, str):
            try:
                data = json.loads(j)
            except Exception:
                continue
        else:
            data = j

        if not isinstance(data, dict):
            continue

        for key in data.keys():
            if key.startswith("l_"):
                try:
                    num = int(key.split("_")[1])
                    if num > max_lecture:
                        max_lecture = num
                except ValueError:
                    continue

    return max_lecture + 1 if max_lecture > 0 else 1


# =====================================================================
# SAVE ATTENDANCE
# =====================================================================

def save_attandance_in_db(attendance: set):
    """
    Save attendance for students for today.
    `attendance` is a set of present student roll numbers (int or str).
    """
    try:
        # Convert to int list
        att = [int(x) for x in attendance]
        print("Attendance set (present rolls):", att)

        # All students
        Student = create_table_student_info()
        all_rolls = [r[0] for r in session.query(Student.roll_number).all()]
        print("All student rolls in DB:", all_rolls)

        # Ensure today's table exists and base rows inserted
        _, current_date = add_to_not()

        # Calculate lecture number purely from JSON data
        lecture_num = _get_next_lecture_number(current_date)
        print(f"Saving attendance for lecture number -> {lecture_num}, table {current_date}")

        # Mark present
        for roll in att:
            session.execute(
                text(
                    f"""
                    UPDATE {current_date}
                    SET student_attandace =
                        COALESCE(student_attandace::jsonb, '{{}}'::jsonb)
                        || '{{"l_{lecture_num}":"p"}}'::jsonb
                    WHERE student_roll = :roll;
                    """
                ),
                {"roll": roll},
            )

        # Mark absent (everyone else in table)
        att_table = session.execute(
            text(f"SELECT student_roll FROM {current_date}")
        ).fetchall()

        for r in att_table:
            if r[0] not in att:
                session.execute(
                    text(
                        f"""
                        UPDATE {current_date}
                        SET student_attandace =
                            COALESCE(student_attandace::jsonb, '{{}}'::jsonb)
                            || '{{"l_{lecture_num}":"a"}}'::jsonb
                        WHERE student_roll = :roll;
                        """
                    ),
                    {"roll": r[0]},
                )

        session.commit()
        print(f"Attendance saved for lecture {lecture_num} on {current_date}")

    except Exception as e:
        session.rollback()
        print("Error saving attendance:", e)


# =====================================================================
# DEBUG & HEATMAP
# =====================================================================

def debug_print_attendance_table(date_table_name: str):
    """Print raw DB content for a given date table (for checking)."""
    rows = session.execute(
        text(
            f"""
            SELECT student_roll, student_attandace
            FROM {date_table_name}
            ORDER BY student_roll
            """
        )
    ).fetchall()

    print(f"--- Attendance table: {date_table_name} ---")
    for r in rows:
        print(r[0], "=>", r[1])


def plot_all_student_heatmap(date_table_name: str):
    """
    Build and show a heatmap for all students for a given date table.
    Roll numbers ALWAYS match their correct row.
    """
    rows = session.execute(
        text(
            f"""
            SELECT student_roll, student_attandace
            FROM {date_table_name}
            ORDER BY student_roll
            """
        )
    ).fetchall()

    if not rows:
        print("No data found for", date_table_name)
        return None

    # Same order for labels and data
    rolls = [r[0] for r in rows]
    json_list = []
    for _, j in rows:
        if isinstance(j, str):
            try:
                json_list.append(json.loads(j))
            except Exception:
                json_list.append({})
        else:
            json_list.append(j or {})

    # How many lectures exist?
    max_lecture = 0
    for j in json_list:
        if not isinstance(j, dict):
            continue
        for k in j.keys():
            if k.startswith("l_"):
                try:
                    num = int(k.split("_")[1])
                    max_lecture = max(max_lecture, num)
                except ValueError:
                    pass

    if max_lecture == 0:
        print("No lecture data yet for", date_table_name)
        return None

    # Build matrix: rows = students, cols = l_1 ... l_n
    data = []
    for j in json_list:
        row_vals = []
        for lec in range(1, max_lecture + 1):
            key = f"l_{lec}"
            val = j.get(key)
            row_vals.append(1 if val == "p" else 0)
        data.append(row_vals)

    data = np.array(data)

    fig, ax = plt.subplots()
    im = ax.imshow(data, aspect="auto")

    ax.set_xticks(range(max_lecture))
    ax.set_xticklabels([f"Lec {i}" for i in range(1, max_lecture + 1)])

    ax.set_yticks(range(len(rolls)))
    ax.set_yticklabels(rolls)

    ax.set_xlabel("Lectures")
    ax.set_ylabel("Roll Numbers")
    ax.set_title(f"All Student Attendance Heatmap ({date_table_name})")

    # numbers inside cells
    for i in range(len(rolls)):
        for j in range(max_lecture):
            ax.text(j, i, str(data[i, j]), ha="center", va="center", color="white")

    plt.tight_layout()
    plt.show()
    return fig


# =====================================================================
# TABLE CHECK
# =====================================================================

def check_table():
    """Ensure all base tables exist."""
    Inspector = inspect(engine)
    list_of_lable = Inspector.get_table_names()
    flag = True

    if "lacture_time" not in list_of_lable:
        create_table_lacture_time()
        base.metadata.create_all(engine)
        flag = False

    if "store_date" not in list_of_lable:
        create_table_store_date()
        base.metadata.create_all(engine)
        flag = False

    if "setting" not in list_of_lable:
        create_table_setting()
        base.metadata.create_all(engine)
        flag = False

    if "student_info" not in list_of_lable:
        create_table_student_info()
        base.metadata.create_all(engine)
        flag = False

    if flag:
        print("Table check successful: all tables available")
    else:
        print("Some tables were missing and are now created")


# =====================================================================

if __name__ == "__main__":
    print("Helper module loaded.")
    # Example manual checks:
    # today = _today_table_name()
    # debug_print_attendance_table(today)
    # plot_all_student_heatmap(today)
