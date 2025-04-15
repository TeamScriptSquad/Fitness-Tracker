from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

def init_gsheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("FitnessTrackerLogs").sheet1

def log_workout(exercise, sets, reps, weight, comment=""):
    sheet = init_gsheet()
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d"),
        exercise, sets, reps, weight, comment
    ])