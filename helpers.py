#!/usr/bin/env python3
"""Pure helpers shared by the renderer, controller, and unit tests."""

from __future__ import annotations

import json
import os
import signal
import shlex
import shutil
import stat
import sys
from collections.abc import Callable, Mapping
from pathlib import Path


DEFAULT_CONFIG = {
    "font": "Monospace 18",
    "background": "#000000",
    "frame_rate": 60,
    "exclude_effects": ["bouncyballs", "overflow"],
}
TTE_SUCCESS_RESTART_MS = 80
TTE_MAX_FAILURES = 5
FALLBACK_VERSION = "0.1.0"
MAX_FRAME_RATE = 240
MAX_FONT_LENGTH = 200
MAX_EXCLUDED_EFFECTS = 128
CONFIG_DIR_ENV = "GNOME_ASCII_SAVER_CONFIG_DIR"
DATA_DIR_ENV = "GNOME_ASCII_SAVER_DATA_DIR"
TTE_ENV = "GNOME_ASCII_SAVER_TTE"


def _warn(message: str) -> None:
    print(f"gnome-ascii-saver: {message}", file=sys.stderr)


def xdg_path(env_name: str, fallback: Path, env: Mapping[str, str] | None = None) -> Path:
    value = (os.environ if env is None else env).get(env_name)
    return Path(value).expanduser() if value else fallback


def _override_path(env_name: str, env: Mapping[str, str] | None = None) -> Path | None:
    value = (os.environ if env is None else env).get(env_name)
    return Path(value).expanduser() if value else None


def config_dir(env: Mapping[str, str] | None = None) -> Path:
    override = _override_path(CONFIG_DIR_ENV, env)
    if override is not None:
        return override
    return xdg_path("XDG_CONFIG_HOME", Path.home() / ".config", env) / "gnome-ascii-saver"


def data_dir(env: Mapping[str, str] | None = None) -> Path:
    override = _override_path(DATA_DIR_ENV, env)
    if override is not None:
        return override
    return xdg_path("XDG_DATA_HOME", Path.home() / ".local" / "share", env) / "gnome-ascii-saver"


def tte_path(env: Mapping[str, str] | None = None, *, data: Path | None = None) -> Path:
    """Resolve the TTE binary. A missing override or venv copy falls back to PATH."""
    override = _override_path(TTE_ENV, env)
    if override is not None:
        return override if override.exists() else Path("tte")
    executable = (data if data is not None else data_dir(env)) / "venv" / "bin" / "tte"
    return executable if executable.exists() else Path("tte")


def renderer_command(env: Mapping[str, str] | None = None) -> list[str]:
    """Argv used to spawn the GTK renderer from the idle watcher."""
    root = data_dir(env)
    return [str(root / "venv" / "bin" / "python"), str(root / "app.py")]


def renderer_environ(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """Copy env with resolved CONFIG_DIR and DATA_DIR so children share helpers."""
    source = os.environ if env is None else env
    result = {key: str(value) for key, value in source.items()}
    result[CONFIG_DIR_ENV] = str(config_dir(source))
    result[DATA_DIR_ENV] = str(data_dir(source))
    return result


def windows_need_rebuild(existing_windowed: bool | None, requested_windowed: bool) -> bool:
    """True when a second Gio activation asked for a different window mode."""
    if existing_windowed is None:
        return False
    return existing_windowed != requested_windowed


def new_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    config["exclude_effects"] = list(DEFAULT_CONFIG["exclude_effects"])
    return config


def read_version(here: Path | None = None) -> str:
    root = Path(__file__).resolve().parent if here is None else here
    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return FALLBACK_VERSION
    return version or FALLBACK_VERSION


def _valid_color(value: object) -> bool:
    """Return whether *value* works in both GDK and TTE."""
    if not isinstance(value, str):
        return False
    text = value.strip()
    digits = text[1:] if text.startswith("#") else ""
    return len(digits) == 6 and all(char in "0123456789abcdefABCDEF" for char in digits)


def _apply_config(config: dict, loaded: dict, origin: Path) -> dict:
    font = loaded.get("font", config["font"])
    if (
        isinstance(font, str)
        and font.strip()
        and len(font) <= MAX_FONT_LENGTH
        and font.isprintable()
    ):
        config["font"] = font.strip()
    elif "font" in loaded:
        _warn(f"{origin}: ignoring invalid font {font!r}")

    background = loaded.get("background", config["background"])
    if _valid_color(background):
        config["background"] = str(background).strip()
    elif "background" in loaded:
        _warn(f"{origin}: ignoring invalid background color {background!r}")

    if "frame_rate" in loaded:
        frame_rate = loaded["frame_rate"]
        if (
            isinstance(frame_rate, bool)
            or not isinstance(frame_rate, int)
            or not 1 <= frame_rate <= MAX_FRAME_RATE
        ):
            _warn(
                f"{origin}: ignoring invalid frame_rate {frame_rate!r}; "
                f"expected 1-{MAX_FRAME_RATE}, using {config['frame_rate']}"
            )
        else:
            config["frame_rate"] = frame_rate

    if "exclude_effects" in loaded:
        excluded = loaded["exclude_effects"]
        if not isinstance(excluded, list):
            _warn(f"{origin}: exclude_effects must be a list of names; using defaults")
        else:
            cleaned: list[str] = []
            for item in excluded[:MAX_EXCLUDED_EFFECTS]:
                if (
                    not isinstance(item, str)
                    or not item
                    or len(item) > 64
                    or not all(char.isascii() and (char.isalnum() or char in "_-") for char in item)
                ):
                    _warn(f"{origin}: ignoring invalid exclude_effects entry {item!r}")
                    continue
                if item.startswith("-"):
                    _warn(
                        f"{origin}: ignoring exclude_effects entry {item!r} "
                        "because it starts with '-'"
                    )
                    continue
                cleaned.append(item)
            if len(excluded) > MAX_EXCLUDED_EFFECTS:
                _warn(
                    f"{origin}: ignoring exclude_effects entries after "
                    f"the first {MAX_EXCLUDED_EFFECTS}"
                )
            config["exclude_effects"] = cleaned
    return config


def load_config(path: Path) -> dict:
    config = new_config()
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return config
    except OSError as error:
        _warn(f"could not read {path}: {error}")
        return config
    except ValueError as error:
        _warn(f"invalid JSON in {path}: {error}")
        return config
    if not isinstance(loaded, dict):
        _warn(f"{path} must contain a JSON object")
        return config
    return _apply_config(config, loaded, path)


def tte_exit_ok(status: int) -> bool:
    """True when a TTE child finished an effect successfully.

    VTE reports a waitpid-style status. A decoded exit code of 0 is also
    treated as success.
    """
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status) == 0
    if os.WIFSIGNALED(status):
        return False
    return status == 0


