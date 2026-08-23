#!/usr/bin/env python3
"""Unit tests for config validation, TTE backoff, PID files, and EDITOR argv."""

from __future__ import annotations

import io
import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import helpers  # noqa: E402


class LoadConfigTests(unittest.TestCase):
    def _write(self, directory: str, text: str) -> Path:
        path = Path(directory) / "config.json"
        path.write_text(text, encoding="utf-8")
        return path

    def test_valid_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp,
                '{"font": "Monospace 20", "background": "#111111", '
                '"frame_rate": 30, "exclude_effects": ["matrix"]}',
            )
            config = helpers.load_config(path)
        self.assertEqual(config["font"], "Monospace 20")
        self.assertEqual(config["background"], "#111111")
        self.assertEqual(config["frame_rate"], 30)
        self.assertEqual(config["exclude_effects"], ["matrix"])

    def test_missing_file_returns_defaults(self) -> None:
        path = Path("/tmp/does-not-exist-gnome-ascii-saver.json")
        config = helpers.load_config(path)
        self.assertEqual(config, helpers.new_config())

    def test_invalid_json_warns_and_returns_defaults(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, "{not json")
            config = helpers.load_config(path)
        self.assertEqual(config["frame_rate"], 60)
        self.assertIn("invalid JSON", stderr.getvalue())

    def test_non_object_json_warns(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, "[1, 2, 3]")
            config = helpers.load_config(path)
        self.assertEqual(config, helpers.new_config())
        self.assertIn("JSON object", stderr.getvalue())

    def test_string_frame_rate_is_rejected(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, '{"frame_rate": "60"}')
            config = helpers.load_config(path)
        self.assertEqual(config["frame_rate"], 60)
        self.assertIn("frame_rate", stderr.getvalue())

    def test_bool_frame_rate_is_rejected(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, '{"frame_rate": true}')
            config = helpers.load_config(path)
        self.assertEqual(config["frame_rate"], 60)
        self.assertIn("frame_rate", stderr.getvalue())

    def test_zero_frame_rate_is_rejected(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, '{"frame_rate": 0}')
            config = helpers.load_config(path)
        self.assertEqual(config["frame_rate"], 60)

    def test_exclude_effects_flags_are_dropped(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, '{"exclude_effects": ["matrix", "--help", "-v", "beams"]}')
            config = helpers.load_config(path)
        self.assertEqual(config["exclude_effects"], ["matrix", "beams"])
        self.assertIn("starts with '-'", stderr.getvalue())

    def test_exclude_effects_must_be_a_list(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, '{"exclude_effects": "matrix"}')
            config = helpers.load_config(path)
        self.assertEqual(config["exclude_effects"], ["bouncyballs", "overflow"])
        self.assertIn("exclude_effects", stderr.getvalue())

    def test_invalid_color_keeps_default(self) -> None:
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, patch("sys.stderr", stderr):
            path = self._write(tmp, '{"background": "--red", "font": 12}')
            config = helpers.load_config(path)
        self.assertEqual(config["background"], "#000000")
        self.assertEqual(config["font"], "Monospace 18")
        self.assertIn("background", stderr.getvalue())
        self.assertIn("font", stderr.getvalue())

    def test_named_color_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, '{"background": "black"}')
            config = helpers.load_config(path)
        self.assertEqual(config["background"], "black")

    def test_defaults_are_not_mutated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, '{"exclude_effects": ["matrix"]}')
            helpers.load_config(path)
        self.assertEqual(helpers.DEFAULT_CONFIG["exclude_effects"], ["bouncyballs", "overflow"])


class BackoffTests(unittest.TestCase):
    def test_successful_wait_status(self) -> None:
        self.assertTrue(helpers.tte_exit_ok(0))
        self.assertFalse(helpers.tte_exit_ok(1 << 8))

    def test_signaled_status_is_a_failure(self) -> None:
        self.assertFalse(helpers.tte_exit_ok(15))

    def test_exponential_backoff_then_give_up(self) -> None:
        self.assertEqual(helpers.tte_failure_delay_ms(1), 80)
        self.assertEqual(helpers.tte_failure_delay_ms(2), 160)
        self.assertEqual(helpers.tte_failure_delay_ms(3), 320)
        self.assertEqual(helpers.tte_failure_delay_ms(4), 640)
        self.assertIsNone(helpers.tte_failure_delay_ms(5))
        self.assertIsNone(helpers.tte_failure_delay_ms(6))

    def test_backoff_rejects_non_positive_counts(self) -> None:
        with self.assertRaises(ValueError):
            helpers.tte_failure_delay_ms(0)


