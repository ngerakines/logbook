import os
import time
import tempfile
import subprocess

def clone(repo_url):
    tmpd = tempfile.mkdtemp()
    clone_proc = subprocess.Popen(['git', 'clone', repo_url, tmpd], close_fds=True)
    if clone_proc.wait() == 0:
        return tmpd
    return None

def log(tmpd, filter_opt=None, filter_s=None):
    """Get the commits in the following format:
%h ::: %an ::: %aD ::: %s ::: %d
Check the PRETTY FORMATS section in git log help.
"""
    commits = None
    git_cmd = ['git', '--no-pager', 'log',
               '--pretty=format:"%h ::: %an ::: %aD ::: %s ::: %d"']

    if filter_opt is not None and filter_s is not None:
        git_cmd.append('%s=%s' % (filter_opt, filter_s))

    commits_proc = subprocess.Popen(
        git_cmd, stdout=subprocess.PIPE, close_fds=True, cwd=tmpd)

    stdout = commits_proc.communicate()[0]

    # get the parts of the commit into a list
    # XXX: optimize this shit, it's a mess
    commits = [[s.strip("\"").strip() for s in rev.strip().split(":::")] for rev in stdout.split("\n")]
    commits = [(commit[0].strip(), commit[1].strip(),
                commit[2].strip(), commit[3].strip(),
                commit[4].strip()) for commit in commits]
    return commits
