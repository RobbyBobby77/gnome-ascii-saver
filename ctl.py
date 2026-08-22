#!/usr/bin/env python3
"""Control utility for GNOME ASCII Saver."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
from pathlib import Path

from helpers import current_saver_pid, editor_argv, pid_file_path, read_version


UUID = "gnome-ascii-saver@local"
SCHEMA = "org.gnome.shell.extensions.gnome-ascii-saver"
VERSION = read_version()
home = Path.home()
config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
config_dir = config_home / "gnome-ascii-saver"
data_dir = data_home / "gnome-ascii-saver"
extension_dir = data_home / "gnome-shell" / "extensions" / UUID
launcher = home / ".local" / "bin" / "gnome-ascii-saver"


def systemd_user_available() -> bool:
    executable = shutil.which("systemctl")
    if executable is None:
        return False
    return subprocess.run(
        [executable, "--user", "show-environment"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def current_pid() -> int | None:
    try:
        return current_saver_pid(pid_file_path())
    except RuntimeError:
        return None


def settings(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gsettings", "--schemadir", str(extension_dir / "schemas"), *args],
        check=check,
        text=True,
        capture_output=True,
    )


def command_start(windowed: bool = False) -> None:
    if current_pid():
        print("GNOME ASCII Saver is already running")
        return
    args = [str(launcher)]
    if windowed:
        args.append("--windowed")
    subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def command_stop() -> None:
    try:
        path = pid_file_path()
    except RuntimeError:
        print("GNOME ASCII Saver is not running")
        return
    pid = current_saver_pid(path)
    if not pid:
        path.unlink(missing_ok=True)
        print("GNOME ASCII Saver is not running")
        return
    os.kill(pid, signal.SIGTERM)
    print("Stopped GNOME ASCII Saver")


def command_edit() -> None:
    logo = config_dir / "logo.txt"
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if editor:
        argv = editor_argv(editor)
        if argv:
            subprocess.run([*argv, str(logo)], check=False)
            return
    subprocess.Popen(["xdg-open", str(logo)], start_new_session=True)


def command_status() -> None:
    pid = current_pid()
    try:
        enabled = settings("get", SCHEMA, "enabled", check=False).stdout.strip()
        delay = settings("get", SCHEMA, "idle-delay", check=False).stdout.strip()
        delay = delay.removeprefix("uint32 ")
    except OSError:
        enabled, delay = "unknown", "unknown"
    print(f"running: {'yes' if pid else 'no'}")
    print(f"automatic: {enabled}")
    print(f"idle delay: {delay} seconds")
    if systemd_user_available():
        service = subprocess.run(
            ["systemctl", "--user", "is-active", "gnome-ascii-saver.service"],
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    else:
        service = "unavailable"
    extension_info = subprocess.run(
        ["gnome-extensions", "info", UUID],
        text=True,
        capture_output=True,
        check=False,
    ).stdout
    extension_state = "unavailable"
    for line in extension_info.splitlines():
        if line.strip().startswith("State:"):
            extension_state = line.split(":", 1)[1].strip().lower()
            break
    if extension_state == "active":
        integration = "GNOME Shell extension (active)"
    elif service == "active":
        integration = "fallback user service (active)"
    else:
        integration = f"extension {extension_state}; fallback {service or 'unavailable'}"
    print(f"idle integration: {integration}")
    print(f"logo: {config_dir / 'logo.txt'}")


def command_uninstall() -> None:
    subprocess.run(
        ["gnome-extensions", "disable", UUID],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if systemd_user_available():
        subprocess.run(
            ["systemctl", "--user", "disable", "--now", "gnome-ascii-saver.service"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    for path in (
        extension_dir,
        data_dir,
        config_home / "systemd" / "user" / "gnome-ascii-saver.service",
        data_home / "applications" / "io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop",
        home / ".local" / "bin" / "gnome-ascii-saver",
        home / ".local" / "bin" / "gnome-ascii-saverctl",
        home / ".local" / "bin" / "gnome-ascii-saver-watcher",
    ):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    if systemd_user_available():
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    try:
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio

        shell = Gio.Settings.new("org.gnome.shell")
        enabled = [item for item in shell.get_strv("enabled-extensions") if item != UUID]
        shell.set_strv("enabled-extensions", enabled)
    except Exception:
        pass
    print(f"Removed the application and extension. Your art is preserved in {config_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Control GNOME ASCII Saver")
    parser.add_argument("--version", action="version", version=f"GNOME ASCII Saver {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("start")
    sub.add_parser("preview")
    sub.add_parser("stop")
    sub.add_parser("edit")
    sub.add_parser("enable")
    sub.add_parser("disable")
    delay_parser = sub.add_parser("delay")
    delay_parser.add_argument("seconds", type=int)
    sub.add_parser("prefs")
    sub.add_parser("status")
    sub.add_parser("uninstall")
    args = parser.parse_args()

    if args.command == "start":
        command_start()
    elif args.command == "preview":
        command_start(windowed=True)
    elif args.command == "stop":
        command_stop()
    elif args.command == "edit":
        command_edit()
    elif args.command in ("enable", "disable"):
        settings("set", SCHEMA, "enabled", "true" if args.command == "enable" else "false")
        print(f"Automatic screensaver {args.command}d")
    elif args.command == "delay":
        if not 10 <= args.seconds <= 86400:
            parser.error("delay must be between 10 and 86400 seconds")
        settings("set", SCHEMA, "idle-delay", str(args.seconds))
        print(f"Idle delay set to {args.seconds} seconds")
    elif args.command == "prefs":
        subprocess.Popen(["gnome-extensions", "prefs", UUID], start_new_session=True)
    elif args.command == "status":
        command_status()
    elif args.command == "uninstall":
        command_stop() if current_pid() else None
        command_uninstall()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
