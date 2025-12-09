from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import datetime
import json
import re
import subprocess
import socket
import sys
import os
import time

app = FastAPI()

# Database connection
DATABASE_URL = "postgresql+psycopg2://postgres:Hemang812@127.0.0.1:5432/attandance_app"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User model for signup data - without created_at to avoid column issues
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_number = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

# Don't create tables automatically - we'll handle this manually
# Base.metadata.create_all(bind=engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if TCP port is open on host."""
    try:
        with socket.create_connection((host, port), timeout=0.8):
            return True
    except Exception:
        return False


def start_frontend_if_needed(port: int = 8000):
    """Start the Frontend uvicorn server in a detached process if it's not already running.

    This is intended for development convenience only.
    """
    if is_port_open(port):
        # already running
        return

    # path to repository root (parent of this backend folder)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Build command: python -m uvicorn Frontend.main:app --app-dir Frontend --host 127.0.0.1 --port <port>
    cmd = [sys.executable, "-m", "uvicorn", "Frontend.main:app", "--app-dir", "Frontend", "--host", "127.0.0.1", "--port", str(port)]

    try:
        if os.name == 'nt':
            # Detached on Windows
            CREATE_NO_WINDOW = 0x08000000
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008
            creationflags = CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_NO_WINDOW
            subprocess.Popen(cmd, cwd=repo_root, creationflags=creationflags)
        else:
            # POSIX: start new session so it doesn't die with the caller
            subprocess.Popen(cmd, cwd=repo_root, start_new_session=True)
        # give the server a moment to start
        time.sleep(0.5)
    except Exception:
        # don't raise here; starting servers is a best-effort convenience
        pass

def create_users_table() -> bool:
    sql_stmt = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        roll_number VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    """
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        cur.execute(sql_stmt)
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception:
        return False

def create_daily_attendance_table(date_str: str) -> bool:
    table_name = f"date{date_str}"
    sql_stmt = f"""
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        roll_number VARCHAR(50) PRIMARY KEY,
        status VARCHAR(20) DEFAULT 'absent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        cur.execute(sql_stmt)
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception:
        return False

def aggregate_lecture_status(lecture_map: dict) -> str:
    """Aggregate a per-lecture map (L_1..L_6) to present/partial/absent.
    present => all six are 'p'
    partial => at least one 'p' and at least one 'a'
    absent  => all are 'a' (or map empty)
    Any other value counts as 'a'.
    """
    if not lecture_map:
        return "absent"
    values = []
    for i in range(1, 7):
        key = f"L_{i}"
        v = str(lecture_map.get(key, 'a')).lower()
        if v in ["p", "present", "1", "true", "yes", "y"]:
            values.append('p')
        else:
            values.append('a')
    if all(v == 'p' for v in values):
        return "present"
    if any(v == 'p' for v in values) and any(v == 'a' for v in values):
        return "partial"
    return "absent"

def normalize_lecture_map(value) -> dict:
    """Coerce various stored forms into a map with keys L_1..L_6.
    Accepts:
    - dict already (keys like L_1, L1, 1, '1')
    - JSON strings (even with single quotes)
    Returns a dict with string keys L_1..L_6.
    """
    if value is None:
        return {}
    obj = value
    if isinstance(value, str):
        s = value.strip()
        # try standard JSON
        try:
            obj = json.loads(s)
        except Exception:
            # try converting single quotes to double and adding quotes to unquoted keys like L_1
            s2 = s.replace("'", '"')
            try:
                obj = json.loads(s2)
            except Exception:
                return {}
    if not isinstance(obj, dict):
        return {}
    result = {}
    for i in range(1, 7):
        candidates = [f"L_{i}", f"l_{i}", f"L{i}", f"l{i}", str(i)]
        val = None
        for k in candidates:
            if k in obj:
                val = obj[k]
                break
        result[f"L_{i}"] = val if val is not None else 'a'
    return result

