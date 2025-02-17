#!/usr/bin/env bash
set -e

# Copy static files
cp -rf /shared/* /app &

# Decrypt and copy config file
mkdir -p /root/.kube &
cd /app && make decrypt INPUTFILE=/app/configs/config.gpg PASSPHRASE=$LARGE_PASSPHRASE OUTPUTFILE=/app/config && cp -rf /app/config /root/.kube/config &
cp -rf /app/config /root/.kube/config &

# Configure aws
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set aws-region us-east-2

# Branching base on POD_TYPE
if [ "$POD_TYPE" == "WORKER" ];
then
	make start_celery
else
	make start_django
fi
