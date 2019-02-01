#!/usr/bin/env python

"""
Mount S3FS-FUSE.

Provides a way to put the various arguments in the app configuration, so they don't have to be passed around the command
line. Should also make it far easier for devs who don't have to remember the s3fs CLI syntax.

Since it uses the app config, it's easiest to have it as a Python rather than a bash script.
"""

import subprocess
import sys

from portality.core import app


class S3FSScriptException(Exception):
    pass


def check_permanent_mount(bucket):
    try:
        # we don't actually need grep's output, but this prevents grep from printing it out
        subprocess.check_output('grep "s3fs#{} {}" /etc/fstab'.format(bucket, app.config['S3FS_MOUNT_DIR']), shell=True)
        return True
    except subprocess.CalledProcessError:
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--unmount", action="store_true", help="Unmount, rather than mount (the default action)")
    parser.add_argument("-p", "--permanent", action="store_true", help="Make the mount stick on reboot. Checks /etc/fstab for a relevant entry and adds one if no entries are found.")
    args = parser.parse_args()

    if args.unmount and args.permanent:
        raise S3FSScriptException("You can't specify both --unmount and --permanent. --permanent only makes sense when mounting.")

    # print args
    if 'S3FS_BUCKET' not in app.config:
        raise S3FSScriptException(
"""

--> Ensure S3FS_BUCKET is a defined string in your .cfg files. <--

Acceptable formats are s3://bucket_name and bucket_name.
The test server's bucket is s3://doaj-test-sync, can also be used on development machines to test syncing. Your files will be synced with those of the test server if you use it!
"""
        )
    if 'S3FS_CREDS_PATH' not in app.config:
        raise S3FSScriptException(
"""

--> Ensure S3FS_CREDS_PATH is defined in your .cfg files. <--

<DOAJ repository root>/.s3fs-credentials is conventional and .gitignore-d.
The file you're pointing to must conform to the format "AWS ACCESS KEY:AWS SECRET KEY" on 1 line.
"""
        )
    if 'S3FS_MOUNT_DIR' not in app.config:
        raise S3FSScriptException(
"""

--> Ensure S3FS_MOUNT_DIR is defined in your .cfg files. <--

**NOTE it's recommended you put this outside the DOAJ git repostitory, since 'git status' and other everyday commands which recurse through the directory tree may become significantly slower if S3FS is mounted.
Please use an empty directory as the mount target.
"""
        )

    bucket = app.config['S3FS_BUCKET']
    if bucket.startswith('s3://'):
        bucket = bucket[5:]

    credentials_arg = 'passwd_file={}'.format(app.config['S3FS_CREDS_PATH'])

    permanently_mounted = check_permanent_mount(bucket)

    if args.permanent:
        if permanently_mounted:
            print "S3FS permanent mount for bucket {} already exists, not doing anything.\n" \
                  'If you think the /etc/fstab entry is wrong, remove it manually and rerun this script with --permanent.'
            sys.exit(0)

        fstab_entry = 's3fs#{} {} fuse _netdev,allow_other,{},url=https://s3.amazonaws.com 0 0'.format(bucket, app.config['S3FS_MOUNT_DIR'], credentials_arg)
        if '"' in fstab_entry:
            raise S3FSScriptException("You can't have \" (double quotes) in any of the environment variables that control the S3 mount.")
        print
        print 'Setting up permanent mount in /etc/fstab - you may be asked for your sudo password now.'
        print
        subprocess.check_call('echo "{}" | sudo tee -a /etc/fstab'.format(fstab_entry), shell=True)
        print
        print '^ the above entry has been appended to your /etc/fstab'
        permanently_mounted = check_permanent_mount(bucket)

    if args.unmount:
        try:
            subprocess.check_call(["sudo", 'umount', app.config['S3FS_MOUNT_DIR']])
        except subprocess.CalledProcessError:
            print
            print 'Unmounting failed. This can happen if you try to unmount too soon after you mounted. If the error is something like "device busy", wait for 5-10 seconds and rerun the unmount.'
            print
            raise

        print 'S3FS UNmounted bucket {} from directory {} succesfully'.format(bucket, app.config['S3FS_MOUNT_DIR'])
        sys.exit(0)

    # let's mount then
    if permanently_mounted:
        print
        print "Mounting using the permanent mount in /etc/fstab.\n" \
              "If this script completes successfully but you can't use the mountpoint as an S3 file system, " \
              "check your /etc/fstab and compare against your local S3FS_* DOAJ config vars, then report a bug."

        subprocess.check_call(['sudo', 'mount', app.config['S3FS_MOUNT_DIR']])
    else:
        print
        print 'Mounting with temporary mount.'
        subprocess.check_call(["s3fs", bucket, app.config['S3FS_MOUNT_DIR'], '-o', credentials_arg, '-o', 'url=https://s3.amazonaws.com'])

    print 'S3FS mounted bucket {} at directory {} succesfully'.format(bucket, app.config['S3FS_MOUNT_DIR'])
