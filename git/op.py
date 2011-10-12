import os
import urllib
import tempfile
import subprocess

def clone(repo_url):
    tmpd = tempfile.mkdtemp()
    clone_proc = subprocess.Popen(['git', 'clone', repo_url, tmpd], close_fds=True)
    if clone_proc.wait() == 0:
        return tmpd
    return None

def log(tmpd):
    """Get the commits in the following format:
%h ::: %an ::: %aD ::: %s ::: %d
Check the PRETTY FORMATS section in git log help.
"""
    commits = None
    commits_proc = subprocess.Popen(
        ['git', 'log', '--pretty=format:"%h ::: %an ::: %aD ::: %s ::: %d"'],
        stdout=subprocess.PIPE, close_fds=True, cwd=tmpd)

    # XXX: SOME ERROR CHECKING MISSING HERE.
    if commits_proc.wait() == 0:
        # get the parts of the commit into a list
        # XXX: optimize this shit, it's a mess
        commits = [[s.strip("\"").strip() for s in rev.strip().split(":::")] for rev in commits_proc.stdout]
        commits = [(commit[0].strip(), commit[1].strip(),
                    commit[2].strip(), commit[3].strip(),
                    commit[4].strip()) for commit in commits]
    return commits