def detect_roll_col(cur, table_name: str) -> str:
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s
        """,
        (table_name,)
    )
    cols = [r['column_name'] for r in cur.fetchall()]
    candidate_cols = [
        'roll_number','rollno','roll','student_roll','student_id','sid','enrollment','enroll','rollnumber'
    ]
    for c in candidate_cols:
        if c in cols:
            return c
    for c in cols:
        if c not in ['status','created_at']:
            return c
    raise HTTPException(status_code=500, detail="Could not identify roll number column")

@app.get("/")
def read_root():
    return {"message": "Smart Attendance System API is running!"}

# Signup route - stores data in users table
@app.post("/signup")
def signup(name: str = Form(...), roll_number: str = Form(...), password: str = Form(...)):
    # Create users table if it doesn't exist
    if not create_users_table():
        raise HTTPException(status_code=500, detail="Failed to create users table")
    
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE roll_number = %s", (roll_number,))
        existing_user = cur.fetchone()
        
        if existing_user:
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="User with this roll number already exists")
        
        # Hash password and create user
        hashed_pw = hash_password(password)
        cur.execute(
            "INSERT INTO users (name, roll_number, password) VALUES (%s, %s, %s)",
            (name, roll_number, hashed_pw)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# Login route - checks users table
@app.post("/login")
def login(roll_number: str = Form(...), password: str = Form(...)):
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        
        # Get user by roll number
        cur.execute("SELECT id, name, roll_number, password FROM users WHERE roll_number = %s", (roll_number,))
        user_data = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user_data or not verify_password(password, user_data[3]):  # password is at index 3
            raise HTTPException(status_code=401, detail="Invalid roll number or password")
        
        return {
            "message": "Login successful", 
            "user": {
                "name": user_data[1],  # name is at index 1
                "roll_number": user_data[2]  # roll_number is at index 2
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

# Mark attendance - creates date table and marks present/absent
@app.post("/mark_attendance")
def mark_attendance(roll_number: str = Form(...), status: str = Form(...)):
    today = datetime.datetime.now().strftime("%d_%m_%Y")
    table_name = f"date{today}"
    
    # Create table if it doesn't exist
    if not create_daily_attendance_table(today):
        raise HTTPException(status_code=500, detail="Failed to create attendance table")
    
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        
        # Normalize incoming status
        normalized = status.lower()
        if normalized in ["p", "present", "1", "yes", "y", "true"]:
            normalized = "present"
        elif normalized in ["a", "absent", "0", "no", "n", "false"]:
            normalized = "absent"
        else:
            normalized = "absent"
        
        # Use ON CONFLICT for upsert
        upsert_sql = f'''
        INSERT INTO "{table_name}" (roll_number, status, created_at)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (roll_number) 
        DO UPDATE SET 
            status = EXCLUDED.status,
            created_at = CURRENT_TIMESTAMP
        '''
        
        cur.execute(upsert_sql, (roll_number, normalized))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"message": "Attendance marked successfully", "date": today, "status": normalized}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking attendance: {str(e)}")

# Get attendance - checks date table for present/absent/partial
@app.get("/attendance")
def get_attendance(
    roll_number: str = Query(..., description="Student roll number"),
    date: str = Query(None, description="Date in format DD_MM_YYYY (optional, defaults to today)")
):
    if date:
        table_name = f"date{date}"
    else:
        table_name = f"date{datetime.datetime.now().strftime('%d_%m_%Y')}"
    
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
            """,
            (table_name,)
        )
        table_exists = cur.fetchone()['exists']
        if not table_exists:
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail="Attendance table not found for this date")

        rn_col = detect_roll_col(cur, table_name)
        cur.execute(sql.SQL('SELECT * FROM {} WHERE {} = %s').format(
            sql.Identifier(table_name), sql.Identifier(rn_col)
        ), (roll_number,))
        record = cur.fetchone()
        cur.close(); conn.close()
        if not record:
            raise HTTPException(status_code=404, detail="Attendance not found for this student on this date")

        normalized_status = None
        if 'status' in record and record['status'] is not None:
            val = str(record['status']).lower()
            if val in ["p", "present", "1", "yes", "y", "true"]:
                normalized_status = "present"
            elif val in ["a", "absent", "0", "no", "n", "false"]:
                normalized_status = "absent"

        lecture_map = None
        if not normalized_status:
            for key, value in record.items():
                if key == rn_col or value is None:
                    continue
                norm_map = normalize_lecture_map(value)
                if norm_map:
                    lecture_map = norm_map
                    normalized_status = aggregate_lecture_status(norm_map)
                    break
            if not normalized_status:
                normalized_status = "absent"

        attendance_info = {
            "roll_number": record.get(rn_col, roll_number),
            "status": normalized_status,
            "date": date or datetime.datetime.now().strftime('%d_%m_%Y'),
            "lectures": lecture_map or {}
        }
        return {"status": "success", "attendance": attendance_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attendance: {str(e)}")

# Admin: get all students' attendance for a date
@app.get("/admin/attendance_by_date")
def admin_attendance_by_date(
    date: str = Query(..., description="Date in format DD_MM_YYYY")
):
    table_name = f"date{date}"
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
            """,
            (table_name,)
        )
        if not cur.fetchone()['exists']:
            cur.close(); conn.close()
            return {"date": date, "students": []}

        rn_col = detect_roll_col(cur, table_name)
        cur.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(table_name)))
        rows = cur.fetchall()
        cur.close(); conn.close()

        result = []
        for row in rows:
            status = None
            lecture_map = None
            if 'status' in row and row['status'] is not None:
                val = str(row['status']).lower()
                if val in ["p", "present", "1", "yes", "y", "true"]:
                    status = "present"
                elif val in ["a", "absent", "0", "no", "n", "false"]:
                    status = "absent"
            if not status:
                for key, value in row.items():
                    if key == rn_col or value is None:
                        continue
                    norm_map = normalize_lecture_map(value)
                    if norm_map:
                        lecture_map = norm_map
                        status = aggregate_lecture_status(norm_map)
                        break
                if not status:
                    status = "absent"
            result.append({
                "roll_number": row.get(rn_col),
                "status": status,
                "lectures": lecture_map or {}
            })
        return {"date": date, "students": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admin attendance: {str(e)}")

# Get all users
@app.get("/users")
def get_users():
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, roll_number FROM users")
        users_data = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "users": [
                {
                    "id": user[0],
                    "name": user[1],
                    "roll_number": user[2]
                }
                for user in users_data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

# Settings and holidays endpoints
@app.post("/admin/settings/total_days")
def set_total_days(total_days: int = Form(...)):
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key VARCHAR(100) PRIMARY KEY,
                value VARCHAR(100)
            );
            """
        )
        cur.execute(
            """
            INSERT INTO settings (key, value) VALUES ('total_semester_days', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (str(total_days),)
        )
        conn.commit(); cur.close(); conn.close()
        return {"message": "Total days saved", "total_days": total_days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save total days: {str(e)}")

@app.get("/admin/settings/total_days")
def get_total_days():
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS settings (key VARCHAR(100) PRIMARY KEY, value VARCHAR(100));")
        cur.execute("SELECT value FROM settings WHERE key='total_semester_days'")
        row = cur.fetchone(); cur.close(); conn.close()
        return {"total_days": int(row[0]) if row and row[0] is not None else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load total days: {str(e)}")

@app.post("/admin/holidays/add")
def add_holiday(date: str = Form(...)):
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS holidays (
                date_key VARCHAR(20) PRIMARY KEY
            );
            """
        )
        cur.execute(
            "INSERT INTO holidays (date_key) VALUES (%s) ON CONFLICT (date_key) DO NOTHING",
            (date,)
        )
        conn.commit(); cur.close(); conn.close()
        return {"message": "Holiday added", "date": date}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add holiday: {str(e)}")

@app.post("/admin/holidays/remove")
def remove_holiday(date: str = Form(...)):
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS holidays (date_key VARCHAR(20) PRIMARY KEY);")
        cur.execute("DELETE FROM holidays WHERE date_key=%s", (date,))
        conn.commit(); cur.close(); conn.close()
        return {"message": "Holiday removed", "date": date}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove holiday: {str(e)}")

@app.get("/admin/holidays")
def list_holidays():
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS holidays (date_key VARCHAR(20) PRIMARY KEY);")
        cur.execute("SELECT date_key FROM holidays ORDER BY date_key")
        rows = cur.fetchall(); cur.close(); conn.close()
        return {"holidays": [r[0] for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list holidays: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5432)