def tte_failure_delay_ms(consecutive_failures: int) -> int | None:
    """Exponential backoff after a failed TTE child, or None to give up."""
    if consecutive_failures < 1:
        raise ValueError("consecutive_failures must be >= 1")
    if consecutive_failures >= TTE_MAX_FAILURES:
        return None
    return TTE_SUCCESS_RESTART_MS * (2 ** (consecutive_failures - 1))


def resolve_runtime_dir(
    env: Mapping[str, str] | None = None,
    *,
    uid: int | None = None,
    fallback_dir: Path | None = None,
) -> Path:
    """Return a private per-user runtime directory.

    Prefer XDG_RUNTIME_DIR. If it is unset, try /run/user/<uid> (or an
    explicit fallback used by tests). Never fall back to world-writable /tmp.
    """
    environ = os.environ if env is None else env
    resolved_uid = os.getuid() if uid is None else uid
    xdg = environ.get("XDG_RUNTIME_DIR")
    path = (
        Path(xdg).expanduser()
        if xdg
        else Path(fallback_dir) if fallback_dir is not None else Path(f"/run/user/{resolved_uid}")
    )
    try:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        status = path.lstat()
    except OSError as error:
        raise RuntimeError(
            f"{path} cannot be used as a private runtime directory: {error}"
        ) from error
    if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
        raise RuntimeError(f"{path} is not a real runtime directory")
    if status.st_uid != os.getuid() or stat.S_IMODE(status.st_mode) & 0o077:
        raise RuntimeError(f"{path} is not private to the current user")
    if not os.access(path, os.W_OK | os.X_OK):
        raise RuntimeError(f"{path} is not writable")
    return path


def pid_file_path(
    env: Mapping[str, str] | None = None,
    *,
    uid: int | None = None,
    fallback_dir: Path | None = None,
) -> Path:
    resolved_uid = os.getuid() if uid is None else uid
    return resolve_runtime_dir(env, uid=resolved_uid, fallback_dir=fallback_dir) / (
        f"gnome-ascii-saver-{resolved_uid}.pid"
    )


def _process_argv(pid: int) -> tuple[bytes, ...]:
    if pid <= 0:
        return ()
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ()
    return tuple(argument for argument in cmdline.split(b"\0") if argument)


def process_matches_saver(pid: int, expected_script: Path | None = None) -> bool:
    """Match the renderer's exact absolute Python script argument."""
    argv = _process_argv(pid)
    script = (
        Path(__file__).resolve().with_name("app.py")
        if expected_script is None
        else expected_script
    )
    if len(argv) < 2:
        return False
    try:
        actual_script = Path(os.fsdecode(argv[1])).resolve(strict=False)
    except UnicodeError:
        return False
    return actual_script == script.resolve(strict=False)


def pid_from_file(path: Path, matches: Callable[[int], bool]) -> int | None:
    try:
        pid = int(path.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None
    return pid if matches(pid) else None


def send_signal_if_matches(pid: int, signum: int, matches: Callable[[int], bool]) -> bool:
    """Signal a matching process without redirecting a signal after PID reuse."""
    pidfd_open = getattr(os, "pidfd_open", None)
    pidfd_send_signal = getattr(signal, "pidfd_send_signal", None)
    if pidfd_open is not None and pidfd_send_signal is not None:
        try:
            descriptor = pidfd_open(pid)
        except ProcessLookupError:
            return False
        try:
            if not matches(pid):
                return False
            try:
                pidfd_send_signal(descriptor, signum)
            except ProcessLookupError:
                return False
            return True
        finally:
            os.close(descriptor)

    if not matches(pid):
        return False
    try:
        os.kill(pid, signum)
    except ProcessLookupError:
        return False
    return True


def pid_file_is_stale(path: Path) -> bool:
    try:
        pid = int(path.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return True
    return not process_matches_saver(pid)


def write_pid_file(path: Path, pid: int) -> Path:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        if not pid_file_is_stale(path):
            raise RuntimeError(f"pid file {path} is already claimed") from None
        path.unlink(missing_ok=True)
        fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, f"{pid}\n".encode("ascii"))
    finally:
        os.close(fd)
    return path


def current_saver_pid(path: Path | None = None) -> int | None:
    try:
        pid_path = path if path is not None else pid_file_path()
    except RuntimeError:
        return None
    return pid_from_file(pid_path, process_matches_saver)


def editor_argv(editor: str) -> list[str]:
    """Turn $EDITOR / $VISUAL into argv without a naive split on every space."""
    editor = editor.strip()
    if not editor:
        return []
    if " " not in editor:
        found = shutil.which(editor)
        return [found if found else editor]
    return shlex.split(editor)
