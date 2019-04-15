"""
Misc utility functions.
"""

import shlex

from qz7.shell.cmdlist import CmdList

def export_command(env):
    """
    Convert a enviornment dictionary to command list of export commands.
    """

    env = {k: shlex.quote(str(v)) for k, v in env.items()}
    cmds = ["export {}={}".format(k, v) for k, v in env.items()]

    return CmdList(cmds)
