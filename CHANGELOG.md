# Changelog

All notable changes to this project will be documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Dependency guidance for Fedora/RHEL, Debian/Ubuntu, Arch, openSUSE, and
  manually packaged distributions.
- Fedora and Debian validation jobs in CI.
- A systemd-optional install path for GNOME environments using another init.
- Unit tests for config validation, TTE restart backoff, and PID-file claiming.
- `GNOME_ASCII_SAVER_CONFIG_DIR`, `GNOME_ASCII_SAVER_DATA_DIR`, and
  `GNOME_ASCII_SAVER_TTE` path overrides for tests.
- Monitor add/remove handling while the fullscreen saver is showing.

### Changed

- Resolve Python from `PATH` instead of assuming `/usr/bin/python3`.
- Report unavailable systemd integration cleanly in the controller.
- Do not start the systemd fallback from extension `disable()`, so lock-screen
  teardown and turning the extension off cannot re-arm the watcher.
- Stop the renderer with SIGTERM and escalate to SIGKILL after three seconds.
- Back off and give up when the TTE child fails instead of restarting in an
  80 ms loop.
- Validate `config.json` types and warn on corrupt JSON.
- Claim the PID file exclusively under `$XDG_RUNTIME_DIR` or `/run/user/$UID`.
- Scope the user unit to GNOME, wait on `gnome-session.target`, and cap
  restart bursts.
- Treat an unknown screensaver lock state as locked (fail closed).
- Wait for `systemctl --user stop` of the fallback (and log a failure) before
  the extension arms its idle watch.
- Replace an already-running windowed preview with fullscreen (and the reverse)
  on a second Gio application activation.
- Make `gnome-ascii-saverctl uninstall` the shared removal path used by
  `uninstall.sh`.

### Fixed

- Quote the desktop `Exec` path so homes with spaces still launch.
- Split `$EDITOR` with `shlex` when the value contains spaces.
- Ignore GSettings cleanup failures in `uninstall.sh` under `set -e`.
- Report a missing launcher or a failed `os.kill` from the controller.

## [0.1.0] - 2026-08-21

### Added

- Fullscreen GTK 4/VTE rendering on every detected monitor.
- Random TerminalTextEffects animations using custom ASCII artwork.
- GNOME Shell idle integration for Shell versions 45 through 50.
- A systemd user-service fallback for installation and Shell reloads.
- GNOME extension preferences for the automatic toggle and idle delay.
- A command-line controller for previewing, configuration, and diagnostics.
- XDG-aware installation, upgrades, and removal with preserved user artwork.

[Unreleased]: https://github.com/RobbyBobby77/gnome-ascii-saver/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/RobbyBobby77/gnome-ascii-saver/releases/tag/v0.1.0
