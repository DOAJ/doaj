## DOAJ and AWS

terms:
* AWS is Amazon Web Services - we are billed monthly depending on our usage.
    + IAM is the account manager for AWS. A user has an account on IAM if they have an API key or access to the AWS management console. This applies to machines as well as people.
* S3 - Amazon S3 is a storage service - you can upload and retrieve essentially unlimited data for reasonable cost, and it is generally safer than keeping on our servers
    + bucket - on S3, data is stored in 'buckets' which are like folders on your computer. Access to these can be public or limited via API key / IAM account. Their path can be prefixed by `s3://` - we'll use that notation here.
* SecretsManager - a key / value store which allows our API keys to be securely stored and retrieved to the production machines on deployment. This is accessed via the command line interface for AWS, `awscli`.
* Lambda - serverless code execution. If you want a function to run briefly, you can run it extremely cheaply on Lambda. We use this for monitoring whether our backups are successful.

todo: summary table

### ElasticSearch backups

ElasticSearch has a bucket configured to send its index snapshots to, using the [`cloud-aws`](https://github.com/elastic/elasticsearch-cloud-aws) plugin version 2.7.1 installed on each index node. The requests for the snapshots are issued via background jobs on the background server.

The backup repository name is held in in the app settings as **ELASTIC_SEARCH_SNAPSHOT_REPOSITORY** e.g. for production we use:

    ELASTIC_SEARCH_SNAPSHOT_REPOSITORY = 'doaj-index-backups'

The credentials for this are stored in ElasticSearch's settings, and can be viewed on the index machines. To find all snapshot repositories configured on a server, request that from the `_snapshot` plugin:

```json
cloo@doaj-new-index-1:~$ curl 10.131.99.251:9200/_snapshot
{
  "doaj-index-backups" : {
    "type" : "s3",
    "settings" : {
      "bucket" : "doaj-index-backups",
      "endpoint" : "s3.eu-west-2.amazonaws.com",
      "server_side_encryption" : "true"
    }
  }
}
```

This shows we have the `doaj-index-backups` snapshot repository configured, as the app expects. Furthermore, it backs up to a an Amazon S3 bucket of the same name: `s3://doaj-index-backups`. The credentials for the snapshot plugin are saved in the elasticsearch configuration file in `/etc/elasticsearch/elasticsearch.yml` on the index servers. So at the end of that file we have:

```
# S3 credentials for backups
cloud:
    aws:
        access_key: <ACCESS_KEY>
        secret_key: <SECRET_KEY>
```

This corresponds to IAM user `doaj-index-backups`, which has read and write access to the bucket `s3://doaj-index-backups` only.

#### Optional: credential-gapped vault
In production, in order to limit the damage by accidental or malicious deletion or overwrites, there is a duplicated bucket which stays up-to-date with the snapshots bucket above, but can't be accessed via keys stored on any servers. In order to do this, you need to turn on object versioning and cross-region replication using the AWS console, and configure an additional bucket to replicate the contents.

In production, that bucket is `s3://doaj-vault-index-backups`. Permissions are all handled in the AWS console, so won't be reproduced here.

### Anonymised data export and data dump
todo: we likely don't want these to be the same user.

For development work and the test server the DOAJ has a script to export all of its data to S3 with personally identifiable information scrambled. These are exported to a bucket using the following app settings:

    STORE_ANON_DATA_CONTAINER = "doaj-anon-data"

    STORE_S3_SCOPES = {
        "anon_data" : {
            "aws_access_key_id" : "<ACCESS_KEY>",
            "aws_secret_access_key" : "<SECRET_KEY>"
        }
    }

These correspond to the IAM user **doaj-s3-client**, which has all read / write permissions on buckets `s3://doaj-anon-data` and `s3://doaj-data-dump`. Developers have AWS roles to download these resources, which give them read-only access to the anonymised data bucket, as does the test server - `steve-doaj-anon`, `test-doaj-anon` etc.

### app.cfg secrets file

When the production site is installed via the `deploy.sh` script, the application *secrets* are automatically downloaded from [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) to the project directory on the server. This keeps the public open source code and the sensitive secret credentials separate and securely stored. Its use in the installation script is via the AWS Command Line Interface on the production server:

```
if [ "$ENV" = 'production' ]
then
    aws --profile doaj-app secretsmanager get-secret-value --secret-id doaj/app-credentials | cut -f4 | base64 -d > app.cfg
elif [ "$ENV" = 'test' ]
then
    aws --profile doaj-test secretsmanager get-secret-value --secret-id doaj/test-credentials | cut -f4 | base64 -d > app.cfg
fi
```

These require the IAM users **doaj-apps* and **doaj-test** - these just have permission to download the individual files above. These profiles are stored in `~/.aws/config` and `~/aws/credentials`:

**~/.aws/config**

    [profile doaj-app]
    output = text
    region = eu-west-2


**~/.aws/credentials**

    [doaj-app]
    aws_access_key_id = <ACCESS_KEY>
    aws_secret_access_key = <SECRET_KEY>

In order to **update** the files (e.g. if you've downloaded it to a local file called `app.cfg`), you need to use the **doaj-apps-upload** profile.

    aws --profile doaj-app-upload secretsmanager put-secret-value --secret-id doaj/app-credentials --secret-binary file://app.cfg

Note: when decoding on a mac with `base64`, you need to change the flag from `-d` to `-D`.

The creation syntax is a little different. See the example below.

    aws --profile doaj-app-upload secretsmanager create-secret --name doaj/app-credentials --description "app.cfg for live app servers" --secret-binary file://app.cfg

### AWS Lambda

We use a Lambda function to check our index backup snapshot has occurred correctly every morning. That way it's completely separate from our production infrastructure. It's configured via the online interface to run at 1200h daily. The Lambda function has permissions to access the AWS buckets via an IAM role, and it has its own secrets in Secrets Manager to store email credentials when alerting us if a backup hasn't occurred.

### Logs and Misc backups.

Sysadmins periodically upload old logs to S3, such as nginx logs for analysis, and journal / article histories. By convention we prefix these buckets with `doaj-` so for example we currently have `s3://doaj-misc-backups` containing old web server logs.

### S3FS & Buckets pre-2019

Until the Jan 2019 hardware reconfiguration, S3FS was used to synchronise the filesystems between the app server and the background server. Failed file uploads, the application cache, and journal histories remain in the bucket `s3://doaj-sync-production`. In addition during the reconfiguration, we started using a new index backup bucket - the old one is `s3//doaj-es-backups` (and `s3://doaj-vault-es-backups`). Also from the legacy system: `s3://doaj-duplicity` and `s3://doaj-letsencrypt`, both used to store encrypted backups of system configuration. These can be deleted when the old infrastructure snapshots are removed permanently.
