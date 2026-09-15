# Packages
import textwrap
import datetime
import python_weather
import asyncio
import os.path
import argparse
from zoneinfo import ZoneInfo
import json

#Check argments for --real flag and --tomorrow
parser = argparse.ArgumentParser(description="POS Printer Script")
parser.add_argument('--real', action='store_true', help='Send output to physical USB printer')
parser.add_argument('--tomorrow', action='store_true', help='Generate receipt for tomorrow [IN ADVANCE]')
args = parser.parse_args()

#Configure the date for today or tomorrow based on the --tomorrow flag
local_tz = ZoneInfo("America/Toronto")                   # MOVED UP: Defined tz early
target_date = datetime.datetime.now(tz=local_tz).date()  # ADDED: Initialize target_date before adding to it

if args.tomorrow:
    target_date += datetime.timedelta(days=1)
date_str = target_date.strftime("%A, %b %d")
if args.tomorrow:
    date_str += " [IN ADVANCE]"

#Configure the printer (if --real flag is set)
p = None
if args.real:
    try:
        from escpos.printer import Usb
        p = Usb(0x0416, 0x5011, in_ep=0x81, out_ep=0x03, profile="POS-5890")
    except Exception as e:
        print(f"[WARNING] Could not connect to physical printer: {e}")
icode = 0
def pos_print(text=""):
    print(text) # Always prints to standard out (captured by NiceGUI web dashboard)
    if p is not None:
        p.text(text + "\n") # Only prints to hardware if --real flag is enabled


# Google Calendar API Setup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly",
          "https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/tasks"
          ]

#Authenticate
def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds
shared_creds = get_credentials()

#Set up time zone for Montreal
# --- TIMEZONE & DATE SETUP (Global so Calendar and Date/Time can both use them) ---
# MODIFIED: Use target_date instead of hardcoded 'today'
start_of_day = datetime.datetime.combine(target_date, datetime.time.min, tzinfo=local_tz)
end_of_day = datetime.datetime.combine(target_date, datetime.time.max, tzinfo=local_tz)

# -- CURRENT TIME--  
def get_current_timedate():
    now = datetime.datetime.now(tz=local_tz)
    pos_print("DATE: " + date_str) # MODIFIED: Use the formatted string we created at the top
    pos_print("TIME: Printed at " + now.strftime("%H:%M") + "\n")


# --- WEATHER ---
async def getWeather() -> None:
    async with python_weather.Client(unit=python_weather.METRIC) as client:
        weather = await client.get("Montreal")
        
        # MODIFIED: Pick index 0 for today, index 1 for tomorrow
        day_idx = 1 if args.tomorrow else 0
        forecast = list(weather.daily_forecasts)[day_idx]
        
        pos_print("Temp: " + str(forecast.lowest_temperature) + " / " + str(forecast.highest_temperature) + " °C")
        pos_print("Rain: " + str(weather.precipitation) + " mm (" + str(weather.description) + ")\n")

