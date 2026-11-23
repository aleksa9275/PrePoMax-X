"""Boundary regressions: target execution of the solver build."""
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

    def test_missing_elf_runtime_is_not_a_success(self):
        linux = build.load_module(build.ROOT / "ThirdParty/Build/platforms/linux.py", "linux_test")
        with patch.object(linux.subprocess, "check_output", side_effect=["ELF 64-bit LSB executable, x86-64", "libgfortran.so => not found"]):
            with self.assertRaisesRegex(ValueError, "Unresolved ELF"):
                linux.inspect(Path("fixture"), "X64", lambda _: "unused")


if __name__ == "__main__":
    unittest.main()
