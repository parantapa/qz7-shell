"""
Create and manipluate cmd lists.
"""

import shlex

class CmdList:
    """
    A list of shell commands.
    """

    def __init__(self, cmd=None):
        if cmd is None:
            self.parts = ()
        elif isinstance(cmd, str):
            self.parts = (cmd,)
        elif isinstance(cmd, CmdList):
            self.parts = cmd.parts
        else:
            raise ValueError("Can create CmdList from another CmdList or a string")

    def __repr__(self):
        return f"CmdList({self.parts!r})"

    def __add__(self, other):
        if isinstance(other, CmdList):
            ret = CmdList(self)
            ret.parts += other.parts
            return ret
        elif isinstance(other, str):
            ret = CmdList(self)
            ret.parts += (other,)
            return ret

        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, CmdList):
            ret = CmdList(other)
            ret.parts += self.parts
            return ret
        elif isinstance(other, str):
            ret = CmdList(other)
            ret.parts += self.parts
            return ret

        return NotImplemented

    def tocmd(self, shell="/bin/bash -c", sep="&&"):
        """
        Convert the command list to a command that can be executed.
        """

        if not self.parts:
            raise ValueError("Can't convert an empty CmdList to a command")

        sep = sep.strip()
        sep = f" {sep} "

        parts = sep.join(self.parts)
        parts = shlex.quote(parts)

        cmd = f"{shell} {parts}"
        return cmd

def command(*args, quote=None):
    """
    Create the cmd from args.
    """

    if not args:
        return CmdList()

    if len(args) == 1:
        if quote is None:
            quote = False
        args = args[0]
        if quote:
            args = shlex.quote(str(args))
    else:
        if quote is None:
            quote = True
        if quote:
            args = map(str, args)
            args = map(shlex.quote, args)
        args = " ".join(args)

    return CmdList(args)
