"""
Misc utility functions.
"""

import shlex

from qz7.shell.cmdlist import ShellCmdList, CmdList

def screenlog_command(cmd, screen_name, logfname="/dev/null"):
    """
    Wrap the given cmd in a detached screen session.
    """

    screen_name = shlex.quote(str(screen_name))
    logfname = shlex.quote(str(logfname))

    shell = f"screenlog {logfname} -dmS {screen_name} /bin/bash -c"
    cmd = ShellCmdList(cmd, shell, final=False)
    return cmd

def export_command(env):
    """
    Convert a enviornment dictionary to command list of export commands.
    """

    env = {k: shlex.quote(str(v)) for k, v in env.items()}
    cmds = ["export {}={}".format(k, v) for k, v in env.items()]

    return CmdList(cmds)
