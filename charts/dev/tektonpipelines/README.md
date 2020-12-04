
Create new docker config secret which will be used in Service account for pipelines
```shell script
gcloud iam service-accounts keys create keyfile.json --iam-account "${CLUSTER_NAME}-tekton@${GCP_PROJECT}.iam.gserviceaccount.com"

SECRETNAME=docker-registry-auth
kubectl create secret docker-registry $SECRETNAME \
  --docker-server=https://gcr.io \
  --docker-username=_json_key \
  --docker-email=sdlc@vitechteam.com \
  --docker-password="$(cat keyfile.json)"
```
