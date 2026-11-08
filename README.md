# CloudWatch Logs Query with Boto3 and Docker

A Python script that lists CloudWatch log groups in an AWS account, using Boto3. It runs inside a Docker container, so there is nothing to install on your machine apart from Docker and the AWS CLI.

I built this as a lab to practise safe, read-only API access to AWS from a script.

## What it does

- Connects to AWS with a named profile (`lab`)
- Lists the CloudWatch log groups in one region (`eu-west-2` by default)
- Runs in a container, with credentials mounted from your machine and never stored in the image

## Requirements

- An AWS account
- [Docker](https://docs.docker.com/get-docker/)
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), only used on your machine to save credentials and test them

## Project layout

```
.
├── Dockerfile
├── requirements.txt
├── get-log-groups.py
├── .dockerignore
└── README.md
```

## Step 1: Create a read-only IAM user

Do not use the root user. Root can do everything, including closing the account. A read-only user can look but cannot change or delete anything, so a leaked key does far less damage.

1. In the AWS Console, open **IAM** and choose **Create user**.
2. Leave console access off. The script uses the API, so it does not need a password.
3. Attach these policies directly:
   - `ReadOnlyAccess`
   - `CloudWatchLogsReadOnlyAccess`
4. Open the new user, go to **Security credentials** and choose **Create access key**.
5. Copy the **Access key ID** and **Secret access key**. The secret is shown once, so save it somewhere safe.

## Step 2: Save your credentials on your machine

```bash
aws configure --profile lab
```

It asks for four things:

| Prompt | Value |
| --- | --- |
| Access key ID | From Step 1 |
| Secret access key | From Step 1 |
| Default region | `eu-west-2` (London) |
| Output format | `json` |

This writes two files in your home folder: `~/.aws/credentials` and `~/.aws/config`. On Windows they are in `C:\Users\YourName\.aws\`.

CloudWatch Logs are per region. If you pick the wrong region, you will see no log groups.

## Step 3: Test the keys

```bash
aws sts get-caller-identity --profile lab
```

If it returns your account number and user name, the keys work. If it fails, fix the keys or region first. There is no point going further until this passes.

## Step 4: Add the project files

**requirements.txt**

```
boto3
```

**get-log-groups.py**

```python
import os

import boto3

profile = os.getenv("AWS_PROFILE", "lab")
region = os.getenv("AWS_REGION", "eu-west-2")

session = boto3.Session(profile_name=profile, region_name=region)
logs = session.client("logs")

paginator = logs.get_paginator("describe_log_groups")

count = 0
for page in paginator.paginate():
    for group in page["logGroups"]:
        print(group["logGroupName"])
        count += 1

print(f"\n{count} log group(s) found in {region}")
```

**Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY get-log-groups.py .

CMD ["python", "get-log-groups.py"]
```

**.dockerignore**

```
.aws
.env
venv
.git
__pycache__
```

## Step 5: Build the image

```bash
docker build -t cw-logs-query .
```

## Step 6: Run the container

Mount your `~/.aws` folder as read-only, so the container can read the credentials without copying them into the image.

**Mac or Linux**

```bash
docker run --rm \
  -v ~/.aws:/root/.aws:ro \
  cw-logs-query
```

**Windows (PowerShell)**

```powershell
docker run --rm `
  -v "$env:USERPROFILE\.aws:/root/.aws:ro" `
  cw-logs-query
```

### Use another profile or region

```bash
docker run --rm \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_PROFILE=lab \
  -e AWS_REGION=eu-west-1 \
  cw-logs-query
```

## Example output

```
/aws/lambda/my-function
/aws/ecs/my-service
/var/log/messages

3 log group(s) found in eu-west-2
```

## Common problems

| Error | Likely cause |
| --- | --- |
| `ProfileNotFound` | The `~/.aws` folder is not mounted, or the profile name is wrong. |
| `NoCredentialsError` | You did not run `aws configure --profile lab`. |
| `AccessDenied` | The policies are not attached to the IAM user. |
| Empty results | Wrong region, or there are no log groups there. |
| `docker: command not found` | Docker is not installed or not running. |

## Security notes

- Never commit access keys to Git. Keys in code often end up on GitHub.
- Never copy `~/.aws` into the image. Always mount it at run time.
- Keep the IAM user read-only. Rotate or delete the access key when the lab is finished.

## What I learned

Credentials should live outside the code and outside the image. A named profile plus a read-only mount keeps the container simple and the account safer.

## Next steps

- Query log events with `filter_log_events`
- Try CloudWatch Logs Insights queries
- Add other clients, such as `ec2`, `s3` or `ce` for cost data
