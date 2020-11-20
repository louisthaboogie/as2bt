# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# run on Cloud Functions runtime as Python 3.7

from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials


# refer to https://cloud.google.com/dataflow/docs/guides/templates/executing-templates
def run_dataflow(file_name):
    credentials = GoogleCredentials.get_application_default()
    service = build('dataflow', 'v1b3', credentials=credentials)

    # Set the following variables to your values.
    JOBNAME = 'as2bt-{file}'.format(file=file_name)
    PROJECT = 'aerospike2bt'
    BUCKET = 'test-youngsong'
    TEMPLATE = 'as2bt-template'
    ZONE = "us-central1-f"
    GCSPATH = "gs://{bucket}/templates/{template}".format(bucket=BUCKET, template=TEMPLATE)
    BODY = {
        "jobName": "{jobname}".format(jobname=JOBNAME),
        "parameters": {
            "backupFile": "gs://{bucket}/{file}".format(bucket=BUCKET, file=file_name)
        },
        "environment": {
            "tempLocation": "gs://{bucket}/temp".format(bucket=BUCKET),
            "zone": ZONE
        }
    }

    request = service.projects().templates().launch(projectId=PROJECT, gcsPath=GCSPATH, body=BODY)
    response = request.execute()

    print(response)


def handle_event(event, context):
    """ Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    print("Processing file: {filename}.".format(filename=file['name']))

    run_dataflow(file['name'])
