import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoints"""
    
    print("Testing Smart Attendance System API...")
    print("=" * 50)
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test signup
    try:
        signup_data = {
            "name": "Test User",
            "roll_number": "TEST001",
            "password": "testpassword123"
        }
        response = requests.post(f"{BASE_URL}/signup", data=signup_data)
        print(f"✅ Signup: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Signup failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test login
    try:
        login_data = {
            "roll_number": "TEST001",
            "password": "testpassword123"
        }
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        print(f"✅ Login: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Login failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test add student
    try:
        student_data = {
            "name": "John Doe",
            "roll_number": "STU001",
            "mobile_number": "1234567890"
        }
        response = requests.post(f"{BASE_URL}/add_student", data=student_data)
        print(f"✅ Add Student: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Add Student failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test mark attendance
    try:
        attendance_data = {
            "roll_number": "STU001",
            "status": "present"
        }
        response = requests.post(f"{BASE_URL}/mark_attendance", data=attendance_data)
        print(f"✅ Mark Attendance: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Mark Attendance failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test get attendance
    try:
        response = requests.get(f"{BASE_URL}/attendance?roll_number=STU001")
        print(f"✅ Get Attendance: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Get Attendance failed: {e}")
    
    print("\n" + "=" * 50)
    
    # Test get all students
    try:
        response = requests.get(f"{BASE_URL}/students")
        print(f"✅ Get All Students: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Get All Students failed: {e}")
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    test_api() 