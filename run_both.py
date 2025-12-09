import subprocess
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

processes = [
    {
        "name": "Backend",
        "cmd": ["uvicorn", "main:app", "--port", "8000"],
        "cwd": os.path.join(BASE_DIR, "backend"),
    },
    {
        "name": "Frontend",
        "cmd": ["uvicorn", "main:app", "--port", "8001"],
        "cwd": os.path.join(BASE_DIR, "frontend"),
    },
]

try:
    for proc in processes:
        print(f"🚀 Starting {proc['name']}...")
        subprocess.Popen(proc["cmd"], cwd=proc["cwd"])
        time.sleep(2)  # slight delay between startups

    print("\n✅ Both servers started successfully!")
    print("Backend → http://127.0.0.1:8000")
    print("Frontend → http://127.0.0.1:8001")
    print("Press CTRL + C to stop.\n")

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Stopping servers...")
