import os, sys
from subprocess_helper import run_command

GITS = ["git"]
if sys.platform == "win32":
    GITS = ["git.cmd", "git.exe"]

class Common:
    def command(self, cmd, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.gitpath())
        assert not kwargs, kwargs.keys()
        output = run_command([cmd], list(args), workdir, True)
        if output is None:
            self.fail("problem running command %s" % cmd)
        return output
    def git(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.gitpath())
        assert not kwargs, kwargs.keys()
        env = os.environ.copy()
        env["EMAIL"] = "foo@example.com"
        env["GIT_AUTHOR_NAME"] = "foo"
        env["GIT_COMMITTER_NAME"] = "foo"
        output = run_command(GITS, args=list(args), cwd=workdir, verbose=True,
                             env=env)
        if output is None:
            self.fail("problem running git (workdir: %s)" % workdir)
        return output
    def python(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.gitpath())
        exe = kwargs.pop("python", sys.executable)
        assert not kwargs, kwargs.keys()
        output = run_command([exe], list(args), workdir, True)
        if output is None:
            self.fail("problem running python (workdir: %s)" % workdir)
        return output
    def subpath(self, path, base_dir = ""):
        return os.path.join(self.testdir, base_dir, path)
    def projpath(self, alt_base = None):
        base = alt_base or self.gitpath()
        return os.path.join(base, self.projdir)
    def gitpath(self, alt_base = None):
        base = alt_base or self.testdir
        return os.path.join(base, self.gitdir)
