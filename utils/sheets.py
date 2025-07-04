# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# from utils.calend import current_month, next_month
# import os
#
#
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
# SAMPLE_SPREADSHEET_ID = "TEST"
#
#
# creds = None
# if os.path.exists("token.json"):
#     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#
# if not creds or not creds.valid:
#     if creds and creds.expired and creds.refresh_token:
#         creds.refresh(Request())
#     else:
#         flow = InstalledAppFlow.from_client_secrets_file(
#             "credentials.json", SCOPES
#         )
#         creds = flow.run_local_server(port=0)
#     with open("token.json", "w") as token:
#         token.write(creds.to_json())
#
#
# def get_sheet_names(spreadsheet_id):
#     try:
#         service = build("sheets", "v4", credentials=creds)
#
#         spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
#         sheets = spreadsheet.get('sheets', [])
#
#         sheet_names = [sheet['properties']['title'] for sheet in sheets]
#         return sheet_names
#
#     except HttpError as err:
#         print(err)
#         return None
#
#
# def get_data_from_sheet(month, spreadsheet_id):
#     SAMPLE_RANGE_NAME = f"{month}!A2:M"
#
#     try:
#         service = build("sheets", "v4", credentials=creds)
#
#         sheet = service.spreadsheets()
#         result = (
#             sheet.values()
#             .get(spreadsheetId=spreadsheet_id, range=SAMPLE_RANGE_NAME)
#             .execute()
#         )
#         values = result.get("values", [])
#
#         if not values:
#             print("No data found.")
#             return None
#
#         return values
#
#     except HttpError as err:
#         print(err)
#         return None
