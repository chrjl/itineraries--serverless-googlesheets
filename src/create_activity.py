import json
import os
import boto3

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def lambda_handler(event, context):
    itinerary_id = event["pathParameters"].get("id")
    sheet_name = event["pathParameters"].get("sheet_name")
    activity_index = event["pathParameters"].get("index")
    body = event["body"]

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
    if activity_index and not activity_index.isdigit():
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Non-integer activity index"}),
        }

    if not body:
        return {"statusCode": 400, "body": json.dumps({"message": "Empty body"})}

    body = json.loads(body)

    # Retrieve sheet header
    try:
        with build("sheets", "v4", credentials=credentials) as service:
            request = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=itinerary_id, range=f"{sheet_name}!1:1")
            )
            response = request.execute()

            header = response["values"][0]
    except HttpError as err:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Error loading sheet"}),
        }

    # Create sheet row from JSON body
    row = [body.get(field, "") for field in header]

    # Add activity to sheet
    # If activity_index is provided, overwrite row. Otherwise, append sheet with new activity.
    request_body = {"values": [row]}

    if activity_index:
        row_number = int(activity_index) + 1
        range_name = f"{sheet_name}!{row_number}:{row_number}"
        with build("sheets", "v4", credentials=credentials) as service:
            request = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=itinerary_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body=request_body,
                )
            )
            response = request.execute()

    else:
        with build("sheets", "v4", credentials=credentials) as service:
            request = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=itinerary_id,
                    range=sheet_name,
                    valueInputOption="RAW",
                    body=request_body,
                )
            )
            response = request.execute()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response),
    }
