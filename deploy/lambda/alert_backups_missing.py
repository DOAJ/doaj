#!/usr/bin/env python3
""" Steven Eardley 2020-02-07 for DOAJ - uploaded manually (todo: we should upload this in the release script) """

import boto3
import botocore
import json
from datetime import datetime, timezone, timedelta

s3 = boto3.client('s3')

# Check the doaj elasticsearch snapshot bucket has been updated today (should happen daily at 0600 via background job)
buckets = ['doaj-index-backups']

# Check the doaj-nginx logs bucket has been updated today (should happen daily at 0630 via cron logrotate)
buckets += ['doaj-nginx-logs']


def lambda_handler(event, context):
    """ The main function executed by Lambda"""

    summary = {'success': [], 'fail': []}
    for b in buckets:

        # First check the bucket actually exists
        try:
            s3.head_bucket(Bucket=b)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                send_alert_email(b, last_mod=None)

        # Then check the expected entry exists in the bucket's objects.
        files = list_bucket_keys(bucket_name=b)
        old_to_new = sorted(files, key=lambda f: f['LastModified'])
        newest = old_to_new[-1]

        # If the newest file is older than 1 day old, our backups are not up to date.
        if datetime.now(timezone.utc) - newest['LastModified'] > timedelta(days=1):
            # Send an alert
            send_alert_email(bucket=b, last_mod=newest['LastModified'])
            summary['fail'].append(b)
        else:
            summary['success'].append(b)

    print(summary)  # For the CloudWatch logs
    return str(summary)


def list_bucket_keys(bucket_name):
    """ Read all object metadata from an S3 bucket """
    all_keys = []
    r = s3.list_objects_v2(Bucket=bucket_name)
    while r.get('Contents', None):
        all_keys += r['Contents']

        if r.get('NextContinuationToken', None):
            r = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=r['NextContinuationToken'])
        else:
            break
    return all_keys


def send_alert_email(bucket, last_mod):
    """ Use the mailgun API key stored in AWS Secrets Manager to email us errors """

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='eu-west-1',
        endpoint_url='https://secretsmanager.eu-west-1.amazonaws.com'
    )

    try:
        resp = client.get_secret_value(SecretId='doaj-error-email')
    except botocore.exceptions.ClientError as e:
        raise e
    else:
        if 'SecretString' in resp:
            credentials = json.loads(resp['SecretString'])

            if last_mod is None:
                msg = 'AWS backup error: bucket {b} is missing.'.format(b=bucket)
            else:
                msg = 'AWS backup error: bucket {b} has not been updated today - it was last modified on {t}.' \
                      '\nYou may wish to check the corresponding logs.'.format(b=bucket, t=last_mod.strftime(
                    '%Y-%m-%dT%H:%M:%SZ'))

            r = botocore.vendored.requests.post('https://api.mailgun.net/v3/doaj.org/messages',
                                                auth=('api', credentials.get('ERROR_MAIL_API_KEY', '')),
                                                data={'from': 'error@doaj.org',
                                                      'to': [credentials.get('ERROR_LOGGING_EMAIL',
                                                                             'sysadmin@cottagelabs.com')],
                                                      'subject': 'DOAJ backups error - AWS S3',
                                                      'text': msg})

            if r.status_code != 200:
                raise Exception('Error sending email: status {0}'.format(r.status_code))
        else:
            raise Exception('Could not send alert email - no usable credentials supplied.')
