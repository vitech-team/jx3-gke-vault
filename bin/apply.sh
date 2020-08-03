#!/bin/bash

set -e

terraform init $TERRAFORM_INPUT
terraform apply $TERRAFORM_INPUT $TERRAFORM_APPROVE

# now lets update the requirements...
terraform output jx_requirements > jx-requirements.yml

