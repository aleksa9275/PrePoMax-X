"""Boundary regressions: target execution and immutable staged host evidence."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build


class BuildBoundaries(unittest.TestCase):
    def test_plan_never_claims_execution(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(build.main(["plan", "--target", "linux-arm64"]), 0)
        self.assertFalse(json.loads(output.getvalue())["executionVerified"])

    def test_wrong_native_host_refuses_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build.platform, "system", return_value="Darwin"), \
                patch.object(build.platform, "machine", return_value="arm64"), contextlib.redirect_stderr(io.StringIO()):
            output = Path(folder) / "never-created"
            self.assertEqual(build.main(["build", "--target", "linux-x64", "--component", "solver", "--output", str(output)]), 1)
            self.assertFalse(output.exists())

    def test_unsupported_recipe_is_explicit(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build.platform, "system", return_value="Windows"), \
                patch.object(build.platform, "machine", return_value="AMD64"), contextlib.redirect_stderr(io.StringIO()):
            output = Path(folder) / "never-created"
            self.assertEqual(build.main(["build", "--target", "win-x64", "--component", "solver", "--output", str(output)]), 1)
            self.assertFalse(output.exists())

    def test_dmg_requires_explicit_solver_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build.platform, "system", return_value="Darwin"), \
                patch.object(build.platform, "machine", return_value="arm64"), contextlib.redirect_stderr(io.StringIO()):
            output = Path(folder) / "never-created"
            self.assertEqual(build.main(["package", "--target", "osx-arm64", "--format", "dmg", "--output", str(output)]), 1)
            self.assertFalse(output.exists())

    def test_linux_package_requires_tar_and_explicit_solver_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(build.platform, "system", return_value="Linux"), \
                patch.object(build.platform, "machine", return_value="aarch64"), contextlib.redirect_stderr(io.StringIO()):
            output = Path(folder) / "never-created"
            command = ["package", "--target", "linux-arm64", "--pmx-preview", "--output", str(output)]
            self.assertEqual(build.main(command), 1)
            self.assertEqual(build.main(command + ["--format", "app", "--solver-build", "solver"]), 1)
            self.assertFalse(output.exists())

    def test_staged_host_changes_cannot_reuse_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            host = root / "hosts/mesh/probe"
            host.parent.mkdir(parents=True)
            host.write_bytes(b"accepted fixture host")
            (root / "build.json").write_text(json.dumps({"success": True, "target": "linux-x64", "hostFiles": build.file_hashes(root / "hosts")}))
            build.verify_hosts(root, "linux-x64", ("mesh",))
            host.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "changed"):
                build.verify_hosts(root, "linux-x64", ("mesh",))

    def test_wrong_target_cannot_reuse_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "build.json").write_text(json.dumps({"success": True, "target": "win-x64", "hostFiles": {}}))
            with self.assertRaisesRegex(ValueError, "requested target"):
                build.verify_hosts(root, "linux-x64")

    @unittest.skipIf(build.platform.system() == "Windows", "Symlink creation can require Windows privilege")
    def test_added_runtime_symlink_cannot_reuse_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "hosts/mesh").mkdir(parents=True)
            (root / "build.json").write_text(json.dumps({"success": True, "target": "linux-x64", "hostFiles": {}}))
            (root / "hosts/mesh/runtime").symlink_to(root / "external-runtime")
            with self.assertRaisesRegex(ValueError, "symlinks"):
                build.verify_hosts(root, "linux-x64", ())

    def test_missing_elf_runtime_is_not_a_success(self):
        linux = build.load_module(build.ROOT / "ThirdParty/Build/platforms/linux.py", "linux_test")
        with patch.object(linux.subprocess, "check_output", side_effect=["ELF 64-bit LSB executable, x86-64", "libgfortran.so => not found"]):
            with self.assertRaisesRegex(ValueError, "Unresolved ELF"):
                linux.inspect(Path("fixture"), "X64", lambda _: "unused")


if __name__ == "__main__":
    unittest.main()
