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

### Changed

- Resolve Python from `PATH` instead of assuming `/usr/bin/python3`.
- Report unavailable systemd integration cleanly in the controller.

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
