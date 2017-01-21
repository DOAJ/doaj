#!/usr/bin/env bash
THIS_SCRIPT=`basename "$0"`
[ $# -ne 1 ] && echo "Call this script as $THIS_SCRIPT <environment: [production, staging, test, harvester]>" && exit 1

ENV=$1

sudo apt-get update -q -y
sudo apt-get -q -y install curl linux-image-extra-$(uname -r) linux-image-extra-virtual apt-transport-https ca-certificates
curl -fsSL https://yum.dockerproject.org/gpg | sudo apt-key add -
# TODO could use apt-key fingerprint to verify the key had fingerprint 58118E89F3A912897C070ADBF76221572C52609D
sudo add-apt-repository "deb https://apt.dockerproject.org/repo/ ubuntu-$(lsb_release -cs) main"
sudo apt-get update -q -y
sudo apt-get -q -y install docker-engine=1.12.3-0~trusty
echo
echo "Docker version should be displayed below if successfully installed"
docker -v
echo
echo "Setting up Docker to be used without sudo"
sudo groupadd docker
sudo gpasswd -a ${USER} docker
newgrp docker
echo
echo "Installing Docker Compose, version information should be displayed below"
curl -L https://github.com/docker/compose/releases/download/1.9.0/docker-compose-`uname -s`-`uname -m` | sudo tee /usr/local/bin/docker-compose > /dev/null && sudo chmod a+x /usr/local/bin/docker-compose
docker-compose --version

cd /home/cloo/repl/$ENV/doaj/src/doaj/docker
docker-compose down || true  # it's fine to fail to bring down redis if it is not started yet
# for the line below:
# --build to pick up docker/redis/Dockerfile changes
# --remove-orphans to remove all containers that are not defined in the docker/docker-compose.yml (allows us to change service names and configuration just by editing that file and deploying
# -d for detached mode rather than run in foreground
docker-compose up --build --remove-orphans -d

aip=$(cat /home/cloo/repl/ips/${ENV})

. /home/cloo/repl/$ENV/doaj/src/doaj/app.cfg > /dev/null 2>&1

DEFAULT_REDIS_PORT=6379

if [ -z "$HUEY_REDIS_PORT" ]; then
    HUEY_REDIS_PORT=${DEFAULT_REDIS_PORT}
    echo "HUEY_REDIS_PORT not set, defaulting to $DEFAULT_REDIS_PORT"
else
    echo "HUEY_REDIS_PORT read in from app.cfg: '$DEFAULT_REDIS_PORT'"
fi

echo "Opening firewall port for Redis"
echo "sudo ufw allow in on eth1 from $aip to any port $HUEY_REDIS_PORT"
sudo ufw allow in on eth1 from ${aip} to any port ${HUEY_REDIS_PORT}
