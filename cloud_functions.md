# Cloud Functions Documentation

The project can be deployed as a Google Cloud Function.

## Local development

You can run the function locally with:

    > functions-framework --target calendar --debug

## Deploying

You can deploy the Cloud Function to Google Cloud like this:

    > poetry export > requirements.txt
    > gcloud functions deploy python-http-function --gen2 --runtime=python39 --entry-point=calendar --trigger-http --allow-unauthenticated

This assumes that you have set up the default project and region already using `gcloud config`.

You can then hit the deployed URL with `?username=...&password=...&customer_id=...` and it will return the iCalendar.
