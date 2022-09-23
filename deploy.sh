#!/bin/bash
echo Generating requirements.txt
poetry export > requirements.txt
gcloud functions deploy calendar --gen2 --runtime=python39 --entry-point=calendar --trigger-http --allow-unauthenticated
rm requirements.txt
