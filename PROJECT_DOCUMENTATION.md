# Smart Attendance System - Project Documentation

## 📋 Project Title
**Smart Attendance System with Facial Recognition**

---

## 📝 Project Description

The Smart Attendance System is an automated attendance management application that uses facial recognition technology to mark student attendance in real-time. The system eliminates manual attendance taking, reduces errors, and provides comprehensive analytics through interactive graphs and visualizations.

### Key Features:
- **Facial Recognition Attendance**: Automated attendance marking using DeepFace AI model
- **Student Registration**: Register students with photos captured via webcam
- **Real-time Camera Feed**: Live video feed with face detection and recognition
- **Attendance Analytics**: 
  - Individual student monthly attendance graphs (bar charts)
  - All students monthly attendance heatmaps
  - Daily attendance tracking per lecture
- **Database Management**: PostgreSQL database with dynamic table creation per date
- **Modern UI**: Material Design 3 interface built with KivyMD
- **Settings Management**: Theme switching (Light/Dark), auto-attendance scheduling
- **Multi-lecture Support**: Track attendance across multiple lectures per day

### Workflow:
1. **Registration**: Admin captures student photos and registers them with roll number and contact details
2. **Attendance Marking**: System uses webcam to detect faces and match them against registered students
3. **Data Storage**: Attendance is stored in PostgreSQL with date-based table organization
4. **Analytics**: Generate visual reports for individual students or entire class for any month

---

## 🛠️ Complete Technology Stack & Tools List

### **Programming Languages**
- **Python 3.11** - Primary programming language

### **GUI Framework**
- **Kivy** - Cross-platform Python framework for GUI development
- **KivyMD** - Material Design components for Kivy
  - Material Design 3 (M3) styling
  - MDNavigationLayout, MDScreen, MDTopAppBar
  - MDTextField, MDRaisedButton, MDSwitch
  - MDCard, MDLabel, MDNavigationDrawer
  - Toast notifications

### **Computer Vision & AI**
- **OpenCV (cv2)** - Computer vision library
  - Video capture and processing
  - Image manipulation (flip, resize, color conversion)
  - Frame processing and texture creation
- **DeepFace** - Facial recognition library
  - Face detection using OpenCV backend
  - Face recognition using SFace model
  - Face alignment and normalization
  - Database-based face matching

### **Database & ORM**
- **PostgreSQL** - Relational database management system
- **SQLAlchemy** - Python SQL toolkit and Object-Relational Mapping (ORM)
  - `create_engine` - Database connection management
  - `declarative_base` - Base class for models
  - `sessionmaker` - Session management
  - `Column`, `Integer`, `String`, `LargeBinary`, `JSON`, `Boolean`, `Time`, `Date` - Data types
  - `ForeignKey`, `relationship` - Database relationships
  - `text` - Raw SQL queries
  - `inspect` - Database introspection

### **Data Visualization**
- **Matplotlib** - Plotting library
  - Figure creation and management
  - PNG image generation to memory buffers
- **Seaborn** - Statistical data visualization
  - Heatmaps for attendance visualization
  - Bar plots for individual student statistics
  - Color palettes and styling
- **NumPy** - Numerical computing
  - Array operations
  - Data manipulation for graphs

### **Backend API (Additional Component)**
- **FastAPI** - Modern web framework for building APIs
- **Passlib** - Password hashing library
  - Bcrypt hashing algorithm
- **CORS Middleware** - Cross-origin resource sharing

### **Standard Library Modules**
- **threading.Thread** - Multi-threading for async operations
  - Background model loading
  - Database operations
  - Graph generation
- **datetime** - Date and time operations
  - Current date formatting
  - Date string conversion
- **calendar** - Calendar operations
  - Month range calculation
  - Day counting
- **io.BytesIO** - In-memory binary streams
  - Image buffer management
- **time** - Time-related functions

### **Development Tools & Utilities**
- **Builder (Kivy)** - KV language parser for UI layouts
- **Clock (Kivy)** - Event scheduling and timing
- **Texture (Kivy)** - GPU texture management for images
- **ObjectProperty (Kivy)** - Property binding system

