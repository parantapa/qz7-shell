"""
Misc utility functions.
"""

import shlex

from qz7.shell.cmdlist import ShellCmdList

def screenlog_command(cmd, screen_name, logfname="/dev/null"):
    """
    Wrap the given cmd in a detached screen session.
    """

    screen_name = shlex.quote(str(screen_name))
    logfname = shlex.quote(str(logfname))

    shell = f"screenlog {logfname} -dmS {screen_name} /bin/bash -c"
    cmd = ShellCmdList(cmd, shell, final=False)
    return cmd
