#!/usr/bin/env bash

echo "Installing S3FS-FUSE system software requirements"
sudo apt-get update -q -y
sudo apt-get -q -y install automake autotools-dev g++ git libcurl4-gnutls-dev libfuse-dev libssl-dev libxml2-dev make pkg-config

S3FS_GIT_REPO_PATH=/tmp/s3fs-fuse
echo
echo "Compiling S3FS-FUSE"
echo "It is OK to see \"fatal: destination path '$S3FS_GIT_REPO_PATH' already exists and is not an empty directory\". This script deals with it."
echo

function update_git_repo {
    cd $S3FS_GIT_REPO_PATH
    git checkout master
    git pull
    git status
}

git clone https://github.com/s3fs-fuse/s3fs-fuse.git $S3FS_GIT_REPO_PATH || update_git_repo
cd $S3FS_GIT_REPO_PATH
./autogen.sh
./configure
make
echo
echo "Attempting to install S3FS-FUSE. This uses sudo so you may be asked for your password now."
echo
sudo make install
echo
echo "Installed S3FS-FUSE. Use the deploy/mount_s3fs.py script in this repo for easier mounting. See s3fs -h if you need to use the software directly."
echo
s3fs --version