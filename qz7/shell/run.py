"""
Helper functions to execute shell commands locally and via ssh.
"""
# pylint: disable=too-many-arguments

import sys
import shlex
from functools import partial
from subprocess import run
from concurrent.futures import ThreadPoolExecutor, as_completed

import logbook
from blessings import Terminal

from qz7.shell.cmdlist import CmdList, ShellCmdList
from qz7.shell.ssh import get_ssh_client

DEFAULT_TERM_WIDTH = 1024
HOSTNAME_COLOR = "bold_cyan"
TERM = None

log = logbook.Logger(__name__)

def set_term(term):
    global TERM
    TERM = term

def get_term():
    global TERM
    if TERM is None:
        TERM = Terminal()
    return TERM

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
        d = dict(self.__dict__)
        del d["stdout"]
        return f"{self.__class__.__name__}({d!r})"

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

    def __repr__(self):
        d = dict(self.__dict__)
        del d["stdout"]
        return f"{self.__class__.__name__}({d!r})"

class RemoteExecError(Exception):
    """
    Raised when an exception occurs when running remote execution.
    """

    def __init__(self, e, hostname):
        super().__init__(str(e))

        self.hostname = hostname

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__!r})"

def do_remote(hostname, cmd, pty, echo_output, capture, check):
    """
    Do the remote execution.
    """

    try:
        term = get_term()

        ssh_client = get_ssh_client(hostname)

        chan = ssh_client.get_transport().open_session()
        if pty:
            if term.width is None:
                term_width = DEFAULT_TERM_WIDTH
            else:
                term_width = term.width
            chan.get_pty(width=term_width)
        chan.exec_command(cmd)
        sout = chan.makefile("rt", -1)

        output = []
        for line in sout:
            if echo_output:
                sys.stdout.write(line)
                sys.stdout.flush()
            if capture:
                output.append(line)
        output = "".join(output)
        returncode = chan.recv_exit_status()
    except Exception as e:
        raise RemoteExecError(e, hostname)

    if check and returncode != 0:
        raise RemoteCalledProcessError(hostname, cmd, returncode, output)

    return RemoteCompletedProcess(hostname, cmd, returncode, output)

def do_remote_serial(hostnames, cmds, pty, echo_output, capture, check):
    """
    Execute the command in a remote shell on remote hosts serially.
    """

    term = get_term()

    outputs = []
    exceptions = []
    for hostname, cmd in zip(hostnames, cmds):
        hostname_str = getattr(term, HOSTNAME_COLOR)(hostname)
        log.info(f"Executing on: {hostname_str}")
        try:
            out = do_remote(hostname, cmd, pty, echo_output, capture, check)
            outputs.append(out)
        except Exception as e: # pylint: disable=broad-except
            log.warn(f"Unexpected exception", exc_info=True)
            exceptions.append(e)

    return outputs, exceptions

def do_remote_parallel(hostnames, cmds, pty, echo_output, capture, check, max_workers):
    """
    Execute the command in a remote shell on remote hosts in parallel.
    """

    term = get_term()

    do_remote_partial = partial(do_remote, pty=pty,
                                echo_output=echo_output, capture=capture,
                                check=check)

    outputs, exceptions = [], []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futs = []
        for hostname, cmd in zip(hostnames, cmds):
            futs.append(executor.submit(do_remote_partial, hostname, cmd))

        for fut in as_completed(futs):
            try:
                out = fut.result()
                hostname_str = getattr(term, HOSTNAME_COLOR)(out.hostname)
                log.info(f"Succefully finished on: {hostname_str}")
                outputs.append(out)
            except (RemoteExecError, RemoteCalledProcessError) as e:
                hostname_str = getattr(term, HOSTNAME_COLOR)(e.hostname)
                log.warn(f"Unexpected exception on: {hostname_str}", exc_info=True)
                exceptions.append(e)
            except Exception as e: # pylint: disable=broad-except
                log.warn(f"Unexpected exception on unknown host", exc_info=True)
                exceptions.append(e)

    return outputs, exceptions

def remote(hostname, cmd, shell="/bin/bash -l -c",
           pty=True, echo_cmd=True, echo_output=None,
           capture=True, check=False, parallel=None, max_workers=None):
    """
    Execute the command in a remote shell.
    """
    # pylint: disable=redefined-argument-from-local

    # Convert the hostnames and cmds to list
    if isinstance(hostname, (list, tuple)):
        hostnames = list(hostname)
    else:
        hostnames = [hostname]
    if isinstance(cmd, (list, tuple)):
        cmds = list(cmd)
    else:
        cmds = [cmd]

    # Valid cases
    # n hostnames n commands
    # n hostnames 1 command
    if len(hostnames) == len(cmds) and len(hostnames) >= 1:
        pass
    elif len(hostnames) > 1 and len(cmds) == 1:
        pass
    else:
        raise ValueError("Invalid # hostname x # cmd combination")

    # Make cmds same length as hostnames
    if len(cmds) == 1 and len(hostnames) > 1:
        cmds = cmds * len(hostnames)

    # Fill out the defaults
    if parallel is None:
        parallel = len(hostnames) > 1
    if echo_output is None:
        echo_output = not parallel

    ncmds = []
    for cmd in cmds:
        if isinstance(cmd, CmdList):
            cmd = ShellCmdList(cmd, shell=shell)
        elif isinstance(cmd, ShellCmdList) and not cmd.final:
            cmd = ShellCmdList(cmd, shell=shell)

        ncmds.append(cmd)
    cmds = ncmds

    if echo_cmd:
        if parallel:
            log.info("Executing in parallel on {0} host(s)\n{1}", len(hostnames), cmds[0])
        else:
            log.info("Executing in serial on {0} host(s)\n{1}", len(hostnames), cmds[0])

    ncmds = []
    for cmd in cmds:
        if hasattr(cmd, "execfmt"):
            cmd = cmd.execfmt()
        ncmds.append(cmd)
    cmds = ncmds

    if parallel:
        return do_remote_parallel(hostnames, cmds, pty, echo_output, capture, check, max_workers)
    return do_remote_serial(hostnames, cmds, pty, echo_output, capture, check)

def local(cmd, *args, **kwargs):
    """
    Execute the command in a locally.
    """

    shell = kwargs.pop("shell", "/bin/bash -c")
    echo_cmd = kwargs.pop("echo_cmd", True)

    if isinstance(cmd, CmdList):
        cmd = ShellCmdList(cmd, shell=shell)
    elif isinstance(cmd, ShellCmdList) and not cmd.final:
        cmd = ShellCmdList(cmd, shell=shell)

    if echo_cmd:
        log.info(f"Executing\n{cmd}")

    if hasattr(cmd, "execfmt"):
        cmd = cmd.execfmt()
    cmd = shlex.split(cmd)

    return run(cmd, *args, **kwargs)
