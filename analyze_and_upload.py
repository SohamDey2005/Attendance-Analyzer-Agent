import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import schedule
import time

def authorize_gsheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('config/credentials.json', scope)
    return gspread.authorize(creds)

def analyze_attendance(csv_path):
    df = pd.read_csv(csv_path)
    df.fillna("", inplace=True) 
    results = []
    for _, row in df.iterrows():
        name = str(row['Name']).strip()
        login_time_str = str(row['Login Time']).strip()
        if login_time_str == "":
            status = 'Absent'
            login_display = "N/A"
        else:
            try:
                login_time = datetime.strptime(login_time_str, "%H:%M")
                if login_time <= datetime.strptime("09:15", "%H:%M"):
                    status = 'Present'
                elif login_time <= datetime.strptime("10:00", "%H:%M"):
                    status = 'Late'
                else:
                    status = 'Absent'
                login_display = login_time.strftime("%H:%M")
            except ValueError:
                status = 'Absent'
                login_display = "Invalid"
        results.append([str(name), str(login_display), str(status)])
    return results

def write_to_gsheet(sheet_name, data):
    client = authorize_gsheet()
    sheet = client.open(sheet_name).sheet1 
    sheet.clear()
    sheet.append_row(["Name", "Login Time", "Status"])
    for row in data:
        sheet.append_row(row)

def main_task():
    csv_path = "data/attendance.csv"
    attendance_data = analyze_attendance(csv_path)
    write_to_gsheet("Daily Attendance", attendance_data)
    output_df = pd.DataFrame(attendance_data, columns=["Name", "Login Time", "Status"])
    output_df.to_csv("data/processed_attendance.csv", index=False)

with open("config/schedule_time.txt", "r") as f:
    run_time = f.read().strip()  

schedule.every().day.at(run_time).do(main_task)

while True:
    schedule.run_pending()
    time.sleep(60)
