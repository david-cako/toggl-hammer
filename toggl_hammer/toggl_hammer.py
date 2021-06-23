#!/usr/local/bin/python3
import os, requests, json, signal, sys
from datetime import date, timedelta, datetime
from time import timezone
from collections import OrderedDict
from .us_holidays import holidays_export as holidays

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
        if date_input in holidays:
            self.holiday = holidays.get(date_input)
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
        # get last [week_range] weeks of entries
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
        print("")
        print("existing hours: ")
        for i, entry in enumerate(self.time_log.values()):
            weekday = DAY_INDEX[datetime.strptime(str(entry.date), "%Y-%m-%d").weekday()]
            if entry.holiday:
                print("[{0:2}] {1:3} {2} - {3} hours - {4}".format(i, weekday, entry.date, entry.time, entry.holiday)) # item(ISO date, existing hours)
            else:
                print("[{0:2}] {1:3} {2} - {3} hours".format(i, weekday, entry.date, entry.time)) # item(ISO date, existing hours)
        date_index = input("select date(s): ")
        print("")           
        if date_index.find("-") != -1:
            date_range = date_index.split("-")
            if len(date_range) != 2:
                print("Invalid date selection.  Expected int or range (i.e., '1-5').")
                return
            else:
                self.entry_prompt(list(
                    range(int(date_range[0]), int(date_range[1]) + 1)
                ))
        else:
            try:
                self.entry_prompt(int(date_index))
            except ValueError: 
                print("Invalid date selection.  Expected int or range (i.e., '1-5').")

    def entry_prompt(self, date_index):
        if type(date_index) == list:
            print("selected date range: {0} - {1}".format(
                str(
                    list(self.time_log.values())[date_index[0]].date
                ),
                str(
                    list(self.time_log.values())[date_index[-1]].date
                ),
            ))
        else:
            print("selected date: {0}".format(str(
                list(self.time_log.values())[date_index].date
            )))
        for i, project in enumerate(self.projects):
            print("[{0}] {1}".format(i, project[0]))
        proj_index = input("choose project: ")
        proj_index = int(proj_index)
        proj_id = self.projects[proj_index][1]
        task_list = requests.get('https://www.toggl.com/api/v8/projects/' + str(proj_id) + '/tasks', auth=(API_KEY, 'api_token')).json()
        
        if task_list != None:
            for i, task in enumerate(task_list):
                print("[{0}] {1}".format(i, task['name']))
            task_index = input("choose task: ")
            task_index = int(task_index)
            task_id = task_list[task_index]['id']
        else:
            task_id = None

        hours_index = int(input("input hours: "))
        print("")
        if type(date_index) == list:
            for each in date_index:
                self.create_entry(proj_index, each, hours_index, task_id)
        else:
            self.create_entry(proj_index, date_index, hours_index, task_id)
    
    def create_entry(self, proj_index, date_index, hours_index, task_id=None):
        project = self.projects[proj_index]
        date = str(
            list(self.time_log.values())[date_index].date
        )
        time_entry = {'time_entry':{
                "pid": project[1],
                "start": date + "T09:00:00.000" + TIMEZONE,
                "duration": hours_index*3600,
                "description": "description",
                "created_with": "toggl-hammer"
        }}
        if task_id != None:
            time_entry["time_entry"]["tid"] = task_id

        entry = requests.post('https://www.toggl.com/api/v8/time_entries', auth=(API_KEY, 'api_token'), data=json.dumps(time_entry))
        if not entry: # request.Response returns True if status 'OK'
            print(entry.text)
        else:
            self.time_log[date].time = self.time_log[date].time + float(hours_index)
            print("[ {0} hours logged for {1} on {2} ]".format(hours_index, project[0], date))

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

