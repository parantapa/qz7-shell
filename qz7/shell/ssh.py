"""
Functions to connect to server via ssh.
"""

import os
import paramiko
import threading

THLOCAL = threading.local()

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

    return cfg

def make_ssh_client(hostname):
    """
    Return a connected ssh client.
    """

    ssh_config = get_ssh_config()
    connect_config = get_connect_config(ssh_config, hostname)

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(**connect_config)

    return client

def get_ssh_client(hostname):
    """
    Get a ssh client from the thread local cache.
    """

    if not hasattr(THLOCAL, "ssh_clients"):
        THLOCAL.ssh_clients = {}

    if hostname not in THLOCAL.ssh_clients:
        THLOCAL.ssh_clients[hostname] = make_ssh_client(hostname)

    return THLOCAL.ssh_clients[hostname]
