from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
import json
from sqlalchemy import text
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


import os

app = FastAPI()

DATABASE_URL = "postgresql+psycopg2://postgres:Hemang812@127.0.0.1:5432/attandance_app"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class LeaveReport(Base):
    __tablename__ = "leave_reports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    roll = Column(String(50))
    from_date = Column(Date)
    to_date = Column(Date)
    reason = Column(Text)
    signature = Column(Text)  # Base64 image

Base.metadata.create_all(bind=engine)

class LeaveReportSchema(BaseModel):
    name: str
    roll: str
    from_date: date
    to_date: date
    reason: str
    signature: str


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or ["http://localhost:5500"] if serving HTML locally
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/leave-report")
def submit_leave_report(report: LeaveReportSchema):
    db = SessionLocal()
    try:
        new_report = LeaveReport(
            name=report.name,
            roll=report.roll,
            from_date=report.from_date,
            to_date=report.to_date,
            reason=report.reason,
            signature=report.signature
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        return {"message": "Leave report submitted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

from sqlalchemy import and_
from datetime import date

# Existing imports and setup...

@app.get("/absent-without-leave")
def get_absent_without_leave(selected_date: date):
    db = SessionLocal()
    try:
        # 1. Get all absent students on selected date
        absent_students = db.execute(
            """
            SELECT s.id, s.name, s.roll
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = :selected_date AND a.status = 'Absent'
            """,
            {"selected_date": selected_date}
        ).fetchall()

        result = []
        for student in absent_students:
            # 2. Check if leave report exists for this student & date
            leave_exists = db.query(LeaveReport).filter(
                LeaveReport.roll == student.roll,
                and_(
                    LeaveReport.from_date <= selected_date,
                    LeaveReport.to_date >= selected_date
                )
            ).first()

            if not leave_exists:
                result.append({
                    "roll": student.roll,
                    "name": student.name
                })

        return {"date": selected_date, "students": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/material-list.json")
def get_material_list():
    """Serve the material-list.json file"""
    try:
        # Get the directory where this file is located (Frontend folder)
        current_dir = os.path.dirname(os.path.abspath(__file__)) #abspath(__file__) used store full path and path.dirname used to store folder in which file is
        json_path = os.path.join(current_dir, "material-list.json") 
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return JSONResponse(content=data)
        else:
            # Return default structure if file doesn't exist
            default_data = {
                "BCA": {
                    "1st": {
                        "Python Programming": ["1.txt", "Unit2.pdf", "FullNotes.pdf"],
                        "Web Development": ["HTML.pdf", "CSS.pdf"]
                    },
                    "2nd": {
                        "Database Management": ["DBMS Unit1.pdf"]
                    }
                },
                "BScIT": {
                    "1st": {
                        "Artificial Intelligence": ["AI Notes.pdf"]
                    }
                },
                "MCA": {
                    "1st": {
                        "Advanced Programming": ["Notes.pdf"]
                    }
                }
            }
            return JSONResponse(content=default_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading material list: {str(e)}")

from datetime import datetime, timedelta
import json

from datetime import datetime, timedelta

@app.get("/student/absent_without_leave")
def absent_without_leave(roll: int):
    conn = engine.raw_connection()
    cursor = conn.cursor()

    # 1️⃣ Get all date tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'date%'")
    date_tables = [row[0] for row in cursor.fetchall()]

    leave_required_dates = set()

    # 2️⃣ Read attendance from each date table
    for table in date_tables:
        cursor.execute(f"SELECT student_attandace FROM {table} WHERE student_roll = %s", (roll,))
        row = cursor.fetchone()
        if not row:
            continue

        att = row[0]        # JSON already dict -> DO NOT json.loads
        lectures = [att.get(f"L_{i}", 'a') for i in range(1, 6)]  # L1–L5 only

        # If ANY lecture is absent, leave is required
        if "a" in lectures:
            leave_required_dates.add(table.replace("date", ""))  # convert table name to dd_mm_yyyy

    # 3️⃣ Get leave date ranges
    cursor.execute("SELECT from_date, to_date FROM leave_reports WHERE roll = %s", (str(roll),))
    leave_ranges = cursor.fetchall()

    cursor.close()
    conn.close()

    # 4️⃣ Expand leave ranges into individual dates
    leave_dates = set()
    for f, t in leave_ranges:
        d1 = datetime.strptime(str(f), "%Y-%m-%d")
        d2 = datetime.strptime(str(t), "%Y-%m-%d")
        while d1 <= d2:
            leave_dates.add(d1.strftime("%d_%m_%Y"))
            d1 += timedelta(days=1)

    # 5️⃣ Final pending leave report dates
    final_missing = sorted(list(leave_required_dates - leave_dates))

    return {"dates": final_missing}

@app.get("/review")
def review_page():
    html_path = os.path.join(os.path.dirname(__file__), "review.html")
    if not os.path.exists(html_path):
        raise HTTPException(404, "review.html not found")
    return FileResponse(html_path)


# Utility: safe function to load JSON from DB column (handles str or already-parsed)
def parse_attendance_column(value) -> Dict[str, Any]:
    """
    value may be:
      - dict (already parsed by driver)
      - str like '{"L_2":"a", ...}'
      - None
    Returns Python dict.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            # fallback: try single quotes -> replace
            try:
                return json.loads(value.replace("'", '"'))
            except Exception:
                return {}
    # unknown type
    return {}


# API: fetch attendance for date-table and lecture
@app.get("/get_attendance/{table}/{lecture}")
def get_attendance(table: str, lecture: str):
    lec_key = f"l_{lecture}"
    # Basic SQL safety: allow only expected table name pattern
    if not table.startswith("date"):
        raise HTTPException(status_code=400, detail="Invalid table name")

    try:
        with engine.connect() as conn:
            q = text(f"SELECT student_roll, student_attandace FROM {table} ORDER BY student_roll")
            rows = conn.execute(q).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error (reading): {e}")

    result = []
    for row in rows:
        roll = row[0]
        att_raw = row[1]
        att = parse_attendance_column(att_raw)
        raw_val = att.get(lec_key, "a")  # default absent if missing
        status = "Present" if str(raw_val) == "p" else "Absent"
        result.append({"roll": roll, "status": status})

    return result


# API: submit attendance (updates entire student_attandace JSON column for rows provided)
@app.post("/submit_attendance")
def submit_attendance(payload: Dict):
    """
    payload expected:
    {
      "table": "date01_12_2025",
      "lecture": "2",
      "records": [ {"roll": 12, "status": "Present"}, ... ]
    }
    """
    table = payload.get("table")
    lecture = payload.get("lecture")
    records = payload.get("records")

    if not table or not lecture or not isinstance(records, list):
        raise HTTPException(status_code=400, detail="Invalid payload")

    if not table.startswith("date"):
        raise HTTPException(status_code=400, detail="Invalid table name")

    lec_key = f"l_{lecture}"

    try:
        with engine.begin() as conn:
            # For each record: load row, update Python dict, write back JSON string
            for rec in records:
                roll = rec.get("roll")
                status = rec.get("status")
                if roll is None or status not in ("Present", "Absent"):
                    continue

                # Read existing JSON column
                sel = text(f"SELECT student_attandace FROM {table} WHERE student_roll = :roll FOR UPDATE")
                row = conn.execute(sel, {"roll": roll}).fetchone()
                if not row:
                    # optionally: skip or insert; here we skip (no such roll)
                    continue

                att_raw = row[0]
                att = parse_attendance_column(att_raw)

                # Set lecture key
                att[lec_key] = "p" if status == "Present" else "a"

                # Convert back to JSON string
                new_json_str = json.dumps(att)

                # Update row: set to JSON string (works for json or text columns)
                upd = text(f"""
                    UPDATE {table}
                    SET student_attandace = :new_json
                    WHERE student_roll = :roll
                """)
                conn.execute(upd, {"new_json": new_json_str, "roll": roll})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error (writing): {e}")

    return {"message": "Attendance updated successfully"}


# Small health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}