"""
Helper functions to execute shell commands locally and via ssh.
"""
# pylint: disable=too-many-arguments

import sys
import shlex
from subprocess import run

import logbook

from qz7.shell.cmdlist import command, CmdList
from qz7.shell.ssh import get_ssh_client

DEFAULT_TERM_WIDTH = 1024

log = logbook.Logger(__name__)

def set_default_term_width(width):
    global DEFAULT_TERM_WIDTH
    DEFAULT_TERM_WIDTH = width

class RemoteCompletedProcess:
    """
    Remote completed process.
    """

    def __init__(self, hostname, args, returncode, stdout):
        self.hostname = hostname
        self.args = args
        self.returncode = returncode
        self.stdout = stdout

    def __repr__(self):
        return f"RemoteCompletedProcess(hostname={self.hostname!r}, args={self.args!r} returncode={self.returncode})"

class RemoteCalledProcessError(Exception):
    """
    Raised when the remote process raises with non zero exit status.
    """

    def __init__(self, hostname, cmd, returncode, stdout):
        super().__init__(f"Remote command failed with exit code {returncode}")

        self.hostname = hostname
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout

def local(cmd, *args, **kwargs):
    """
    Execute the command in a locally.
    """

    if isinstance(cmd, CmdList):
        shell = kwargs.pop("shell", "/bin/bash -c")

        cmd = cmd.tocmd(shell=shell)
        cmd = shlex.split(cmd)

    if __debug__:
        log.debug(f"local: {cmd!r}")

    return run(cmd, *args, **kwargs)

def remote(hostname, cmd, shell="/bin/bash -l -c",
           pty=True, echo=True, capture=True, check=False,
           term_width=None):
    """
    Execute the command in a remote shell.
    """

    if isinstance(cmd, CmdList):
        cmd = cmd.tocmd(shell=shell)

    if __debug__:
        log.debug(f"{hostname}: {cmd!r}")

    ssh_client = get_ssh_client(hostname)

    chan = ssh_client.get_transport().open_session()
    if pty:
        if term_width is None:
            term_width = DEFAULT_TERM_WIDTH
        chan.get_pty(width=term_width)
    chan.exec_command(cmd)
    sout = chan.makefile("rt", -1)

    output = []
    for line in sout:
        if echo:
            sys.stdout.write(line)
            sys.stdout.flush()
        if capture:
            output.append(line)
    output = "".join(output)
    returncode = chan.recv_exit_status()

    if check and returncode != 0:
        raise RemoteCalledProcessError(hostname, cmd, returncode, output)

    return RemoteCompletedProcess(hostname, cmd, returncode, output)
