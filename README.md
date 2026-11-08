# CloudWatch Logs Query with Boto3

A Python script that lists CloudWatch log groups in an AWS account, using Boto3. It runs directly on a Linux server, inside a Python virtual environment.

I built this as a lab to practise safe, read-only API access to AWS from a script. I plan to move it into Docker later.

## What it does

* Connects to AWS with a named profile (`lab`)- (Stores AWS IAM credentials)
* Lists the CloudWatch log groups in one region (`eu-west-2` by default)
* Keeps credentials in `\~/.aws`, never in the code

## Requirements

* An AWS account
* A Linux server (or a Linux VM, or WSL) with terminal access
* Python 3.8 or newer
* `pip` and `venv`

Nothing is installed in AWS. Everything runs on your own machine.

## Project layout

```
.
├── get-log-groups.py
├── .gitignore
└── README.md
```

## Step 1: Create a read-only IAM user

Do not use the root user. Root can do everything, including closing the account. A read-only user can look but cannot change or delete anything, so a leaked key does far less damage.

1. In the AWS Console, open **IAM** and choose **Create user**.
2. Leave console access off. The script uses the API, so it does not need a password.
3. Attach these policies directly:

   * `ReadOnlyAccess`
   * `CloudWatchLogsReadOnlyAccess`
4. Open the new user, go to **Security credentials** and choose **Create access key**.
5. Copy the **Access key ID** and **Secret access key**. The secret is shown once, so save it somewhere safe.

## Step 2: Set up the server

### 1\. Check Python is installed

```bash
python3 --version
```

You need Python 3.8 or newer.

If `venv` or `pip` is missing:

```bash
# Debian or Ubuntu
sudo apt update \&\& sudo apt install -y python3 python3-venv python3-pip

# RHEL, Rocky or Amazon Linux
sudo dnf install -y python3 python3-pip
```

### 2\. Get the project

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 3\. Create and activate virtual environment

```bash
python3 -m venv venv


source venv/bin/activate
```

This keeps Boto3 inside the project folder, so it does not clash with other Python packages on the server.

### 4\. Install the packages

```bash
pip install boto3 awscli
```

* `boto3` is the Python library the script uses to call AWS.
* `awscli` gives you the `aws` command. Boto3 does not need it, but it gives you `aws configure` and quick checks like `aws sts get-caller-identity`.

You can also keep Boto3 in a `requirements.txt` and run `pip install -r requirements.txt`.

### 5\. Save your credentials

```bash
aws configure --profile lab
```

It asks four things:

|Prompt|Value|
|-|-|
|Access key ID|From Step 1|
|Secret access key|From Step 1|
|Default region|`eu-west-2` (London)|
|Output format|`json`|

This writes two files in your home folder:

* `\~/.aws/credentials` for the keys
* `\~/.aws/config` for the region and output format

Boto3 reads these automatically, so you never put keys in your code.

Lock the folder down so only your user can read it:

```bash
chmod 700 \~/.aws
chmod 600 \~/.aws/credentials \~/.aws/config
```

CloudWatch Logs are per region. If you pick the wrong region, you will see no log groups.

### 6\. Test the connection

```bash
aws sts get-caller-identity --profile lab
```

STS is the "who am I?" service. If it returns your account number and user name, the keys work. If it fails, fix the keys or region first. There is no point going further until this passes.

## Step 3: Run script

With the virtual environment active, run this from the project folder:

```bash
python3 get-log-groups.py
```

Next time you log in, activate the environment again first:

```bash
source venv/bin/activate
```

## Common problems

|Error|Likely cause|
|-|-|
|`command not found: pip` or `aws`|The venv is not active, or Python is not on your PATH. Try `python3 -m pip install boto3 awscli`.|
|`NoCredentialsError`|Wrong profile name, or you did not run `aws configure`.|
|`AccessDenied`|The policy is not attached to the IAM user.|
|Empty results|Wrong region, or there is simply nothing there.|
|`No module named venv`|Install `python3-venv` (see Step 2, part 1).|

## Security notes

* Never commit access keys to Git. Keys in code often end up on GitHub.
* Add a `.gitignore` with at least `venv/` and `\_\_pycache\_\_/`.
* Keep the IAM user read-only.
* Delete or rotate the access key when the lab is finished.

## What I learned

Credentials should live outside the code. A named profile keeps the script simple and lets me switch between accounts without mixing them up.

## Next steps

* Print just the log group names, and handle more than 50 groups with a paginator
* Query log events with `filter\_log\_events`
* Move the whole thing into Docker

