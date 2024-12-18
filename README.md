# itineraries--serverless-googlesheets

AWS SAM project for serverless front-facing API of trip itinerary planning app backed with Google Sheets. The app authenticates with a Google Cloud project using a service account and uses Google Workspace APIs (Google Drive, Google Sheets) to read to and write from Google Sheets.

↗ See also: [FastAPI backend](https://github.com/chrjl/itineraries--fastapi-googlesheets)  
↗ See also: [Reference front-end app (React)](https://github.com/chrjl/itineraries--frontend)

This project creates the following resources:

- Parameter Store parameter: to store the Google Cloud service account credentials

  The parameter needs to be manually written after creation (a placeholder value is set in the template). See [#development-and-deployment](#development-and-deployment).

- API Gateway HTTP API
- Lambda layer: [`google-api-python-client`](https://github.com/googleapis/google-api-python-client) Lambda dependency

Migration Lambda function

- [!TODO] Scaffold Google Drive folders, template spreadsheet

Lambda functions (and API routes) for read:

- Get all active itineraries
- Get all archived itineraries
- Get an itinerary

Lambda functions (and API routes) for write:

- Create an itinerary
- Archive an itinerary
- Delete an archived itinerary
- Add an activity to itinerary
- Delete an activity from itinerary
- Overwrite an activity
- Patch an activity

## Credentials

The Lambda functions require Google Cloud service account credentials, and are authored to search for them. The Lambda code is authored to search first in environment variables (`SERVICE_ACCOUNT_INFO`) then, if the environment variable is not found, in SSM Parameter Store.

Resolving secret string parameters from Parameter Store into environment variables is not supported for Lambda (in CloudFormation), so the `Boto3` SSM client is used in the Lambda code to retrieve the parameter. The `SSMParameterReadPolicy` needs to be added to Lambda functions to permit access to the parameter.

## Development and deployment

Prior to deployment (or development):

- Create and store credentials for Google Cloud service account in either Lambda function environment variable `SERVICE_ACCOUNT_INFO` or SSM Parameter Store secure string defined in the template.

  - Manually update Parameter Store parameter with Google Cloud service account details

    Secure string parameters are not supported in CloudFormation, so a placeholder string is used in the SAM template. This needs to be updated to allow Lambda functions access to the Google Workspace APIs. The JSON should be unescaped.

    ```console
    $ aws ssm put-parameter --name ServiceAccountParameterName --type SecureString --value $SERVICE_ACCOUNT_JSON_STRING --overwrite
    ```

    If service account info is stored in a SAM-formatted environment variable JSON (stored in `env/service-account.json`):

    ```console
    $ aws ssm put-parameter --name ServiceAccountParameterName --type SecureString --value "$(cat env/service-account.json | jq -c '.Parameters.SERVICE_ACCOUNT_INFO | fromjson')" --overwrite
    ```

    To directly use service account JSON:

    ```console
    $ aws ssm put-parameter --name ServiceAccountParameterName --type SecureString --value "$(cat /path/to/service-account.json)" --overwrite
    ```

  - For local development/invoke, store the credentials in a properly formatted environment variable JSON (see [#local-development](#local-development)).

- [Build Lambda layer](https://docs.aws.amazon.com/lambda/latest/dg/python-layers.html)

  ```console
  layers/google-api-python-client$ python -m venv python
  layers/google-api-python-client$ source python/bin/activate
  layers/google-api-python-client$ pip install -r requirements.txt
  layers/google-api-python-client$ zip -r layer_content.zip python
  ```

### Local development

SAM local does not work with Parameter Store, so service account credentials need to be stored in Lambda function environment variables.

- [Cannot access Parameter Store](https://github.com/aws/aws-sam-cli/issues/616#issuecomment-707891861) into environment variables.
- Lambda functions cannot resolve secure string parameters via [dynamic reference in CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references-ssm-secure-strings.html).
- Does not create Parameter Store parameters, which makes parameters unreachable by Lambda function code (`Boto3`).

The Lambda functions are authored such that service account credentials can be read from environment variable `SERVICE_ACCOUNT_INFO`, if it exists. For local development, the environment variable can be stored in JSON and read into the SAM local server using `--env-vars`. The data read in with `--env-vars` will override the values defined in the SAM template.

```console
$ sam local start-api --env-vars env/service_account.json
```

The environment variable file should take the form as described in the [documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-invoke.html#serverless-sam-cli-using-invoke-environment-file). To apply globally:

```json
{
  "Parameters": {
    "SERVICE_ACCOUNT": "..."
  }
}
```

### Deployment

To do...
