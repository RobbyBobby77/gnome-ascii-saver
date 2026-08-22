#!/usr/bin/env python3
"""Idle watcher fallback used until the GNOME Shell extension is loaded."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402


UUID = "gnome-ascii-saver@local"
SCHEMA = "org.gnome.shell.extensions.gnome-ascii-saver"
home = Path.home()
data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
extension_dir = data_home / "gnome-shell" / "extensions" / UUID
app_dir = data_home / "gnome-ascii-saver"


class IdleWatcher:
    def __init__(self) -> None:
        source = Gio.SettingsSchemaSource.new_from_directory(
            str(extension_dir / "schemas"), Gio.SettingsSchemaSource.get_default(), False
        )
        schema = source.lookup(SCHEMA, True)
        if schema is None:
            raise RuntimeError(f"settings schema {SCHEMA} was not found")
        self.settings = Gio.Settings.new_full(schema, None, None)
        self.process: subprocess.Popen | None = None
        self.loop = GLib.MainLoop()
        self.idle_proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.gnome.Mutter.IdleMonitor",
            "/org/gnome/Mutter/IdleMonitor/Core",
            "org.gnome.Mutter.IdleMonitor",
            None,
        )
        self.screen_proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.gnome.ScreenSaver",
            "/org/gnome/ScreenSaver",
            "org.gnome.ScreenSaver",
            None,
        )
        # Installing or restarting the service should not immediately cover an
        # already-idle desktop. Arm after the next real user interaction.
        self.ready = self._idle_msec() < max(10, self.settings.get_uint("idle-delay")) * 1000
        self._lock_unknown_logged = False

    def _idle_msec(self) -> int:
        result = self.idle_proxy.call_sync("GetIdletime", None, Gio.DBusCallFlags.NONE, 1000, None)
        return int(result.unpack()[0])

    def _screen_locked(self) -> bool:
        try:
            result = self.screen_proxy.call_sync("GetActive", None, Gio.DBusCallFlags.NONE, 1000, None)
            self._lock_unknown_logged = False
            return bool(result.unpack()[0])
        except GLib.Error as error:
            if not self._lock_unknown_logged:
                print(
                    f"gnome-ascii-saver watcher: lock state unknown ({error.message}); not launching",
                    file=sys.stderr,
                )
                self._lock_unknown_logged = True
            return True

    def _start(self) -> None:
        if self.process is not None:
            return
        self.process = subprocess.Popen(
            [str(app_dir / "venv" / "bin" / "python"), str(app_dir / "app.py")],
            start_new_session=True,
        )

    def _stop(self) -> None:
        if self.process is None:
            return
        process = self.process
        self.process = None
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def poll(self) -> bool:
        if self.process is not None and self.process.poll() is not None:
            self.process = None
        try:
            enabled = self.settings.get_boolean("enabled")
            idle = self._idle_msec()
            locked = self._screen_locked()
            threshold = max(10, self.settings.get_uint("idle-delay")) * 1000
            if not self.ready and idle < 1000:
                self.ready = True
            if self.ready and enabled and not locked and idle >= threshold:
                self._start()
            elif self.process is not None and (not enabled or locked or idle < 1000):
                self._stop()
        except GLib.Error as error:
            print(f"gnome-ascii-saver watcher: {error.message}")
        return GLib.SOURCE_CONTINUE

    def stop(self) -> None:
        self._stop()
        self.loop.quit()

    def run(self) -> None:
        GLib.timeout_add_seconds(1, self.poll)
        self.poll()
        self.loop.run()


def main() -> int:
    watcher = IdleWatcher()
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, lambda *_unused: GLib.idle_add(watcher.stop))
    watcher.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
