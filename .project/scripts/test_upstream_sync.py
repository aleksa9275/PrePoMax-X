"""Safety tests using disposable local Git repositories; no network or real fork writes."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("upstream-sync.py").resolve()
OFFICIAL = "https://gitlab.com/MatejB/PrePoMax.git"


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="prepomax-sync-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "upstream.git"
        self.seed = self.root / "seed"
        self.local = self.root / "fork"
        self.git(self.root, "init", "--bare", "--initial-branch=trunk", str(self.remote))
        self.git(self.root, "clone", str(self.remote), str(self.seed))
        self.configure(self.seed)
        self.commit(self.seed, "baseline")
        self.git(self.seed, "push", "origin", "trunk")
        self.git(self.root, "clone", str(self.remote), str(self.local))
        self.configure(self.local)
        self.git(self.local, "remote", "set-url", "origin", "https://gitlab.com/example/fork.git")
        self.git(self.local, "remote", "add", "upstream", OFFICIAL)
        # Exact official URL is redirected to a local fixture only within this temporary repo.
        self.git(self.local, "config", "url." + str(self.remote) + ".insteadOf", OFFICIAL)
        self.git(self.local, "branch", "x/main")
        self.git(self.local, "switch", "-c", "feature/audit")
        self.original = self.git(self.local, "rev-parse", "trunk")

    def git(self, cwd, *args):
        return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()

    def configure(self, cwd):
        self.git(cwd, "config", "user.name", "Sync fixture")
        self.git(cwd, "config", "user.email", "fixture@example.invalid")
        self.git(cwd, "config", "commit.gpgsign", "false")

    def commit(self, cwd, content):
        (cwd / "fixture.txt").write_text(content)
        self.git(cwd, "add", "fixture.txt")
        self.git(cwd, "commit", "-m", content)
        return self.git(cwd, "rev-parse", "HEAD")

    def advance(self):
        new = self.commit(self.seed, "upstream update")
        self.git(self.seed, "tag", "release-fixture")
        self.git(self.seed, "push", "origin", "trunk", "--tags")
        return new

    def run_sync(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.local,
                              text=True, capture_output=True)

    def unchanged_development(self):
        self.assertEqual("feature/audit", self.git(self.local, "branch", "--show-current"))
        self.assertEqual(self.original, self.git(self.local, "rev-parse", "x/main"))

    def refused(self, message):
        result = self.run_sync()
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn(message, result.stderr)

    def test_noop(self):
        self.assertEqual(0, self.run_sync().returncode)
        self.unchanged_development()

    def test_fast_forward_detected_default_and_tags(self):
        new = self.advance()
        result = self.run_sync()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(new, self.git(self.local, "rev-parse", "trunk"))
        self.assertEqual(new, self.git(self.local, "rev-parse", "release-fixture"))
        self.unchanged_development()

    def test_dry_run_fetches_but_does_not_update_local(self):
        new = self.advance()
        self.assertEqual(0, self.run_sync("--dry-run").returncode)
        self.assertEqual(self.original, self.git(self.local, "rev-parse", "trunk"))
        self.assertEqual(new, self.git(self.local, "rev-parse", "upstream/trunk"))
        self.unchanged_development()

    def test_untracked_work_is_refused(self):
        (self.local / "user-notes.txt").write_text("do not overwrite")
        self.refused("Working tree is dirty")
        self.assertEqual("do not overwrite", (self.local / "user-notes.txt").read_text())

    def test_tracked_work_is_refused(self):
        (self.local / "fixture.txt").write_text("user work")
        self.refused("Working tree is dirty")
        self.assertEqual("user work", (self.local / "fixture.txt").read_text())

    def test_divergent_or_ahead_mirror_is_refused(self):
        self.git(self.local, "switch", "trunk")
        local_commit = self.commit(self.local, "fork-only change")
        self.git(self.local, "switch", "feature/audit")
        self.advance()
        self.refused("non-upstream commits")
        self.assertEqual(local_commit, self.git(self.local, "rev-parse", "trunk"))
        self.unchanged_development()

    def test_checked_out_mirror_uses_ff_only(self):
        new = self.advance()
        self.git(self.local, "switch", "trunk")
        self.assertEqual(0, self.run_sync().returncode)
        self.assertEqual("upstream update", (self.local / "fixture.txt").read_text())
        self.assertEqual(new, self.git(self.local, "rev-parse", "HEAD"))
        self.assertEqual(self.original, self.git(self.local, "rev-parse", "x/main"))

    def test_mirror_in_other_worktree_is_refused(self):
        self.advance()
        self.git(self.local, "worktree", "add", str(self.root / "other"), "trunk")
        self.refused("another worktree")
        self.assertEqual(self.original, self.git(self.local, "rev-parse", "trunk"))
        self.unchanged_development()

    def test_wrong_upstream_is_refused(self):
        self.git(self.local, "remote", "set-url", "upstream", str(self.remote))
        self.refused("official PrePoMax")
        self.assertEqual(self.original, self.git(self.local, "rev-parse", "trunk"))


if __name__ == "__main__":
    unittest.main()