class RuntimeDirTests(unittest.TestCase):
    def test_prefers_xdg_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = helpers.resolve_runtime_dir({"XDG_RUNTIME_DIR": tmp}, uid=1234)
            self.assertEqual(path, Path(tmp))

    def test_uses_run_user_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fallback = Path(tmp) / "run-user"
            path = helpers.resolve_runtime_dir({}, uid=1234, fallback_dir=fallback)
            self.assertEqual(path, fallback)
            self.assertTrue(path.is_dir())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700)

    def test_errors_when_fallback_cannot_be_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blocked = Path(tmp) / "blocked"
            blocked.write_text("not a directory", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                helpers.resolve_runtime_dir({}, uid=1, fallback_dir=blocked)


class PidFileTests(unittest.TestCase):
    def test_exclusive_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "saver.pid"
            helpers.write_pid_file(path, 4242)
            self.assertEqual(path.read_text(encoding="ascii").strip(), "4242")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with patch("helpers.pid_file_is_stale", return_value=False):
                with self.assertRaises(RuntimeError):
                    helpers.write_pid_file(path, 4343)
            self.assertEqual(path.read_text(encoding="ascii").strip(), "4242")

    def test_replaces_stale_pid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "saver.pid"
            path.write_text("1\n", encoding="ascii")
            helpers.write_pid_file(path, 99)
            self.assertEqual(path.read_text(encoding="ascii").strip(), "99")


class EditorArgvTests(unittest.TestCase):
    def test_single_token_uses_which(self) -> None:
        with patch("helpers.shutil.which", return_value="/usr/bin/vim"):
            self.assertEqual(helpers.editor_argv("vim"), ["/usr/bin/vim"])

    def test_single_token_without_which_is_kept(self) -> None:
        with patch("helpers.shutil.which", return_value=None):
            self.assertEqual(helpers.editor_argv("vim"), ["vim"])

    def test_command_with_spaces_uses_shlex(self) -> None:
        self.assertEqual(
            helpers.editor_argv('"/home/user/my editor" --wait'),
            ["/home/user/my editor", "--wait"],
        )


class VersionTests(unittest.TestCase):
    def test_reads_version_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "VERSION").write_text("0.1.0\n", encoding="utf-8")
            self.assertEqual(helpers.read_version(Path(tmp)), "0.1.0")

    def test_missing_version_file_uses_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(helpers.read_version(Path(tmp)), helpers.FALLBACK_VERSION)

    def test_metadata_version_name_matches_version_file(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        metadata = json.loads((ROOT / "extension" / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["version-name"], version)


class PathOverrideTests(unittest.TestCase):
    def test_config_dir_override(self) -> None:
        path = helpers.config_dir({helpers.CONFIG_DIR_ENV: "/tmp/custom-config"})
        self.assertEqual(path, Path("/tmp/custom-config"))

    def test_config_dir_uses_xdg_when_unset(self) -> None:
        path = helpers.config_dir({"XDG_CONFIG_HOME": "/tmp/xdg-config"})
        self.assertEqual(path, Path("/tmp/xdg-config") / "gnome-ascii-saver")

    def test_data_dir_override(self) -> None:
        path = helpers.data_dir({helpers.DATA_DIR_ENV: "/tmp/custom-data"})
        self.assertEqual(path, Path("/tmp/custom-data"))

    def test_renderer_command_honors_data_dir(self) -> None:
        argv = helpers.renderer_command({helpers.DATA_DIR_ENV: "/tmp/custom-data"})
        self.assertEqual(
            argv,
            ["/tmp/custom-data/venv/bin/python", "/tmp/custom-data/app.py"],
        )

    def test_renderer_environ_honors_config_and_data_dir(self) -> None:
        env = helpers.renderer_environ(
            {
                helpers.CONFIG_DIR_ENV: "/tmp/custom-config",
                helpers.DATA_DIR_ENV: "/tmp/custom-data",
                "PATH": "/usr/bin",
            }
        )
        self.assertEqual(env[helpers.CONFIG_DIR_ENV], "/tmp/custom-config")
        self.assertEqual(env[helpers.DATA_DIR_ENV], "/tmp/custom-data")
        self.assertEqual(env["PATH"], "/usr/bin")

    def test_renderer_environ_uses_xdg_when_overrides_unset(self) -> None:
        env = helpers.renderer_environ(
            {"XDG_CONFIG_HOME": "/tmp/xdg-config", "XDG_DATA_HOME": "/tmp/xdg-data"}
        )
        self.assertEqual(
            env[helpers.CONFIG_DIR_ENV], "/tmp/xdg-config/gnome-ascii-saver"
        )
        self.assertEqual(env[helpers.DATA_DIR_ENV], "/tmp/xdg-data/gnome-ascii-saver")

    def test_data_dir_uses_xdg_when_unset(self) -> None:
        path = helpers.data_dir({"XDG_DATA_HOME": "/tmp/xdg-data"})
        self.assertEqual(path, Path("/tmp/xdg-data") / "gnome-ascii-saver")

    def test_empty_override_is_ignored(self) -> None:
        path = helpers.config_dir(
            {helpers.CONFIG_DIR_ENV: "", "XDG_CONFIG_HOME": "/tmp/xdg-config"}
        )
        self.assertEqual(path, Path("/tmp/xdg-config") / "gnome-ascii-saver")

    def test_tte_override_uses_existing_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tte = Path(tmp) / "fake-tte"
            tte.write_text("", encoding="utf-8")
            path = helpers.tte_path({helpers.TTE_ENV: str(tte)})
            self.assertEqual(path, tte)

    def test_tte_override_missing_falls_back_to_path(self) -> None:
        path = helpers.tte_path({helpers.TTE_ENV: "/no/such/tte-binary"})
        self.assertEqual(path, Path("tte"))

    def test_tte_from_data_dir_venv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tte = Path(tmp) / "venv" / "bin" / "tte"
            tte.parent.mkdir(parents=True)
            tte.write_text("", encoding="utf-8")
            path = helpers.tte_path({helpers.DATA_DIR_ENV: tmp})
            self.assertEqual(path, tte)

    def test_tte_missing_venv_falls_back_to_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = helpers.tte_path({helpers.DATA_DIR_ENV: tmp})
            self.assertEqual(path, Path("tte"))


class ActivationModeTests(unittest.TestCase):
    def test_no_existing_windows(self) -> None:
        self.assertFalse(helpers.windows_need_rebuild(None, False))
        self.assertFalse(helpers.windows_need_rebuild(None, True))

    def test_same_mode_keeps_windows(self) -> None:
        self.assertFalse(helpers.windows_need_rebuild(True, True))
        self.assertFalse(helpers.windows_need_rebuild(False, False))

    def test_mismatch_rebuilds(self) -> None:
        self.assertTrue(helpers.windows_need_rebuild(True, False))
        self.assertTrue(helpers.windows_need_rebuild(False, True))


class DesktopEntryTests(unittest.TestCase):
    def test_exec_key_is_quoted(self) -> None:
        text = (ROOT / "io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop.in").read_text(
            encoding="utf-8"
        )
        self.assertRegex(text, r'(?m)^Exec="@EXEC@"$')


class UninstallPathTests(unittest.TestCase):
    def test_uninstall_sh_prefers_installed_ctl(self) -> None:
        text = (ROOT / "uninstall.sh").read_text(encoding="utf-8")
        ctl_exec = text.find('exec "$ctl" uninstall')
        source_exec = text.find('exec python3 "$source_dir/ctl.py" uninstall')
        self.assertNotEqual(ctl_exec, -1)
        self.assertNotEqual(source_exec, -1)
        self.assertLess(ctl_exec, source_exec)


class ExtensionPolicyTests(unittest.TestCase):
    def test_disable_does_not_start_fallback(self) -> None:
        text = (ROOT / "extension" / "extension.js").read_text(encoding="utf-8")
        self.assertNotIn("_manageFallback('start'", text)
        self.assertNotIn('_manageFallback("start"', text)
        disable = text.split("disable() {", 1)[1].split("\n    _manageFallback", 1)[0]
        self.assertIn("must not start the fallback", disable)
        self.assertNotIn("_manageFallback(", disable)


if __name__ == "__main__":
    unittest.main()
