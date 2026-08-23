#!/usr/bin/env python3
"""Unit tests for controller start/stop error handling."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ctl  # noqa: E402


class CtlStartStopTests(unittest.TestCase):
    def test_start_reports_missing_launcher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            launcher = Path(tmp) / "gnome-ascii-saver"
            with patch.object(ctl, "launcher", launcher), patch.object(
                ctl, "current_pid", return_value=None
            ):
                with self.assertRaises(SystemExit) as raised:
                    ctl.command_start()
        message = str(raised.exception).lower()
        self.assertIn("not found", message)
        self.assertIn(str(launcher).lower(), message)

    def test_start_reports_spawn_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            launcher = Path(tmp) / "gnome-ascii-saver"
            launcher.write_text("#!/bin/sh\n", encoding="utf-8")
            launcher.chmod(0o755)
            with patch.object(ctl, "launcher", launcher), patch.object(
                ctl, "current_pid", return_value=None
            ), patch("ctl.subprocess.Popen", side_effect=OSError("boom")):
                with self.assertRaises(SystemExit) as raised:
                    ctl.command_start()
        self.assertIn("could not start", str(raised.exception).lower())

    def test_stop_handles_process_lookup(self) -> None:
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stdout", stdout):
            path = Path(tmp) / "pid"
            path.write_text("99999\n", encoding="ascii")
            with patch.object(ctl, "pid_file_path", return_value=path), patch.object(
                ctl, "pid_from_file", return_value=99999
            ), patch.object(ctl, "send_signal_if_matches", return_value=False):
                ctl.command_stop()
        self.assertIn("not running", stdout.getvalue())
        self.assertFalse(path.exists())

    def test_stop_reports_permission_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pid"
            path.write_text("1\n", encoding="ascii")
            with patch.object(ctl, "pid_file_path", return_value=path), patch.object(
                ctl, "pid_from_file", return_value=1
            ), patch.object(
                ctl, "send_signal_if_matches", side_effect=PermissionError("denied")
            ):
                with self.assertRaises(SystemExit) as raised:
                    ctl.command_stop()
        self.assertIn("could not stop", str(raised.exception).lower())

    def test_stop_quiet_permission_error_does_not_exit(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = Path(tmp) / "pid"
            path.write_text("1\n", encoding="ascii")
            with patch.object(ctl, "pid_file_path", return_value=path), patch.object(
                ctl, "pid_from_file", return_value=1
            ), patch.object(
                ctl, "send_signal_if_matches", side_effect=PermissionError("denied")
            ):
                ctl.command_stop(quiet=True)
        self.assertIn("could not stop", stderr.getvalue().lower())

    def test_uninstall_refuses_missing_hardened_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.object(ctl, "data_dir", Path(tmp)):
            with self.assertRaises(SystemExit) as raised:
                ctl.command_uninstall()
        self.assertIn("hardened uninstaller is missing", str(raised.exception))

    def test_uninstall_delegates_to_installed_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            uninstaller = Path(tmp) / "uninstall.sh"
            uninstaller.write_text("#!/bin/sh\n", encoding="utf-8")
            uninstaller.chmod(0o700)
            completed = unittest.mock.Mock(returncode=0)
            with patch.object(ctl, "data_dir", Path(tmp)), patch(
                "ctl.subprocess.run", return_value=completed
            ) as run:
                ctl.command_uninstall()
        run.assert_called_once_with([str(uninstaller), "--non-interactive"], check=False)


if __name__ == "__main__":
    unittest.main()
