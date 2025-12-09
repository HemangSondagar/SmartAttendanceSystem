from kivy.uix.filechooser import error
import matplotlib.pyplot as plt
from fact_db import fatch_one, fatch_all_studebent_attandance,fatch_one_month_attandance
import seaborn as sns
import numpy as np
from matplotlib.colors import ListedColormap
import io
from sqlalchemy import inspect,text
from connect_db import engine,session
from datetime import datetime



def one_student_graph(roll: int, date: str):
    try:
        ap = fatch_one(roll, date)
        a = p = 0
        for i in ap[0]:
            if str(i).lower() == 'p':
                p += 1
            else:
                a += 1

        labels = ["Absent", "Present"]
        sizes = [a, p]
        colors = ['red', 'green']

        plt.figure(figsize=(8, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title(f"Attendance for Roll No: {roll} of {date}")

        #  Save image to memory (not disk)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf.getvalue()   # binary PNG data
    except:
        print("error in graph")


def table_exists(table_name):
    """Check if table exists in database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def all_student_graph(date_str: str):
    """
    Generate heatmap based on actual DB table alignment.
    Roll numbers and table rows WILL MATCH correctly.
    """
    try:
        table_name = date_str

        # Validate table exists
        if not table_exists(table_name):
            print(f"❌ Table not found: {table_name}")
            return False,(f"❌ Date not found: {table_name}")

        # Fetch rows in correct order
        rows = session.execute(
            text(f"SELECT student_roll, student_attandace FROM {table_name} ORDER BY student_roll")
        ).fetchall()

        if not rows:
            print(f"❌ No attendance data found for: {table_name}")
            return False,(f"❌ No attendance data found for: {table_name}")

        rolls = []
        attendance_matrix = []

        for roll, json_data in rows:
            rolls.append(roll)

            if isinstance(json_data, str):
                try:
                    json_data = json.loads(json_data)
                except:
                    json_data = {}

            if not isinstance(json_data, dict):
                json_data = {}

            # Convert json: {"l_1":"p","l_2":"a"} => [1,0]
            lecture_numbers = sorted(
                [int(k.split("_")[1]) for k in json_data.keys() if k.startswith("l_")]
            )

            row = []
            for lec in lecture_numbers:
                v = json_data.get(f"l_{lec}")
                row.append(1 if v == "p" else 0)
            attendance_matrix.append(row)

        if not attendance_matrix:
            print("⚠ No valid JSON attendance found.")
            return False,"NO valid attendance found."

        data = np.array(attendance_matrix)

        # Heatmap with fixed order
        cmap = ListedColormap(["red", "green"])
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            data,
            cmap=cmap,
            annot=True,
            cbar=False,
            xticklabels=[f"Lec {i+1}" for i in range(data.shape[1])],
            yticklabels=rolls
        )
        plt.title(f"Attendance Heatmap: {table_name}")
        plt.xlabel("Lectures")
        plt.ylabel("Roll Numbers")

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf.getvalue(),"Imge generated successfully"

    except Exception as e:
        print(f"🔥 Error in all_student_graph: {e}")
        return False,(f"🔥 Error generating graph: ")




def one_month_attandace_graph(month: int) -> bool:
    """
    Create and save a graph for attendance in a month.
    Overwrites the previous graph file.
    Returns True if saved successfully, False otherwise.
    """

    try:
        # Get present/absent data
        data = fatch_one_month_attandance(month)
        print(data)
        if data is None :
            print(f"No attendance data found for month {month}")
            return False,("No attendance data found for the specified month.")
        if data == False:
            print(f"No attendance data found for month {month}")
            return False,("No attendance data found for the specified month.")

        present = data['present_percent']
        absent = data['absent_percent']

        # Labels and values
        labels = ['Present', 'Absent']
        values = [present, absent]
        colors = ['#4CAF50', '#F44336']  # Green and Red

        # Create pie chart
        plt.figure(figsize=(6,6))
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, shadow=True)
        plt.title(f'All student allAttendance Percentage for Month {month}', fontsize=14)

        # Save the figure with fixed name (overwrite each time)
        filename = 'test_all_month.png'
        plt.savefig(filename)
        plt.close()

        print(f" Attendance graph saved as {filename}")
        return True,"Attendance graph saved successfully."

    except Exception as e:
        print(f"Error saving attendance graph: {e}")
        return False,("Error saving attendance graph.")
    

def attendance_graph_between_dates(start_date: str, end_date: str) -> bool:
    """
    Create and save a pie chart for attendance between two dates.
    
    Args:
        start_date (str): Start date in 'day-month-year' format, e.g., '24-8-2025'
        end_date (str): End date in 'day-month-year' format, e.g., '1-9-2025'
    
    Returns:
        bool: True if graph saved successfully, False otherwise
    """
    # Convert input dates to database table format
    def convert_date(date_str):
        try:
            d, m, y = date_str.split('-')
            return f"date{d.zfill(2)}_{m.zfill(2)}_{y}"
        except:
            return False,"Invalid date format"   #none hatu
    
    start_table = convert_date(start_date)
    end_table = convert_date(end_date)
    
    if not start_table or not end_table:
        print("Invalid date format. Expected 'day-month-year'")
        return False,("Invalid date format. Expected 'day-month-year'")

    # Fetch all table dates between start and end from store_date table
    try:
        dates = session.execute(text("SELECT date FROM store_date")).mappings()
    except Exception as e:
        print(f"Error fetching dates: {e}")
        return False,"Error fetching dates from database."
    if dates is None:
        print("No dates found in store_date table.")
        return False,("No dates found in store_date table.")
    date_list = []
    try:

        start_dt = datetime.strptime(start_date, "%d-%m-%Y")
        end_dt = datetime.strptime(end_date, "%d-%m-%Y")
    except Exception as e:
        print(f"Error parsing dates: {e}")
        return False,("Error parsing dates. Ensure format is 'day-month-year'")
    for row in dates:
        table_name = row['date']
        try:
            table_dt = datetime.strptime(table_name.replace("date", ""), "%d_%m_%Y")
        except:
            continue
        if start_dt <= table_dt <= end_dt:
            date_list.append(table_name)

    if not date_list:
        print("No attendance data found in the given range.")
        return False,("No attendance data found in the given range.")

    # Count present and absent
    total_present = 0
    total_absent = 0
    for table_name in date_list:
        try:
            result = session.execute(text(f"SELECT student_attandace FROM {table_name}")).mappings()
        except Exception as e:
            print(f"Error reading table {table_name}: {e}")
            continue

        for row in result:
            att_data = row.get("student_attandace")
            if not att_data:
                continue
            for value in att_data.values():
                if value.lower() == "p":
                    total_present += 1
                elif value.lower() == "a":
                    total_absent += 1

    total = total_present + total_absent
    if total == 0:
        print("No attendance data found for this date range.")
        return False,("No attendance data found for this date range.")

    present_percent = (total_present / total) * 100
    absent_percent = (total_absent / total) * 100

    # Plot pie chart
    labels = ['Present', 'Absent']
    values = [present_percent, absent_percent]
    colors = ['#4CAF50', '#F44336']

    plt.figure(figsize=(6,6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, shadow=True)
    plt.title(f'All Student Attendance from {start_date} to {end_date}', fontsize=14)

    # Save graph
    filename = f"date_to-date.png"
    plt.savefig(filename)
    plt.close()
    print(f"Attendance graph saved as {filename}")
    return True,("Attendance graph saved successfully.")


def convert_date_format(date_string: str):
    """
    Convert date from 'day-month-year' to 'dateDD_MM_YYYY' format.
    Example: '5-8-2025' -> 'date05_08_2025'
    """
    print("date -------> as input ------>",date_string)
    try:
        day, month, year = date_string.split('-')
        # Pad day and month with leading zeros if needed
        day = day.zfill(2)
        month = month.zfill(2)
        # Construct new format
        table_name = f"date{day}_{month}_{year}"
        print(table_name)
        return table_name
    except Exception:
        print("Invalid date format. Expected 'day-month-year' (e.g., '24-8-2025')")
        return False,"Invalid date format. Expected 'day-month-year' (e.g., '24-8-2025')"




if __name__ == "__main__":
    pass

    # print(attendance_graph_between_dates(1,1))