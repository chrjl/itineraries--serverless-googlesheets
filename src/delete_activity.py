import json
import os
import boto3

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def lambda_handler(event, context):
    itinerary_id = event["pathParameters"]["id"]
    sheet_name = event["pathParameters"]["sheet_name"]
    index = event["pathParameters"]["index"]

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

    # Validate request

    if not index.isdigit():
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Requested non-integer row index"}),
        }

    index = int(index)

    if index == 0:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Cannot delete header row"}),
        }

    # Retrieve sheet id
    try:
        with build("sheets", "v4", credentials=credentials) as service:
            request = service.spreadsheets().get(spreadsheetId=itinerary_id)
            response = request.execute()
    except HttpError as err:
        if (err.status_code == 404):
            return {"statusCode": 404, "body": json.dumps({"message": err.reason})}

        return {"statusCode": 400, "body": json.dumps({"message": err.reason})}

    sheets = response["sheets"]
    sheet_id = [
        sheet["properties"]["sheetId"]
        for sheet in sheets
        if sheet["properties"]["title"] == sheet_name
    ][0]

    # Delete row from sheet
    request_body = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": int(index),
                        "endIndex": int(index) + 1,
                    }
                }
            }
        ]
    }

    with build("sheets", "v4", credentials=credentials) as service:
        request = service.spreadsheets().batchUpdate(
            spreadsheetId=itinerary_id, body=request_body
        )
        response = request.execute()

    return {"statusCode": 204}
