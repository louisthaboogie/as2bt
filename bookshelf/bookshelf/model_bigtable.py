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

from flask import current_app
from google.auth import compute_engine
from google.cloud import bigtable
from google.cloud.bigtable import row_filters
from random import randint

project_id = current_app.config['PROJECT_ID']
instance_id = current_app.config['BIGTABLE_INSTANCE_ID']
table_id = current_app.config['BIGTABLE_TABLE_ID']

credentials = compute_engine.Credentials()
client = bigtable.Client(credentials=credentials, project=project_id, admin=True)
instance = client.instance(instance_id)
table = instance.table(table_id)

cf = 'info'

id_col = 'id'.encode()
title = 'title'.encode()
author = 'author'.encode()
published_date = 'published_date'.encode() 
image_url = 'image_url'.encode()
description = 'description'.encode()
created_by = 'created_by'.encode()  
created_by_id = 'created_by_id'.encode()

cols_encoded = [id_col, title, author, published_date, image_url, description, created_by, created_by_id]
cols = ['id', 'title', 'author', 'publishedDate', 'imageUrl', 'description', 'createdBy', 'createdById']

row_filter = row_filters.CellsColumnLimitFilter(1)

def init_app(app):
    pass

# using last_key instead of cursor because there is no cursor or read from offset api
def list(limit=3, last_key=None, cursor=None):
    last_key=cursor
    
    if last_key:
        limit = limit + 2
        partial_rows = table.read_rows(start_key=last_key, limit=limit, filter_=row_filter)
    else:
        limit = limit + 1
        partial_rows = table.read_rows(limit=limit, filter_=row_filter)
  
    recs = []
    rows = []

    for row in partial_rows:
        recs.append(__from_bigtable_row__(row))
        rows.append(row)

    if last_key and len(rows) >= limit:
        recs.pop(0)
        rows.pop(0)
        recs.pop()
        rows.pop()
        last_key = recs[-1]['id']
    elif last_key and len(rows) < limit:
        recs.pop(0)
        rows.pop(0)
        last_key = None
    elif not last_key and len(rows) >= limit:
        recs.pop()
        rows.pop()
        last_key = recs[-1]['id']
    elif not last_key and len(rows) < limit:
        last_key = None     
        
    if not rows:
        return [], None
    else:
        return recs, last_key

    
# using last_key instead of cursor because there is no cursor or read from offset api 
def list_by_user(user_id, limit=3, last_key=None, cursor=None):
    last_key=cursor
    
    # row key starts with user_id 
    if last_key:
        partial_rows = table.read_rows(start_key=last_key, limit=limit, filter_=row_filter)
    else:
        partial_rows = table.read_rows(start_key=user_id.encode(), limit=limit, filter_=row_filter)

    recs = []
    rows = []

    i = 0

    for row in partial_rows:
        if(i >= limit):
            break
     
        info_cells = row.cells[cf]
        created_by_id_val = info_cells[created_by_id][0].value.decode('utf-8')

        if(user_id == created_by_id_val):
            recs.append(__from_bigtable_row__(row))
            rows.append(row)
            i += 1

    if not rows:
        return [], last_key
    else:
        return recs, rows[-1].row_key


def __from_bigtable_row__(row):
    data = dict()
    
    info_cells = row.cells[cf]
    keys = info_cells.keys()

    for i, col in enumerate(cols_encoded):
        if col in keys:
            data[cols[i]] = info_cells[col][0].value.decode('utf-8')

    return data


def __data_to_row__(data, row_key):
    row = table.row(row_key)
    keys = data.keys()

    for i, col in enumerate(cols):
        if col in keys:
            row.set_cell(cf, cols_encoded[i], data[col])
            
    return row


def read(id):
    partial_rows = table.read_rows(start_key=str(id).encode(), limit=1, filter_=row_filter)
    
    if not partial_rows:
        return None
    
    data = __from_bigtable_row__([row for row in partial_rows][0])

    if 'id' in data and data['id'] == id:
        return data
    else:
        return None


def create(data):
    data['id'] = str(randint(10 ** 9, 10 ** 10 - 1))

    if 'createdById' in data:
        row_key = str(data['id'] + '_' + data['createdById'])
    else:
        row_key = str(data['id'])

    rows = [(__data_to_row__(data, row_key))]

    table.mutate_rows(rows)

    return read(data['id'])


def update(data, id):
    data['id'] = str(id).decode('utf-8')
    row_key = str(data['id'] + '_' + data['createdById']).encode()
    row = __data_to_row__(data, row_key)
    row.commit()

    return read(data['id'])


def delete(id):
    partial_rows = table.read_rows(start_key=str(id).encode(), limit=1, filter_=row_filter)
    read_rows = [row for row in partial_rows]
    row = table.row(read_rows.pop(0).row_key)

    row.delete()
    row.commit()
