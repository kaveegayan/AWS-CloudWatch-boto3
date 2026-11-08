# import boto3 lib
import boto3
# direct boto3 to use credentials saved in "profile_name" and aws region
session = boto3.Session(profile_name="lab", region_name="eu-west-2")
# define connection to CloudWatch log service  client "logs" ("ec2"=Ec2, "s3" = S3, "ce" = cost explorer, etc. )
logs = session.client("logs")
# responce from boto3
response = logs.describe_log_groups()
# Print the response
print(response["logGroups"])
