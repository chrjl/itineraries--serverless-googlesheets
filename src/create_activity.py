import json
import os
import boto3

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def lambda_handler(event, context):
    itinerary_id = event["pathParameters"]["id"]
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

    # Validate request body
    if not body:
        return {"statusCode": 400, "body": json.dumps({"message": "Empty body"})}

    body = json.loads(body)

    if body["type"] == "activity":
        sheet_name = "activities"
    elif body["type"] == "transportation":
        sheet_name = "transportation"
    elif body["type"] == "housing":
        sheet_name = "housing"
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Missing or unsupported activity type"}),
        }

    # Retrieve sheet header
    with build("sheets", "v4", credentials=credentials) as service:
        request = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=itinerary_id, range=f"{sheet_name}!1:1")
        )
        response = request.execute()

        header = response["values"][0]

    # Create sheet row from JSON body
    row = [body.get(field, "") for field in header]

    # Add activity to sheet
    request_body = {"values": [row]}
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
