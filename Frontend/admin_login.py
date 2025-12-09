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
class Admin(Base):
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

def create_users_table() -> bool:
    sql_stmt = """
    CREATE TABLE IF NOT EXISTS admins (
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
        cur.execute("SELECT id FROM admins WHERE roll_number = %s", (roll_number,))
        existing_user = cur.fetchone()
        
        if existing_user:
            cur.close()
            conn.close()
            raise HTTPException(status_code=400, detail="User with this roll number already exists")
        
        # Hash password and create user
        hashed_pw = hash_password(password)
        cur.execute(
            "INSERT INTO admins (name, roll_number, password) VALUES (%s, %s, %s)",
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
        cur.execute("SELECT id, name, roll_number, password FROM admins WHERE roll_number = %s", (roll_number,))
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
