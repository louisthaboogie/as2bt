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

# [START startup]
set -v

# Phase 1: Install and start aerospike community
apt-get -qqy update
apt-get -qqy upgrade
apt-get -qqy install python jq

curl -sSLO https://www.aerospike.com/artifacts/aerospike-server-community/4.5.0.2/aerospike-server-community-4.5.0.2-ubuntu18.04.tgz

tar -xf aerospike-server-community-4.5.0.2-ubuntu18.04.tgz

cd aerospike-server-community-4.5.0.2-ubuntu18.04 || exit
./asinstall

systemctl enable aerospike.service
systemctl start aerospike.service
grep cake /var/log/syslog

sed -i.backup -e '1,/namespace bar {/!d' -e '/namespace bar {/d' /etc/aerospike/aerospike.conf
sed -i 's/context any info/context any warning/g' /etc/aerospike/aerospike.conf

cat >>/etc/aerospike/aerospike.conf <<EOF

namespace bookshelf {
        replication-factor 2
        memory-size 4G
        default-ttl 30d
        storage-engine device {
                file /opt/aerospike/data/bookshelf.dat
                filesize 16G
                data-in-memory true # Store data in memory in addition to file.
        }
}

EOF

systemctl restart aerospike.service

for count in {1..3}; do
        sleep 2
        if grep '{bookshelf}' /var/log/syslog; then
                aql -c 'create index bookid on bookshelf.books (id) STRING'
                break
        fi

        if $count -eq 3; then
                echo "Bookshelf namespace hasn't configured correctly."
                exit 1
        fi
done

# Phase 2: Install and start bookshelf app

# Install dependencies from apt
apt-get update
apt-get install -yq \
	git build-essential supervisor python python-dev python-pip libffi-dev libssl-dev \
	python3-distutils python3-dev zlib1g-dev

# Create a bookshelf user. The application will run as this user.
useradd -m -d /home/bookshelf bookshelf

# pip from apt is out of date, so make it update itself and install virtualenv.
pip install --upgrade pip virtualenv

# [TODO] This git clone need to change using public git repogitery.
gcloud source repos clone as2bt /opt/app --project=aerospike2bt

# Talk to the metadata server to get the project id
PROJECTID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/project/project-id" -H "Metadata-Flavor: Google")

# Update config.py with PROJECTID
sed -i "s/your-project-id/$PROJECTID/g" /opt/app/bookshelf/config.py

# Install app dependencies
virtualenv -p python3 /opt/app/bookshelf/env
source /opt/app/bookshelf/env/bin/activate
/opt/app/bookshelf/env/bin/pip install -r /opt/app/bookshelf/requirements.txt

# Generate dummy data
/opt/app/bookshelf/env/bin/python /opt/app/bookshelf/gen_data.py

# Make sure the bookshelf user owns the application code
chown -R bookshelf:bookshelf /opt/app

# Configure supervisor to start gunicorn inside of our virtualenv and run the
# application.
cat >/etc/supervisor/conf.d/bookshelf.conf << EOF
[program:bookshelf]
directory=/opt/app/bookshelf
command=/opt/app/bookshelf/env/bin/python main.py
autostart=true
autorestart=true
user=bookshelf
# Environment variables ensure that the application runs inside of the
# configured virtualenv.
environment=VIRTUAL_ENV="/opt/app/bookshelf/env",PATH="/opt/app/bookshelf/env/bin",\
    HOME="/home/bookshelf",USER="bookshelf"
stdout_logfile=syslog
stderr_logfile=syslog
EOF

supervisorctl reread
supervisorctl update
supervisorctl status all

# Application should now be running under supervisor
# [END startup]
