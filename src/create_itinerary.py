import json
import os
import boto3

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        name = body.get("name")
        email = body.get("email")

        if not name:
            raise Exception("Missing required field")
    except Exception as err:
        return {"statusCode": 400, "body": json.dumps({"message": err}, default=str)}

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

    # Retrieve template id
    with build("drive", "v3", credentials=credentials) as service:
        query = f"name = 'Itinerary' and '{folders['Templates']}' in parents"
        request = service.files().list(q=query)
        response = request.execute()
        template_id = response["files"][0]["id"]

    # Make a copy of template
    try:
        with build("drive", "v3", credentials=credentials) as service:
            file_metadata = {"name": name, "parents": [folders["Itineraries"]]}
            request = service.files().copy(fileId=template_id, body=file_metadata)
            response = request.execute()
            file_id = response["id"]
    except HttpError as err:
        return {"statusCode": 500, "body": json.dumps({"message": err}, default=str)}

    # Share file if email provided
    with build("drive", "v3", credentials=credentials) as service:
        permissions_metadata = {"type": "user", "emailAddress": email, "role": "reader"}
        request = service.permissions().create(
            fileId=file_id, body=permissions_metadata
        )
        response = request.execute()

    return {"statusCode": 201, "body": json.dumps({"id": file_id})}
