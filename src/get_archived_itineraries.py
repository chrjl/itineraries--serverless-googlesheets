import os
import json
import boto3

from google.oauth2 import service_account
from googleapiclient.discovery import build


def lambda_handler(event, context):
    # Load service account credentials
    if SERVICE_ACCOUNT_DATA := os.getenv("SERVICE_ACCOUNT_INFO"):
        SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_DATA)
    elif SERVICE_ACCOUNT_PARAMETER_NAME := os.getenv("SERVICE_ACCOUNT_PARAMETER_NAME"):
        client = boto3.client("ssm")
        response = client.get_parameter(
            Name=SERVICE_ACCOUNT_PARAMETER_NAME, WithDecryption=True
        )

        SERVICE_ACCOUNT_INFO = json.loads(response["Parameter"]["Value"])

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    credentials = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, scopes=SCOPES
    )

    # Retrieve folder ids
    with build("drive", "v3", credentials=credentials) as service:
        request = service.files().list(
            q="mimeType='application/vnd.google-apps.folder'"
        )
        response = request.execute()
        folders = {file.get("name"): file.get("id") for file in response.get("files")}

    # Retrieve itineraries
    with build("drive", "v3", credentials=credentials) as service:
        request = service.files().list(
            q=f"mimeType='application/vnd.google-apps.spreadsheet' and '{folders['Archives']}' in parents"
        )
        response = request.execute()
        itineraries = response.get("files")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(itineraries),
    }
