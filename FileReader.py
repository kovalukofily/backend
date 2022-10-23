from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pprint import pprint

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
spreadsheet_id = '1oAOFzblBW87Zu8P4fdDi-WsWMSGMh2wUclBGQT1SobU'
departures_range = 'Departures!A2:J199'
arrivals_range = 'Arrivals!A2:J199'


# range_to_read = 0 for departures, 1 for arrivals. Must be integer, not string
def read_spreadsheet(range_code):
    if range_code == 0:
        range_to_read = departures_range
    elif range_code == 1:
        range_to_read = arrivals_range
    else:
        return None
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range_to_read).execute()
        values = result.get('values', [])

        if not values:
            # print('No data found.')
            return None

        all_flights = {}

        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            flight = {
                'city': row[1], 'time': row[2],
                'weekday1': 0, 'weekday2': 0, 'weekday3': 0, 'weekday4': 0, 'weekday5': 0, 'weekday6': 0, 'weekday7': 0
                }
            for i in range(3, len(row)):
                if row[i] == '1':
                    flight[f'weekday{i-2}'] = 1
            
            all_flights[row[0]] = flight

        #pprint(all_flights)
        return all_flights

    except HttpError as err:
        return None


