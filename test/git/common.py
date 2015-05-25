import os, sys
from subprocess_helper import run_command

GITS = ["git"]
if sys.platform == "win32":
    GITS = ["git.cmd", "git.exe"]

class Common:
    def command(self, cmd, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.subpath("demoapp"))
        assert not kwargs, kwargs.keys()
        output = run_command([cmd], list(args), workdir, True)
        if output is None:
            self.fail("problem running command %s" % cmd)
        return output
    def git(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.subpath("demoapp"))
        assert not kwargs, kwargs.keys()
        output = run_command(GITS, list(args), workdir, True)
        if output is None:
            self.fail("problem running git")
        return output
    def python(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.subpath("demoapp"))
        exe = kwargs.pop("python", sys.executable)
        assert not kwargs, kwargs.keys()
        output = run_command([exe], list(args), workdir, True)
        if output is None:
            self.fail("problem running python")
        return output
    def subpath(self, *path):
        return os.path.join(self.testdir, *path)
