#!/usr/bin/python3
import requests
import os
from datetime import date, timedelta, datetime
from time import timezone
from collections import OrderedDict
import json

API_KEY = os.environ['TOGGL_API_KEY']

# GOTTA INVERT AND ENCODE THOSE SIGNS
if timezone <= 0:
    TIMEZONE_ENCODED = "%2B0" + str(int(-timezone/3600)) + "%3A00"
    TIMEZONE = "+0" + str(int(-timezone/3600)) + ":00"
else:
    TIMEZONE_ENCODED = "%2D0" + str(int(timezone/3600)) + "%3A00" 
    TIMEZONE = "-0" + str(int(timezone/3600)) + ":00"

DAY_INDEX = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class TogglCli():
    def __init__(self):
        self.date_range = date.today() - timedelta(weeks=2)
        self.user_obj = requests.get('https://www.toggl.com/api/v8/me?with_related_data=true', auth=(API_KEY, 'api_token')).json()
        self.projects = [(x['name'], x['id']) for x in self.user_obj['data']['projects']] # comprehension returning list of (name, id) pairs
        # get last 2 weeks of entries
        self.time_entries = requests.get('https://www.toggl.com/api/v8/time_entries?start_date=' + \
                str(self.date_range) + 'T00:00:00' + TIMEZONE_ENCODED, auth=(API_KEY, 'api_token')).json()
        self.time_log = OrderedDict()
        while self.date_range <= date.today():
            self.time_log[str(self.date_range)] = 0 # keep empty dates as int to make them more visible 
            self.date_range = self.date_range + timedelta(days=1)
        for entry in self.time_entries:
            entry_date = entry['start'].split('T')[0] # split date from time
            self.time_log[entry_date] = self.time_log[entry_date] + entry['duration']
        for isodate, duration in self.time_log.items():
                if duration != 0:
                    self.time_log[isodate] = duration/3600

    def date_prompt(self):
        print("existing hours: ")
        for i, item in enumerate(self.time_log.items()):
            weekday = DAY_INDEX[datetime.strptime(item[0], "%Y-%m-%d").weekday()]
            print("[{0:2}] {1:3} {2} - {3} hours".format(i, weekday, item[0], item[1])) # item(ISO date, existing hours)
        date_input = int(input("select date: "))
        print("")
        self.entry_prompt(date_input)

    def entry_prompt(self, date_input):
        print("selected date: {0}".format(str(list(self.time_log.keys())[date_input])))
        for i, project in enumerate(self.projects):
            print("[{0}] {1}".format(i, project[0]))
        proj_input = input("choose project: ")
        proj_input = int(proj_input)
        hours_input = int(input("input hours: "))
        self.create_entry(proj_input, date_input, hours_input)
    
    def create_entry(self, proj_input, date_input, hours_input):
        project = self.projects[proj_input]
        date = str(list(self.time_log.keys())[date_input])
        time_entry = {'time_entry':{
                "pid": project[1], 
                "start": date + "T09:00:00.000" + TIMEZONE,
                "duration": hours_input*3600,
                "created_with": "toggl-hammer"
        }}
        entry = requests.post('https://www.toggl.com/api/v8/time_entries', auth=(API_KEY, 'api_token'), data=json.dumps(time_entry))
        if not entry: # request.Response returns True is status 'OK'
            print(entry.text)
        else:
            self.time_log[date] = self.time_log[date] + float(hours_input)
            print("[ {0} hours logged for {1} ]".format(hours_input, project[0]))
            print('')

hammer = TogglCli()

while True:
    hammer.date_prompt()
