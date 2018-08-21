"""
Create and manipluate cmd lists.
"""

import shlex

class CmdList:
    """
    A list of shell commands.
    """

    def __init__(self, cmd, sep="&&"):
        if isinstance(cmd, str):
            self.parts = (cmd,)
            self.sep = sep
        elif isinstance(cmd, CmdList):
            self.parts = cmd.parts
            self.sep = cmd.sep
        elif isinstance(cmd, (list, tuple)):
            if not cmd:
                raise ValueError("Can't create CmdList from empty list or tuple")
            if not all(isinstance(c, str) for c in cmd):
                raise ValueError("Not all elements of list are strings")
            self.parts = tuple(cmd)
            self.sep = sep
        else:
            raise ValueError("Invalid type for cmd")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__!r})"

    def tostr(self, level=0, indent=2):
        """
        Convert the command list to a pretty string.
        """

        sep = self.sep.strip()
        sep = f" {sep} \\\n"

        indent_str = " " * (level * indent)
        parts = [indent_str + part for part in self.parts]
        parts = sep.join(parts)
        return parts

    def __str__(self):
        return self.tostr()

    def __add__(self, other):
        if isinstance(other, CmdList):
            ret = CmdList(self)
            ret.parts += other.parts
            return ret
        if isinstance(other, str):
            ret = CmdList(self)
            ret.parts += (other,)
            return ret

        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, CmdList):
            ret = CmdList(other)
            ret.parts += self.parts
            return ret
        if isinstance(other, str):
            ret = CmdList(other)
            ret.parts += self.parts
            return ret

        return NotImplemented

    def execfmt(self):
        """
        Convert the command list to executable format.
        """

        sep = " {0} ".format(self.sep.strip())
        return sep.join(self.parts)

class ShellCmdList:
    def __init__(self, cmdlist, shell="/bin/bash -c", final=True):
        self.cmdlist = cmdlist
        self.shell = shell
        self.final = final

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__!r})"

    def tostr(self, level=0, indent=2):
        """
        Convert the shell command to string.
        """

        indent_str = " " * (level * indent)
        cmdlist_str = self.cmdlist.tostr(level=level+1, indent=indent)
        return f"{indent_str}{self.shell}\n{cmdlist_str}"

    def __str__(self):
        return self.tostr()

    def execfmt(self):
        """
        Convert the shell command list to executable format.
        """

        cmdlist = self.cmdlist.execfmt()
        cmdlist = shlex.quote(cmdlist)
        return f"{self.shell} {cmdlist}"

def command(cmds, *args, **kwargs):
    """
    Create a CmdList from the format string cmds.
    """

    args = [shlex.quote(str(x)) for x in args]
    kwargs = {k: shlex.quote(str(v)) for k, v in kwargs.items()}

    # Check for newlines
    for arg in args:
        if "\n" in arg:
            raise ValueError("Passing raw newlines via arguments is not supported")
    for v in kwargs.values():
        if "\n" in v:
            raise ValueError("Passing raw newlines via arguments is not supported")

    cmds = cmds.format(*args, **kwargs)
    cmds = cmds.split("\n")
    cmds = [cmd.strip() for cmd in cmds]
    cmds = [cmd for cmd in cmds if cmd and not cmd.startswith("#")]

    return CmdList(cmds)
