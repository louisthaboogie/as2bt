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

provider "google" {
}

variable gce_vm_zone {
  description = "Compute engine zone value"
  type = string
  default = "us-east1-b"
}

variable gcs_bucket_prefix {
  description = "gcs bucket prefix"
  type = string
  default = "bookshelf"
}

variable gcs_bucket_location {
  description = "gcs bucket location"
  type = string
  default = "us-east1"
}

resource "google_project_service" "service-api-compute" {
  service   = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "service-api-storage-component" {
  service   = "storage-component.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "service-api-bigtable" {
  service   = "bigtable.googleapis.com"
  disable_on_destroy = true
}

resource "google_project_service" "service-api-bigtableadmin" {
  service   = "bigtableadmin.googleapis.com"
  disable_on_destroy = true
}

resource "google_project_service" "service-api-dataflow" {
  service   = "dataflow.googleapis.com"
  disable_on_destroy = true
}

resource "random_id" "bookshelf_bucket_name" {
  keepers = {
    gcs_bucket_prefix = "${var.gcs_bucket_prefix}"
  }

  prefix = "${var.gcs_bucket_prefix}-"
  byte_length = 8
}

resource "google_storage_bucket" "bookshelf_bucket" {
  name     = "${random_id.bookshelf_bucket_name.hex}"
  location = "${var.gcs_bucket_location}"
  force_destroy = true
}

resource "google_storage_bucket_object" "startup_script" {
  name   = "scripts/startup-scripts"
  source = "./scripts/startup.sh"
  bucket = "${google_storage_bucket.bookshelf_bucket.name}"
}

resource "google_compute_instance" "bookshelf_aerospike" {
  name         = "bookshelf-aerospike"
  zone         = "${var.gce_vm_zone}"
  machine_type = "n1-standard-2"
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
      size = 50
      type = "pd-ssd"
    }
  }

  tags = ["bookshelf-http"]
  
  network_interface {
    network = "default"
    access_config {
    }
  }

  metadata = {
    startup-script-url="${google_storage_bucket.bookshelf_bucket.url}/${google_storage_bucket_object.startup_script.output_name}"
  }

  service_account {
    scopes = [
      "storage-rw",
      "logging-write",
      "monitoring-write",
      "service-control",
      "service-management",
      "cloud-source-repos-ro",
      "https://www.googleapis.com/auth/bigtable.data"
    ]
  }

  depends_on = ["google_project_service.service-api-compute"]
}

resource "google_compute_firewall" "default_allow_bookshelf_http" {
  name    = "default-bookshelf-allow-http"
  network = "default"
  target_tags = ["bookshelf-http"]

  allow {
    protocol = "tcp"
    ports = ["80", "8080"]
  }

  source_ranges = [ "0.0.0.0/0" ]

  depends_on = ["google_project_service.service-api-compute"]
}

resource "google_bigtable_instance" "bookshelf_bigtable" {
  name          = "bookshelf-bigtable"
  instance_type = "DEVELOPMENT"

  cluster {
    cluster_id   = "bookshelf-bigtable-cluster"
    zone         = "${var.gce_vm_zone}"
    storage_type = "SSD"
  }

  depends_on = ["google_project_service.service-api-bigtableadmin"]
}

resource "google_bigtable_table" "bookshelf_bigtable_books" {
  name          = "books"
  instance_name = "${google_bigtable_instance.bookshelf_bigtable.name}"
  column_family {
    family = "info"
  }

  depends_on = ["google_project_service.service-api-bigtable"]
}

// Enable notifications by giving the correct IAM permission to the unique service account.

data "google_storage_project_service_account" "gcs_account" {}

resource "google_pubsub_topic_iam_binding" "binding" {
    topic       = "${google_pubsub_topic.bookshelf_topic.name}"
    role        = "roles/pubsub.publisher"
    members     = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
}

resource "google_pubsub_topic" "bookshelf_topic" {
    name = "bookshelf_topic"
}

resource "google_storage_notification" "notification" {
    bucket            = "${google_storage_bucket.bookshelf_bucket.name}"
    payload_format    = "JSON_API_V1"
    topic             = "${google_pubsub_topic.bookshelf_topic.id}"
    event_types       = ["OBJECT_FINALIZE"]
    depends_on        = ["google_pubsub_topic_iam_binding.binding"]
}
