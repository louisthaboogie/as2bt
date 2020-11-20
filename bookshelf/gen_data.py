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


import bookshelf
import config

app = bookshelf.create_app(config)


def gen(n_records=10000):
    keys = ['title', 'author', 'publishedDate', 'imageUrl', 'description', 'createdBy', 'createdById']
    values = ['book', 'write', '1970-01-01',
              "https://storage.googleapis.com/aerospike2bt-bookshelf/The_Home_Edit-2019-06-24-044906.jpg",
              "test",
              "write",
              "anonymous"]

    print("Generating dummy books data...")
    for i in range(n_records):
        data = dict()

        for j, key in enumerate(keys):
            if j == 2 or j == 3:
                value = values[j]
            elif j == 6:
                value = str(i) + "_" + values[j]
            else:
                value = values[j] + "_" + str(i)

            data[keys[j]] = value

        with app.app_context():
            data = bookshelf.get_model().create(data)


if __name__ == '__main__':
    gen(10000)
