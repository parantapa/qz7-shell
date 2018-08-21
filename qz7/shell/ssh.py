"""
Functions to connect to server via ssh.
"""

import os
import time
import threading

import paramiko
import logbook

THLOCAL = threading.local()
DEFAULT_RETRIES = 10

log = logbook.Logger(__name__)

def get_ssh_config():
    """
    Load the ssh config file.
    """

    ssh_config = paramiko.SSHConfig()
    config_fname = os.path.expanduser("~/.ssh/config")
    if os.path.exists(config_fname):
        with open(config_fname) as fobj:
            ssh_config.parse(fobj)
    return ssh_config

def get_connect_config(ssh_config, hostname):
    """
    Get connect config.
    """

    cfg = {}

    user_config = ssh_config.lookup(hostname)
    for k in ('hostname', 'port'):
        if k in user_config:
            cfg[k] = user_config[k]

        if 'user' in user_config:
            cfg['username'] = user_config["user"]

        if 'proxycommand' in user_config:
            cfg['sock'] = paramiko.ProxyCommand(user_config['proxycommand'])

        cfg["timeout"] = 120
        cfg["banner_timeout"] = 120
        cfg["auth_timeout"] = 120

    return cfg

def make_ssh_client(hostname, retries=None):
    """
    Return a connected ssh client.
    """

    ssh_config = get_ssh_config()
    if retries is None:
        retries = DEFAULT_RETRIES

    last_exc = None
    for try_ in range(retries):
        connect_config = get_connect_config(ssh_config, hostname)

        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(**connect_config)
            return client
        except paramiko.ssh_exception.ProxyCommandFailure as exc:
            log.info(f"Error connecting to {hostname} (try {try_}), retrying ...")
            last_exc = exc
            client.close()
            connect_config['sock'].close()
            time.sleep(1)

    if last_exc is not None:
        raise last_exc # pylint: disable=raising-bad-type

def get_ssh_client(hostname, fresh=False, retries=None):
    """
    Get a ssh client from the thread local cache.
    """

    if not hasattr(THLOCAL, "ssh_clients"):
        THLOCAL.ssh_clients = {}

    if fresh:
        if hostname in THLOCAL.ssh_clients:
            THLOCAL.ssh_clients[hostname].close()
            del THLOCAL.ssh_clients[hostname]

    if hostname not in THLOCAL.ssh_clients:
        THLOCAL.ssh_clients[hostname] = make_ssh_client(hostname, retries)

    return THLOCAL.ssh_clients[hostname]
