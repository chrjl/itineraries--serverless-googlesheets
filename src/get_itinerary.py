import os
import json
import boto3

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def lambda_handler(event, context):
    id = event["pathParameters"]["id"]

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

    # check that spreadsheet exists
    try:
        with build("drive", "v3", credentials=credentials) as service:
            request = service.files().get(fileId=id)
            file = request.execute()
    except HttpError as Error:
        if Error.resp["status"] == "404":
            return {"statusCode": 404}

    # get data from file
    with build("sheets", "v4", credentials=credentials) as service:
        request = (
            service.spreadsheets().values().get(spreadsheetId=id, range="activities")
        )
        rows = request.execute().get("values", [])
        activities = [
            {"category": "activity", **activity}
            for activity in spreadsheet_to_dict(rows)
        ]

    with build("sheets", "v4", credentials=credentials) as service:
        request = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=id, range="transportation")
        )
        rows = request.execute().get("values", [])
        transportation = [
            {"category": "transportation", **transportation}
            for transportation in spreadsheet_to_dict(rows)
        ]

    with build("sheets", "v4", credentials=credentials) as service:
        request = service.spreadsheets().values().get(spreadsheetId=id, range="housing")
        rows = request.execute().get("values", [])
        housing = [
            {"category": "housing", **housing} for housing in spreadsheet_to_dict(rows)
        ]

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({**file, "data": [*activities, *housing, *transportation]}),
    }


def spreadsheet_to_dict(rows):
    header = rows[0]
    data = rows[1:]
    return [{key: value for (key, value) in zip(header, row) if value} for row in data]
