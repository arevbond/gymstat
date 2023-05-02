import os
import datetime
from random import randrange

import httplib2
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


def get_service_sacc():
    creds_json = os.path.dirname(__file__) + "/creds/sacc.json"
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    creds_service = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)


def send_data(sheet_id: str, execise: str, weight: str, repets: str):
    sheet = get_service_sacc().spreadsheets()

    date = datetime.date.today().strftime("%d.%m.%Y")
    values = [[date, execise, weight, repets]]
    resp = sheet.values().append(
        spreadsheetId=sheet_id,
        range="Лист1",
        valueInputOption="RAW",
        # insertDataOption="INSERT_ROWS",
        body={'values': values}).execute()

    return resp

