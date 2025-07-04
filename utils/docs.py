# import os.path
#
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
#
# SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
#
# creds = None
#
# if os.path.exists("token2.json"):
#     creds = Credentials.from_authorized_user_file("token2.json", SCOPES)
#
# if not creds or not creds.valid:
#     if creds and creds.expired and creds.refresh_token:
#         creds.refresh(Request())
#     else:
#         flow = InstalledAppFlow.from_client_secrets_file(
#           "credentials.json", SCOPES)
#         creds = flow.run_local_server(port=0)
#     with open("token2.json", "w") as token:
#         token.write(creds.to_json())
#
#
# def get_content(doc_id):
#     try:
#         service = build("docs", "v1", credentials=creds)
#         document = service.documents().get(documentId=doc_id).execute()
#         content = document.get("body").get("content")
#
#         full_text = ""
#         for elem in content:
#             paragraph = elem.get("paragraph")
#             if paragraph:
#                 elements = paragraph.get("elements")
#                 for element in elements:
#                     text_run = element.get("textRun")
#                     if text_run:
#                         content = text_run.get("content").strip()
#                         if content:
#                             full_text += f" {content}"
#         return full_text
#     except Exception as e:
#         print(e)
#         return ''
#
#
# def get_content_with_links(doc_id):
#     try:
#         service = build("docs", "v1", credentials=creds)
#         document = service.documents().get(documentId=doc_id).execute()
#         content = document.get("body").get("content")
#
#         links = []
#
#         for elem in content:
#             paragraph = elem.get("paragraph")
#             if paragraph:
#                 elements = paragraph.get("elements")
#                 for element in elements:
#                     text_run = element.get("textRun")
#                     if text_run:
#                         link = (
#                             text_run.get("textStyle", {})
#                             .get("link", {})
#                             .get("url")
#                         )
#                         if link:
#                             links.append(link)
#
#         return links
#     except Exception as e:
#         print(e)
#         return "", []
