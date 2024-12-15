import os
import json
import boto3

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def lambda_handler(event, context):
    archive_id = event["pathParameters"]["id"]

    # Load service account credentials
    if SERVICE_ACCOUNT_DATA := os.getenv("SERVICE_ACCOUNT_INFO"):
        SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_DATA)
    elif SERVICE_ACCOUNT_PARAMETER_NAME := os.getenv("SERVICE_ACCOUNT_PARAMETER_NAME"):
        client = boto3.client("ssm")
        response = client.get_parameter(
            Name=SERVICE_ACCOUNT_PARAMETER_NAME, WithDecryption=True
        )

        SERVICE_ACCOUNT_INFO = json.loads(response["Parameter"]["Value"])

    SCOPES = ["https://www.googleapis.com/auth/drive"]
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

    # Check if archived itinerary exists
    try:
        with build("drive", "v3", credentials=credentials) as service:
            request = service.files().get(fileId=archive_id, fields="parents")
            response = request.execute()

        if response["parents"][0] != folders["Archives"]:
            return {
                "statusCode": 403,
                "body": json.dumps({"message": "File is not an archive"}),
            }
    except HttpError as err:
        if err.resp.status == 404:
            return {"statusCode": 204}

    # Delete archived itinerary
    with build("drive", "v3", credentials=credentials) as service:
        request = service.files().delete(fileId=archive_id)
        response = request.execute()

    return {"statusCode": 204}
