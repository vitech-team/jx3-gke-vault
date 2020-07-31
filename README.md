# Jenkins X 3.x GitOps Repository for GKE, Terraform and Vault

This git repository setups the cloud resources required to run Jenkins X on GKE via Terraform and then sets up Jenkins X with Vault.

## Prerequisites

We assume you have access to GCP and have modified the `main.mf` file to add your GCP project ID.

## Creating/upgrading cloud resources

You can run the `./bin/apply.sh` script or if you want to be explicit use terraform:

```bash 
terraform init
terraform apply
```

