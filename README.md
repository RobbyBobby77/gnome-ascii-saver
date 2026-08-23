# GNOME ASCII Saver

[![CI](https://github.com/RobbyBobby77/gnome-ascii-saver/actions/workflows/ci.yml/badge.svg)](https://github.com/RobbyBobby77/gnome-ascii-saver/actions/workflows/ci.yml)
[![GNOME Shell 45–50](https://img.shields.io/badge/GNOME%20Shell-45–50-4A86CF?logo=gnome)](https://www.gnome.org/)
[![Wayland and X11](https://img.shields.io/badge/display-Wayland_%7C_X11-6c63ff)](docs/RELEASE_CHECKLIST.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An Omarchy-inspired animated ASCII idle screen for GNOME. It displays custom
artwork with random
[TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects)
animations on every monitor, then disappears on the first keyboard or pointer
input.

```text
   ██████╗ ███╗   ██╗ ██████╗ ███╗   ███╗███████╗
  ██╔════╝ ████╗  ██║██╔═══██╗████╗ ████║██╔════╝
  ██║  ███╗██╔██╗ ██║██║   ██║██╔████╔██║█████╗
  ██║   ██║██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══╝
  ╚██████╔╝██║ ╚████║╚██████╔╝██║ ╚═╝ ██║███████╗
   ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
```

> [!IMPORTANT]
> GNOME ASCII Saver is decorative, not an authentication or security screen.
> GNOME's lock screen remains responsible for securing the session. This
> project does not replace, delay, unlock, or reconfigure it.

## Install

On a supported GNOME system, run:

```sh
curl -fsSL https://raw.githubusercontent.com/RobbyBobby77/gnome-ascii-saver/main/install-online.sh | bash
```

The bootstrap downloads the latest stable tagged release, verifies its SHA-256
checksum, and runs the bundled user-local installer. It never invokes `sudo`;
if system packages are missing, the installer prints a command for you to
review and run.

To inspect the bootstrap before running it:

```sh
curl -fsSLO https://raw.githubusercontent.com/RobbyBobby77/gnome-ascii-saver/main/install-online.sh
less install-online.sh
bash install-online.sh
```

You can also [install from a Git clone](docs/INSTALLATION.md#install-from-a-git-clone).
See the [installation guide](docs/INSTALLATION.md) for dependencies, pinned
versions, upgrades, rollbacks, and removal.

## What it does

- Shows editable ASCII artwork with randomly selected TTE animations.
- Creates one fullscreen GTK 4/VTE window per connected monitor.
- Uses GNOME Shell's native idle monitor for automatic activation.
- Provides an optional systemd user-service fallback during extension loading.
- Stops when the extension is disabled or GNOME transitions to its lock screen.
- Provides a decorated preview, manual launch, preferences, and CLI controls.
- Preserves user configuration and artwork across upgrades and uninstall.

## Requirements and status

GNOME ASCII Saver targets Linux distributions with GNOME Shell 45–50, Python
3, GTK 4, PyGObject, and GTK4 VTE 3.91. Fedora/RHEL, Debian/Ubuntu,
Arch-family, and openSUSE package commands are in the
[distribution guide](docs/DISTRIBUTIONS.md). A systemd user manager is
optional.

Version `0.1.0` is an initial preview. CI validates portable source and runtime
dependencies on Fedora and Debian. The declared GNOME Shell, display protocol,
and monitor combinations still require recorded desktop acceptance before the
project should be described as stable; see the
[release checklist](docs/RELEASE_CHECKLIST.md).

## Use it

The installer places commands in `~/.local/bin`:

```sh
gnome-ascii-saverctl start        # show the fullscreen saver now
gnome-ascii-saverctl preview      # open a decorated preview window
gnome-ascii-saverctl stop         # close it
gnome-ascii-saverctl edit         # edit the ASCII artwork
gnome-ascii-saverctl prefs        # open extension preferences
gnome-ascii-saverctl delay 180    # set the idle delay in seconds
gnome-ascii-saverctl disable      # pause automatic activation
gnome-ascii-saverctl enable
gnome-ascii-saverctl status
```

If the command is not found, add the user binary directory to your shell path:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

The default idle delay is 120 seconds. Press a key, move the pointer, click, or
scroll to dismiss the saver.

## Customize it

Artwork and visual settings live under `~/.config/gnome-ascii-saver/` by
default:

```text
~/.config/gnome-ascii-saver/logo.txt
~/.config/gnome-ascii-saver/config.json
```

Example configuration:

```json
{
  "font": "Monospace 18",
  "background": "#000000",
  "frame_rate": 60,
  "exclude_effects": ["bouncyballs", "overflow"]
}
```

The project honors `XDG_CONFIG_HOME` and `XDG_DATA_HOME`. Existing settings
and artwork are not overwritten during upgrade or removed during uninstall.
The automatic toggle and idle delay also appear in GNOME Extensions
preferences.

## GNOME integration

The native extension is the preferred idle integration. A systemd fallback
can provide continuity until GNOME Shell loads a newly installed extension.
Once the extension is active it stops the fallback, so only one idle watcher
should run. On a non-systemd desktop, log out and back in once if the current
Shell session cannot load the new extension immediately.

```text
GNOME Shell extension ─┐
                      ├─ idle reached ─> GTK/VTE renderer ─> TTE animation
systemd fallback* ────┘                         │
                                               └─ input ─> exit
GNOME lock screen remains independent and authoritative

* optional; used only when a systemd user manager is available
```

See [Architecture](docs/ARCHITECTURE.md) for the process model and trust
boundaries.

## Help and security

Start diagnostics with:

```sh
gnome-ascii-saverctl --version
gnome-ascii-saverctl status
gnome-extensions info gnome-ascii-saver@robbybobby77.github.io
```

If `status` reports the fallback service, also inspect:

```sh
systemctl --user status gnome-ascii-saver.service
journalctl --user -u gnome-ascii-saver.service -b
```

The [troubleshooting guide](docs/TROUBLESHOOTING.md) covers extension loading,
Wayland/X11, multiple monitors, and systemd/non-systemd sessions. For general
help, see [Support](SUPPORT.md); report vulnerabilities privately as described
in [Security](SECURITY.md).

The application runs entirely as the logged-in user. It does not collect
telemetry, upload artwork or settings, or require an account after
installation. The online path fetches a release from GitHub and installs the
version-pinned, hash-verified Python dependencies into an isolated environment.

## Project documentation

- [Installation and maintenance](docs/INSTALLATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Architecture and trust boundaries](docs/ARCHITECTURE.md)
- [Distribution support](docs/DISTRIBUTIONS.md)
- [Release and GNOME acceptance checklist](docs/RELEASE_CHECKLIST.md)
- [Acceptance record template](docs/ACCEPTANCE-TEMPLATE.md)
- [Contributing](CONTRIBUTING.md)

## Credits

- Inspired by [Omarchy](https://github.com/basecamp/omarchy)
- Animated by [TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects)
- Built with GNOME Shell, GTK, VTE, and PyGObject

Released under the [MIT License](LICENSE).
