import os, sys
from subprocess_helper import run_command

GITS = ["git"]
if sys.platform == "win32":
    GITS = ["git.cmd", "git.exe"]

class Common:
    def command(self, cmd, *args, workdir=None, env=None):
        if workdir is None:
            workdir = self.projdir
        output, rc = run_command([cmd], list(args), workdir, True, env=env)
        if output is None:
            self.fail("problem running command %s" % cmd)
        return output

    def git(self, *args, workdir=None):
        if workdir is None:
            workdir = self.gitdir
        env = os.environ.copy()
        env["EMAIL"] = "foo@example.com"
        env["GIT_AUTHOR_NAME"] = "foo"
        env["GIT_COMMITTER_NAME"] = "foo"
        output, rc = run_command(GITS, args=list(args), cwd=workdir,
                                 verbose=True, env=env)
        if output is None:
            self.fail("problem running git (workdir: %s)" % workdir)
        return output

    def python(self, *args, workdir=None, exe=sys.executable, env=None):
        if workdir is None:
            workdir = self.projdir
        output, rc = run_command([exe], list(args), workdir, True, env=env)
        if output is None:
            self.fail("problem running python (workdir: %s)" % workdir)
        return output

    def project_file(self, *path):
        return os.path.join(self.projdir, *path)

    def subpath(self, *path):
        return os.path.join(self.testdir, *path)
