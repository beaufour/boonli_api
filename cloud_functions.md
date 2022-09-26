# Cloud Functions Documentation

The project can be deployed as a Google Cloud Function.

## Local development

You can run the function locally with:

    > functions-framework --target calendar --debug

## Deploying

You can deploy the Cloud Function to Google Cloud like this:

    > poetry export > requirements.txt
    > gcloud functions deploy calendar --gen2 --runtime=python39 --region=us-east1 --entry-point=calendar --trigger-http --allow-unauthenticated

This can be run using `./deploy.sh`.

This assumes that you have set up the default project using `gcloud config set project PROJECT_ID`.

You can then hit the deployed URL (will be output by the `gcloud` command above) with `?username=...&password=...&customer_id=...` and it will return the iCalendar.

## Custom Domain

To deploy the Cloud Function on a custom domain you need deploy a load balancer which is a little involved on Google Cloud. There's a description on how to do it [here](https://fabianlee.org/2022/04/01/gcp-deploying-a-2nd-gen-python-cloud-function-and-exposing-from-an-https-lb/), and in the [official documentation](https://cloud.google.com/load-balancing/docs/negs/serverless-neg-concepts). Note that `gen2` Cloud Functions are treated as Cloud Run in these setups.

This project includes a [Terraform](https://www.terraform.io/) config in the `terraform`. All you need to do is:

* Enable the necessary APIs [here](https://console.cloud.google.com/apis/enableflow?apiid=compute.googleapis.com,oslogin.googleapis.com)
* Supply credentials (Terraform will give you the instructions if needed)
* Edit `terraform/variables.tf` so they match your setup (and potentially `terraform/main.tf` too)
* Run `terraform init`
* Run `terraform apply`

Note that it seems like, the Terraform Google Cloud provider doesn't quite understand the dependencies on the Network Endpoint Group, so if you change that you'll have to remove all the whole setup and reapply manually (or I have a bug in the Terraform code...).
