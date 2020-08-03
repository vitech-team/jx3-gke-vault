#!/bin/bash

set -e

terraform init
terraform apply $*

# now lets update the requirements...
terraform output jx_requirements > jx-requirements.yml

