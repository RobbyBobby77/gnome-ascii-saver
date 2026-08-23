#!/usr/bin/env python3
"""Control utility for GNOME ASCII Saver."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from helpers import (
    config_dir as resolve_config_dir,
    data_dir as resolve_data_dir,
    editor_argv,
    pid_from_file,
    pid_file_path,
    process_matches_saver,
    read_version,
    send_signal_if_matches,
)


UUID = "gnome-ascii-saver@robbybobby77.github.io"
SCHEMA = "org.gnome.shell.extensions.gnome-ascii-saver"
VERSION = read_version()
home = Path.home()
config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
config_dir = resolve_config_dir()
data_dir = resolve_data_dir()
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
        path = pid_file_path()
    except RuntimeError:
        return None
    return pid_from_file(path, process_matches_installed_saver)


def process_matches_installed_saver(pid: int) -> bool:
    return process_matches_saver(pid, data_dir / "app.py")


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
    if not launcher.exists():
        raise SystemExit(
            f"gnome-ascii-saverctl: launcher not found at {launcher}; run ./install.sh"
        )
    args = [str(launcher)]
    if windowed:
        args.append("--windowed")
    try:
        subprocess.Popen(
            args,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as error:
        raise SystemExit(
            f"gnome-ascii-saverctl: could not start {launcher}: {error}"
        ) from error


def command_stop(*, quiet: bool = False) -> None:
    try:
        path = pid_file_path()
    except RuntimeError:
        if not quiet:
            print("GNOME ASCII Saver is not running")
        return
    pid = pid_from_file(path, process_matches_installed_saver)
    if not pid:
        path.unlink(missing_ok=True)
        if not quiet:
            print("GNOME ASCII Saver is not running")
        return
    try:
        stopped = send_signal_if_matches(pid, signal.SIGTERM, process_matches_installed_saver)
    except PermissionError as error:
        message = f"gnome-ascii-saverctl: could not stop process {pid}: {error}"
        if quiet:
            print(message, file=sys.stderr)
            return
        raise SystemExit(message) from error
    if not stopped:
        path.unlink(missing_ok=True)
        if not quiet:
            print("GNOME ASCII Saver is not running")
        return
    if not quiet:
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
    installed_uninstaller = data_dir / "uninstall.sh"
    if not installed_uninstaller.is_file() or not os.access(installed_uninstaller, os.X_OK):
        raise SystemExit(
            "gnome-ascii-saverctl: the hardened uninstaller is missing; "
            "reinstall GNOME ASCII Saver or run uninstall.sh from a trusted source checkout"
        )
    completed = subprocess.run(
        [str(installed_uninstaller), "--non-interactive"],
        check=False,
    )
    if completed.returncode:
        raise SystemExit(
            f"gnome-ascii-saverctl: uninstaller exited with status {completed.returncode}"
        )


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
        command_uninstall()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
