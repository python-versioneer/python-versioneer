import os, sys
from subprocess_helper import run_command

GITS = ["git"]
if sys.platform == "win32":
    GITS = ["git.cmd", "git.exe"]

class Common:
    def command(self, cmd, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.projdir)
        assert not kwargs, kwargs.keys()
        output, rc = run_command([cmd], list(args), workdir, True)
        if output is None:
            self.fail("problem running command %s" % cmd)
        return output

    def git(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.gitdir)
        assert not kwargs, kwargs.keys()
        env = os.environ.copy()
        env["EMAIL"] = "foo@example.com"
        env["GIT_AUTHOR_NAME"] = "foo"
        env["GIT_COMMITTER_NAME"] = "foo"
        output, rc = run_command(GITS, args=list(args), cwd=workdir,
                                 verbose=True, env=env)
        if output is None:
            self.fail("problem running git (workdir: %s)" % workdir)
        return output

    def python(self, *args, **kwargs):
        workdir = kwargs.pop("workdir", self.projdir)
        exe = kwargs.pop("python", sys.executable)
        assert not kwargs, kwargs.keys()
        output, rc = run_command([exe], list(args), workdir, True)
        if output is None:
            self.fail("problem running python (workdir: %s)" % workdir)
        return output

    def project_file(self, *path):
        return os.path.join(self.projdir, *path)

    def subpath(self, *path):
        return os.path.join(self.testdir, *path)
