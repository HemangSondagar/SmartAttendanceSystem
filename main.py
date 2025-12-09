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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_users_table():
    """Create users table if it doesn't exist"""
    create_table_sql = """
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
        cur.execute(create_table_sql)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating users table: {e}")
        return False

def create_daily_attendance_table(date_str: str):
    """Create daily attendance table if it doesn't exist"""
    table_name = f"date{date_str}"
    create_table_sql = f"""
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
        cur.execute(create_table_sql)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return False

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

# Get attendance - checks date table for present/absent
@app.get("/attendance")
def get_attendance(
    roll_number: str = Query(..., description="Student roll number"),
    date: str = Query(None, description="Date in format DD_MM_YYYY (optional, defaults to today)")
):
    """Fetch attendance for a student from date table"""
    if date:
        table_name = f"date{date}"
    else:
        table_name = f"date{datetime.datetime.now().strftime('%d_%m_%Y')}"
    
    try:
        conn = psycopg2.connect(
            "dbname=attandance_app user=postgres password=Hemang812 host=127.0.0.1 port=5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (table_name,))
        
        table_exists = cur.fetchone()['exists']
        
        if not table_exists:
            cur.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Attendance table not found for this date")
        
        # Find the roll number column dynamically
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
        rn_col = None
        for c in candidate_cols:
            if c in cols:
                rn_col = c
                break
        if rn_col is None:
            # fallback: first text-like column excluding obvious non-id columns
            for c in cols:
                if c not in ['status','created_at']:
                    rn_col = c
                    break
        if rn_col is None:
            raise HTTPException(status_code=500, detail="Could not identify roll number column")
        
        # Fetch attendance for this student
        cur.execute(sql.SQL('SELECT * FROM {} WHERE {} = %s').format(
            sql.Identifier(table_name), sql.Identifier(rn_col)
        ), (roll_number,))
        record = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not record:
            raise HTTPException(status_code=404, detail="Attendance not found for this student on this date")
        
        # Normalize different schemas → present/absent
        normalized_status = None
        if 'status' in record and record['status'] is not None:
            val = str(record['status']).lower()
            if val in ["p", "present", "1", "yes", "y", "true"]:
                normalized_status = "present"
            elif val in ["a", "absent", "0", "no", "n", "false"]:
                normalized_status = "absent"
        
        if not normalized_status:
            for key, value in record.items():
                if key == rn_col or value is None:
                    continue
                try:
                    obj = json.loads(value) if isinstance(value, str) else value
                except Exception:
                    continue
                if isinstance(obj, dict):
                    lecture_vals = [str(v).lower() for v in obj.values()]
                    if any(v in ["p", "present", "1", "true", "yes", "y"] for v in lecture_vals):
                        normalized_status = "present"
                        break
                    if all(v in ["a", "absent", "0", "false", "no", "n"] for v in lecture_vals):
                        normalized_status = "absent"
                        break
            if not normalized_status:
                normalized_status = "absent"
        
        attendance_info = {
            "roll_number": record.get(rn_col, roll_number),
            "status": normalized_status,
            "date": date or datetime.datetime.now().strftime('%d_%m_%Y')
        }
        
        return {"status": "success", "attendance": attendance_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attendance: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)