### **File Formats & Data Handling**
- **JSON** - Data serialization for attendance records
- **PNG** - Image format for graphs and photos
- **JPG/JPEG** - Image format for student photos
- **PKL** - Pickle format for model files

### **System Integration**
- **Webcam/Camera** - Hardware integration via OpenCV
- **File System** - Local file storage for images and graphs

---

## 📦 Detailed Package List

### Core Dependencies:
```
kivy
kivymd
opencv-python (cv2)
deepface
sqlalchemy
psycopg2 (PostgreSQL adapter)
matplotlib
seaborn
numpy
fastapi
passlib[bcrypt]
python-multipart (for FastAPI form data)
```

### Database:
- PostgreSQL Server
- psycopg2-binary (Python PostgreSQL adapter)

### Optional/Development:
- uvicorn (ASGI server for FastAPI)

---

## 🏗️ Architecture Components

### **Frontend (KivyMD Application)**
- `try.py` - Main application entry point
- `my.kv` - UI layout definitions (KV language)

### **Database Layer**
- `connect_db.py` - Database connection and table definitions
- `crud_in_database.py` - Create, Read, Update, Delete operations
- `fact_db.py` - Data fetching functions

### **Visualization**
- `plotly_graph.py` - Graph generation functions (uses Matplotlib/Seaborn)

### **AI/ML Models**
- SFace facial recognition model
- OpenCV face detector model
- Pre-trained model files stored in `attendance/` directory

---

## 🔧 Key Technologies by Function

| Function | Technology |
|----------|-----------|
| **UI Framework** | Kivy, KivyMD |
| **Facial Recognition** | DeepFace, OpenCV |
| **Database** | PostgreSQL, SQLAlchemy |
| **Data Visualization** | Matplotlib, Seaborn, NumPy |
| **Image Processing** | OpenCV, PIL (via Matplotlib) |
| **Async Operations** | Python Threading |
| **API Backend** | FastAPI |
| **Password Security** | Passlib (Bcrypt) |

---

## 📁 Project Structure
```
SmartAttendanceSystem/
├── Kivy_app/              # Main desktop application
│   ├── try.py              # Main application file
│   ├── my.kv               # UI layout file
│   ├── connect_db.py      # Database connection
│   ├── crud_in_database.py # Database operations
│   ├── fact_db.py          # Data fetching
│   ├── plotly_graph.py     # Graph generation
│   └── attendance/         # Model files & images
├── backend/                # FastAPI backend (optional)
├── Frontend/               # Web frontend (optional)
└── requirements.txt        # Python dependencies
```

---

## 🎯 System Requirements

### **Hardware:**
- Webcam/Camera for face capture
- Minimum 4GB RAM (8GB recommended for smooth operation)
- Storage space for database and model files

### **Software:**
- Python 3.11+
- PostgreSQL 12+ (database server)
- Windows/Linux/macOS (cross-platform support via Kivy)

### **Python Version:**
- Python 3.11 (as indicated in error logs)

---

## 📊 Data Models

### **Database Tables:**
1. **student_info** - Student registration data (roll, name, mobile, photo)
2. **store_date** - Date tracking and lecture counting
3. **attendance tables** - Dynamic tables per date (e.g., `date25_08_2025`)
4. **setting** - Application settings (theme, auto-attendance)
5. **lacture_time** - Lecture time scheduling

---

## 🚀 Performance Optimizations

- Lazy loading of camera and AI models
- Frame throttling (process every 5th frame)
- Image downscaling for faster recognition
- Background threading for heavy operations
- Optimized database queries

---

## 📝 Notes

- The system uses date-based table naming convention (`dateDD_MM_YYYY`)
- Supports both zero-padded and non-padded date formats for backward compatibility
- Material Design 3 theme with customizable Light/Dark modes
- Real-time face detection with bounding box visualization
- Monthly attendance aggregation and visualization

---

**Project Developed By:** [Your Name/Team]  
**Last Updated:** 2025  
**Version:** 1.0




