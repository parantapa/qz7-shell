"""
Helper functions to execute shell commands locally and via ssh.
"""

from qz7.shell.cmdlist import command_format

# NOTE: Use of command instead of command_format is deprecated
command = command_format

# from qz7.shell.run import remote, remote_m, local, set_term
