#!/bin/bash

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


PROJECT_ID=aerospike2bt
MAIN=com.google.cloud.as2bt.DataflowJsonWorker

BACKUP_FILE=gs://test-youngsong/books.json

BIGTABLE_INSTANCE_ID=bookshelf
BIGTABLE_TABLE_ID=books

RUNNER=direct

export PATH=/usr/lib/jvm/java-8-openjdk-amd64/bin/:$PATH

mvn compile -e exec:java \
 -Dexec.mainClass=$MAIN \
-Dexec.args="--backupFile=$BACKUP_FILE \
            --project=$PROJECT_ID \
            --bigtableInstanceId=$BIGTABLE_INSTANCE_ID \
            --bigtableTableId=$BIGTABLE_TABLE_ID \
            --runner=$RUNNER" 


