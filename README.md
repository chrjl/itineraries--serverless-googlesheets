# itineraries--serverless-googlesheets

AWS SAM project for serverless front-facing API of trip itinerary planning app backed with Google Sheets. The app authenticates with a Google Cloud project using a service account and uses Google Workspace APIs (Google Drive, Google Sheets) to read to and write from Google Sheets.

↗ See also: [FastAPI backend](https://github.com/chrjl/itineraries--fastapi-googlesheets)  
↗ See also: [Reference front-end app (React)](https://github.com/chrjl/itineraries--frontend)

This project creates the following resources:

- [ ] Parameter Store parameter: to store the Google Cloud service account credentials
- [ ] API Gateway
- [ ] Lambda layer: [`google-api-python-client`](https://github.com/googleapis/google-api-python-client) Lambda dependency

Migration Lambda function 

- [ ] Scaffold Google Drive folders, template spreadsheet

Lambda functions (and API routes) for read:

- [ ] Get all itineraries
- [ ] Get an itinerary

Lambda functions (and API routes) for write:

- [ ] Create an itinerary
- [ ] Delete an itinerary
- [ ] Add an activity to itinerary
- [ ] Update an itinerary

## Development and deployment

Prior to deployment (or development):

- Create and store credentials for Google Cloud service account

  - Manually update Parameter Store parameter with Google Cloud service account details

    Secure string parameters are not supported in CloudFormation, so a placeholder string is used in the SAM template. This needs to be updated to allow Lambda functions access to the Google Workspace APIs.

  - For local development/invoke, store the credentials in a properly formatted environment variable JSON (see [#local-development](#local-development)).

- [Build Lambda layer](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html)

  ```console
  layers/google-api-python-client$ python -m venv python
  layers/google-api-python-client$ source python/bin/activate
  layers/google-api-python-client$ pip install -r requirements.txt
  layers/google-api-python-client$ zip -r layer_content.zip python
  ```

### Local development

SAM local [cannot access Parameter Store](https://github.com/aws/aws-sam-cli/issues/616#issuecomment-707891861) into environment variables, so the service account credentials need to be stored as local JSON and read into the SAM local server using `--env-vars`. The data read in with `--env-vars` will override the values defined in the SAM template.

```console
$ sam local start-api --env-vars env/service_account.json
```

The environment variable file should take the form as described in the [documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-invoke.html#serverless-sam-cli-using-invoke-environment-file):

```json
{
  "MyFunction1": {
    "SERVICE_ACCOUNT": "..."
  },
  "MyFunction2": {
    "SERVICE_ACCOUNT": "..."
  }
}
```

or, to apply globally

```json
{
  "Parameters": {
    "SERVICE_ACCOUNT": "..."
  }
}
```

### Deployment

To do...
