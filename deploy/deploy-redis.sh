#!/usr/bin/env bash
THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

sudo apt-get update -q -y
sudo apt-get -q -y install curl linux-image-extra-$(uname -r) linux-image-extra-virtual apt-transport-https ca-certificates redis-tools
curl -fsSL https://yum.dockerproject.org/gpg | sudo apt-key add -
# TODO could use apt-key fingerprint to verify the key had fingerprint 58118E89F3A912897C070ADBF76221572C52609D
sudo add-apt-repository "deb https://apt.dockerproject.org/repo/ ubuntu-$(lsb_release -cs) main"
sudo apt-get update -q -y
sudo apt-get -q -y install docker-engine=1.12.3-0~trusty
echo
echo "Docker version should be displayed below if successfully installed"
docker -v
# might have to be done manually - script terminates at some point after the echoes below, either after adding the group, adding *to* the group, or the newgrp command
echo
echo "Setting up Docker to be used without sudo"
sudo groupadd docker
sudo gpasswd -a ${USER} docker
#newgrp docker  # TODO automate this. Calling newgrp will start a subshell and not normally execute commands after this line. If we need to run commands under a different group (as we do - everything below this line), then use redirection, see http://unix.stackexchange.com/q/18897/160468 .
echo
echo "Installing Docker Compose, version information should be displayed below"
curl -L https://github.com/docker/compose/releases/download/1.9.0/docker-compose-`uname -s`-`uname -m` | sudo tee /usr/local/bin/docker-compose > /dev/null && sudo chmod a+x /usr/local/bin/docker-compose
docker-compose --version

# Restart redis
/home/cloo/repl/$ENV/doaj/src/doaj/deploy/restart-redis.sh $ENV
