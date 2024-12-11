import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT = json.loads(os.getenv("SERVICE_ACCOUNT"))

credentials = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT, scopes=SCOPES
)


with build("drive", "v3", credentials=credentials) as service:
    request = service.files().list(q="mimeType='application/vnd.google-apps.folder'")
    response = request.execute()
    folders = {file.get("name"): file.get("id") for file in response.get("files")}


def lambda_handler(event, context):
    with build("drive", "v3", credentials=credentials) as service:
        request = service.files().list(
            q=f"mimeType='application/vnd.google-apps.spreadsheet' and '{folders['Itineraries']}' in parents"
        )
        response = request.execute()
        itineraries = response.get('files')

    return {"statusCode": 200, "body": json.dumps(itineraries)}