# --- GOOGLE CALENDAR ---
def getCalendar(creds):
    try:
        service = build("calendar", "v3", credentials=creds)
        calendar_ids = ["primary", "9c6572976fcb3a19c006550cd9a3a96b3b0038d793993ce19b9e01c5b1b49bf1@group.calendar.google.com"]
        
        all_events = []
        for cal_id in calendar_ids:
            try:
                events_result = (
                    service.events()
                    .list(
                        calendarId=cal_id,
                        timeMin=start_of_day.isoformat(),
                        timeMax=end_of_day.isoformat(),
                        timeZone="America/Toronto",
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
                all_events.extend(events_result.get("items", []))
            except HttpError as error:
                pos_print(f"Warning: Could not fetch from {cal_id}: {error}")

        if not all_events:
          pos_print("No planned events for today")
          return

        all_events.sort(key=lambda x: x["start"].get("dateTime", x["start"].get("date")))

        for event in all_events:
          start = event["start"].get("dateTime", event["start"].get("date"))
          if "dateTime" in event["start"]:
              start_time = datetime.datetime.fromisoformat(start).astimezone(local_tz).strftime("%H:%M")
          else:
              start_time = "All Day"

          eventline = f"{start_time} | {event['summary']}"
          pos_print(eventline)

    except HttpError as error:
        pos_print(f"An error occurred with the Google API: {error}")


# --- GOOGLE SHEETS ---
def getGoogleSheet(creds):
    try:
        service = build("sheets", "v4", credentials=creds)
        
        SPREADSHEET_ID = "1eLJQG5i7mBBbESRawSpsIlIUq1V3HA8VzU6MFlrBplE"
        RANGES = ["'Fall 26'!S24:U100", "'Fall 26'!W35:Y100"] 
        
        sheet_result = service.spreadsheets().values().batchGet(
            spreadsheetId=SPREADSHEET_ID, ranges=RANGES
        ).execute()
        
        value_ranges = sheet_result.get("valueRanges", [])
        assignments_rows = value_ranges[0].get("values", []) if len(value_ranges) > 0 else []
        exams_rows = value_ranges[1].get("values", []) if len(value_ranges) > 1 else []

        MAX_WIDTH = 32
        prefix = "[   ] "
        indent_space = "      "  # Exactly 6 spaces to align under the task name

        def print_tasks(rows):
            count = 0
            for row in rows:
                if not row or not any(row):
                    continue
                    
                class_col = row[0].strip() if len(row) > 0 and row[0] else ""
                task_col = row[1].strip() if len(row) > 1 and row[1] else ""
                raw_tag = row[2].strip() if len(row) > 2 and row[2] else ""
                
                category = class_col.split()[0] if class_col else ""

                if category and task_col:
                    task = f"{category}: {task_col}"
                elif category:
                    task = category
                else:
                    task = task_col
                
                if not task:
                    continue

                count += 1
                tag_str = f"[{raw_tag}]" if raw_tag else ""

                if tag_str:
                    max_task_on_line1 = MAX_WIDTH - len(prefix) - 1 - len(tag_str)
                    
                    if len(task) <= max_task_on_line1:
                        space_count = MAX_WIDTH - len(prefix) - len(task) - len(tag_str)
                        line = f"{prefix}{task}{' ' * space_count}{tag_str}"
                        pos_print(line)
                    else:
                        chunk = task[:max_task_on_line1]
                        line1 = f"{prefix}{chunk} {tag_str}"
                        pos_print(line1)
                        
                        remaining_task = task[max_task_on_line1:]
                        wrapped_remaining = textwrap.wrap(
                            remaining_task,
                            width=MAX_WIDTH,
                            initial_indent=indent_space,
                            subsequent_indent=indent_space
                        )
                        for w_line in wrapped_remaining:
                            pos_print(w_line)
                else:
                    full_text = f"{prefix}{task}"
                    wrapped = textwrap.wrap(
                        full_text,
                        width=MAX_WIDTH,
                        initial_indent="",
                        subsequent_indent=indent_space
                    )
                    for w_line in wrapped:
                        pos_print(w_line)
            return count

        # 1. ASSIGNMENTS SECTION
        pos_print(f"{'Assignments':<16}{'[days remaining]':>16}")
        if not assignments_rows:
            pos_print("No assignments found.")
        else:
            printed = print_tasks(assignments_rows)
            if printed == 0:
                pos_print("No assignments pending.")

        # 2. EXAMS & QUIZZES SECTION
        # Pre-filter exams to only keep those within 7 days
        upcoming_exams = []
        for row in exams_rows:
            if not row or not any(row):
                continue
            raw_tag = row[2].strip() if len(row) > 2 and row[2] else ""
            try:
                days_left = int(raw_tag)
                if 0 <= days_left <= 7:
                    upcoming_exams.append(row)
            except ValueError:
                continue

        # Only print the header and the items if there is actually an upcoming exam
        if upcoming_exams:
            pos_print(f"\n{'Quiz/Exams':<16}{'[days remaining]':>16}")
            print_tasks(upcoming_exams)
                
    except HttpError as error:
        pos_print(f"Sheets API Error: {error}")

# --- LOCAL TASKS ---
def getTasks():
    try:
        pos_print("\nPersonal:")
        with open('/home/ncarigi/personal.json', 'r') as f:
            tasks = json.load(f)

            
        if not tasks:
            pos_print("No sprint tasks for today.")
            return

        indent_space = "    "

        for task in tasks:
            task_text = task.get('task', '') if isinstance(task, dict) else str(task)
            
            # Check if the task has a completed date
            is_done = task.get('completed_date') is not None if isinstance(task, dict) else False

            # Swap the prefix based on whether it is done
            prefix = "[ X ] " if is_done else "[   ] "

            full_text = f"{prefix}{task_text}"
            wrapped = textwrap.wrap(
                full_text,
                width=32,
                initial_indent="",
                subsequent_indent=indent_space
            )
            for w_line in wrapped:
                pos_print(w_line)
                
    except FileNotFoundError:
        pos_print("No personal.json file found.")
    except Exception as e:
        pos_print(f"Task Error: {e}")



def getMeals():
    if not os.path.exists("meals.json"):
        pos_print("No meals.json file found.")
        return
        
    try:
        with open("meals.json", 'r') as f:
            data = json.load(f)
            
        # Uses target_date so it automatically handles the --tomorrow flag
        target_str = target_date.strftime("%Y-%m-%d")
        
        # Pull schedule dictionary for the targeted day
        target_schedule = data.get("schedule", {}).get(target_str, {"Lunch": [], "Dinner": []})
        
        lunch_meals = target_schedule.get("Lunch", [])
        dinner_meals = target_schedule.get("Dinner", [])
        
        lunch_str = ", ".join(lunch_meals) if lunch_meals else "Nothing planned"
        dinner_str = ", ".join(dinner_meals) if dinner_meals else "Nothing planned"
        
        pos_print(f"LUNCH: {lunch_str}")
        pos_print(f"DINNER: {dinner_str}")
        
    except Exception as e:
        pos_print(f"Meal Error: {e}")

# --- PRINT EXECUTION ---
pos_print("================================")
pos_print("          SYSTEM READY          ")
pos_print("================================")

get_current_timedate()

pos_print("================================")
pos_print("          1. WEATHER"            )
pos_print("================================")

asyncio.run(getWeather())

pos_print("================================")
pos_print("         2. SCHEDULE"            )
pos_print("================================")

getCalendar(shared_creds)

pos_print("\n================================")
pos_print("     3. DEADLINES & TASKS"       )
pos_print("================================")

getGoogleSheet(shared_creds)
getTasks()

pos_print("\n================================")
pos_print("            4. MEALS            ")
pos_print("================================")

getMeals()

pos_print("\n================================")
pos_print("      5. PACKING LOAD OUT       ")
pos_print("================================")

# Feed a few blank lines to clear the tear-bar
pos_print("\n\n\n")