#!/usr/local/bin/python3
import os, requests, json, signal, sys
from datetime import date, timedelta, datetime
from time import timezone
from collections import OrderedDict
from .us_holidays import us_holidays

API_KEY = os.environ['TOGGL_API_KEY']

# GOTTA INVERT AND ENCODE THOSE SIGNS
if timezone <= 0:
    TIMEZONE_ENCODED = "%2B0" + str(int(-timezone/3600)) + "%3A00"
    TIMEZONE = "+0" + str(int(-timezone/3600)) + ":00"
else:
    TIMEZONE_ENCODED = "%2D0" + str(int(timezone/3600)) + "%3A00" 
    TIMEZONE = "-0" + str(int(timezone/3600)) + ":00"

DAY_INDEX = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class LogEntry():
    def __init__(self, date_input):
        self.date = date_input
        self.time = 0 
        if date_input in us_holidays:
            self.holiday = us_holidays.get(date_input)
        else:
            self.holiday = None
    def toHours(self):
        if self.time != 0:
            self.time = float(self.time/3600) # cast non-zero times as float, making empty days easy to see 

class TogglCli():
    def __init__(self, week_range):
        self.date_range = date.today() - timedelta(weeks=week_range)
        self.user_obj = requests.get('https://www.toggl.com/api/v8/me?with_related_data=true', auth=(API_KEY, 'api_token')).json()
        self.projects = [(x['name'], x['id']) for x in self.user_obj['data']['projects']] # comprehension returning list of (name, id) pairs
        # get last 2 weeks of entries
        self.time_entries = requests.get('https://www.toggl.com/api/v8/time_entries?start_date=' + \
                str(self.date_range) + 'T00:00:00' + TIMEZONE_ENCODED, auth=(API_KEY, 'api_token')).json()
        self.time_log = OrderedDict()
        while self.date_range <= date.today():
            self.time_log[str(self.date_range)] = LogEntry(self.date_range) 
            self.date_range = self.date_range + timedelta(days=1)
        for entry in self.time_entries:
            entry_date = entry['start'].split('T')[0] # split date from time
            self.time_log[entry_date].time = self.time_log[entry_date].time + entry['duration']
        for entry in self.time_log.values():
            entry.toHours()  # after iterating through each individual entry (many days having multiple), convert time to hours  

    def date_prompt(self):
        print("existing hours: ")
        for i, entry in enumerate(self.time_log.values()):
            weekday = DAY_INDEX[datetime.strptime(str(entry.date), "%Y-%m-%d").weekday()]
            if entry.holiday:
                print("[{0:2}] {1:3} {2} - {3} hours - {4}".format(i, weekday, entry.date, entry.time, entry.holiday)) # item(ISO date, existing hours)
            else:
                print("[{0:2}] {1:3} {2} - {3} hours".format(i, weekday, entry.date, entry.time)) # item(ISO date, existing hours)
        date_index = int(input("select date: "))
        print("")
        self.entry_prompt(date_index)

    def entry_prompt(self, date_index):
        print("selected date: {0}".format(str(self.time_log.values()[date_index].date)))
        for i, project in enumerate(self.projects):
            print("[{0}] {1}".format(i, project[0]))
        proj_index = input("choose project: ")
        proj_index = int(proj_index)
        hours_index = int(input("input hours: "))
        self.create_entry(proj_index, date_index, hours_index)
    
    def create_entry(self, proj_index, date_index, hours_index):
        project = self.projects[proj_index]
        date = str(self.time_log.values()[date_index].date)
        time_entry = {'time_entry':{
                "pid": project[1], 
                "start": date + "T09:00:00.000" + TIMEZONE,
                "duration": hours_index*3600,
                "created_with": "toggl-hammer"
        }}
        entry = requests.post('https://www.toggl.com/api/v8/time_entries', auth=(API_KEY, 'api_token'), data=json.dumps(time_entry))
        if not entry: # request.Response returns True if status 'OK'
            print(entry.text)
        else:
            self.time_log[date].time = self.time_log[date].time + float(hours_index)
            print("[ {0} hours logged for {1} ]".format(hours_index, project[0]))
            print('')

def handler(signum, frame):
    print('')
    sys.exit(0)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit() and int(sys.argv[1]) <= 8:
            week_range = int(sys.argv[1])
    else:
        week_range = 2
    signal.signal(signal.SIGINT, handler)
    hammer = TogglCli(week_range)
    while True:
        hammer.date_prompt()

