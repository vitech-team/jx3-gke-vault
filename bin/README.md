## Create Cloud Resources

These instructions will walk you through setting up Jenkins X with Terraform

### Prerequisites

These instructions assume you have cloned this git repository and run `cd` into the clone directory so that you can see this `README.md` file by running:

```bash 
ls -al bin/README.md
```

### Setup your resources

Run the `./bin/apply.sh` script which effectively invokes:

```bash 
terraform init
terraform apply
```

This will use terraform to setup your resources


### Install the git operator

**NOTE** that soon we will be installing the git operator via Terraform, so these instructions will disappear. 

But until then please install the git operator via:

```bash
jx admin operator
```

