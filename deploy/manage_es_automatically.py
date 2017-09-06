#!/usr/bin/env python

import sys
import subprocess
from datetime import datetime

from pid.decorator import pidfile
import argparse
import requests

from portality.core import app


DEFAULT_MAX_HEAP_ALLOWED_PERCENT = 90


class RollbackException(Exception):
    pass


# TODO consider backoff/retrying operations via an error handler that's a decorator

def get_nodes_available():
    # TODO backoff / retry on failure
    r = requests.get("{}/_cluster/state/nodes".format(app.config['ELASTIC_SEARCH_HOST']))
    node_info = r.json()
    return node_info['nodes']


def get_mem_used(node_id):
    # TODO backoff / retry on failure
    r = requests.get(
        "{es_target}/_nodes/{node_id}/stats/jvm".format(
            es_target=app.config['ELASTIC_SEARCH_HOST'], node_id=node_id
        )
    )
    node_stats = r.json()  # TODO handle ValueError
    return node_stats['nodes'][node_id]['jvm']['mem']['heap_used_percent']


def get_mem_use_per_node(node_ids):
    mem_use_per_node = {}
    for node_id in node_ids:
        mem_use_per_node[node_id] = get_mem_used(node_id)
    return mem_use_per_node


def take_node_out_of_upstream_nginx_pool(node_name):
    try:
        subprocess.check_call('cd /etc/nginx/includes && ln -sf index-servers-production-without-{}.conf upstream-index-production.conf'.format(node_name))
        subprocess.check_output('sudo nginx -t && sudo nginx -s reload')
    except subprocess.CalledProcessError as e:
        # TODO log that we're rolling back, including the exception traceback, so that we know which of the above operations failed
        # make sure to log e.returncode and e.output
        reinstate_all_nodes_in_upstream_nginx_pool()
        raise RollbackException


def reinstate_all_nodes_in_upstream_nginx_pool():
    try:
        subprocess.check_call('cd /etc/nginx/includes && ln -sf index-servers-production-all.conf upstream-index-production.conf')
        subprocess.check_output('sudo nginx -t && sudo nginx -s reload')
    except subprocess.CalledProcessError as e:
        # TODO log that we're rolling back, including the exception traceback, so that we know which of the above operations failed
        # make sure to log e.returncode and e.output
        # at this point rollback of nginx configs would have failed - email doajdev@cottagelabs.com
        pass


def allow_shard_allocation(allow):
    allocation = 'all' if allow else 'none'

    # TODO retry on exception a few times
    # TODO retry if not r.ok
    r = requests.put(
        "{es_target}/_cluster/settings".format(es_target=app.config['ELASTIC_SEARCH_HOST']),
        data={
            "transient": {
                "cluster.routing.allocation.enable": allocation
            }
        }
    )


def disable_shard_allocation():
    allow_shard_allocation(False)


def enable_shard_allocation():
    allow_shard_allocation(False)


def restart_es_on_node(node_name):
    pass  # either use subprocess.check_output to ssh `cat /home/repl/ips/{node-name}` -c 'sudo service elasticsearch restart'` or use fabric


def wait_until_no_shards_are_RECOVERING():
    pass


def wait_for_green_cluster_status():
    pass


@pidfile
def main(argv):
    # TODO log start
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--dry-run", action="store_true", default=False,
                        help="Record monitoring and actions to take, but do not actually take any actions")
    parser.add_argument("-m", "--max-heap-allowed-percent", type=int, default=DEFAULT_MAX_HEAP_ALLOWED_PERCENT,
                        help="Maximum % Java heap use allowed on an Elasticsearch node before ES is restarted by this script.")
    args = parser.parse_args(argv)

    # Collect data about the nodes
    nodes = get_nodes_available()
    mem_use_per_node = get_mem_use_per_node(nodes.keys())
    # TODO log the mem_use_per_node dict

    # Taking actions per node
    highest_mem_node_id = max(mem_use_per_node, key=mem_use_per_node.get)
    if mem_use_per_node[highest_mem_node_id] <= args.max_heap_allowed_percent:
        # everything is fine
        # TODO log something
        sys.exit(0)

    try:
        take_node_out_of_upstream_nginx_pool(nodes[highest_mem_node_id]['name'])
    except RollbackException:
        # TODO log something for the failure
        # nothing else to roll back at this point, so exit
        sys.exit(1)

    disable_shard_allocation()

    restart_es_on_node(nodes[highest_mem_node_id]['name'])

    wait_until_no_shards_are_RECOVERING()

    enable_shard_allocation()

    wait_for_green_cluster_status()

    reinstate_all_nodes_in_upstream_nginx_pool()

    # TODO log end and time taken


if __name__ == "__main__":
    main(sys.argv)
