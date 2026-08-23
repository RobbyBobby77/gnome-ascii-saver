# GNOME ASCII Saver

[![CI](https://github.com/RobbyBobby77/gnome-ascii-saver/actions/workflows/ci.yml/badge.svg)](https://github.com/RobbyBobby77/gnome-ascii-saver/actions/workflows/ci.yml)
[![GNOME Shell 45–50](https://img.shields.io/badge/GNOME%20Shell-45–50-4A86CF?logo=gnome)](https://www.gnome.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

```text
   ██████╗ ███╗   ██╗ ██████╗ ███╗   ███╗███████╗
  ██╔════╝ ████╗  ██║██╔═══██╗████╗ ████║██╔════╝
  ██║  ███╗██╔██╗ ██║██║   ██║██╔████╔██║█████╗
  ██║   ██║██║╚██╗██║██║   ██║██║╚██╔╝██║██╔══╝
  ╚██████╔╝██║ ╚████║╚██████╔╝██║ ╚═╝ ██║███████╗
   ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
```

An Omarchy-inspired animated ASCII idle screen for GNOME. Your artwork is
rendered through a random
[TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects)
animation in a clean GTK 4/VTE fullscreen window on every monitor.

> [!IMPORTANT]
> This is a decorative idle screen, not an authentication or security screen.
> It never replaces, delays, or unlocks GNOME's lock screen.

## What it does

- Starts automatically after a configurable idle delay.
- Creates one fullscreen GTK/VTE window per connected monitor.
- Chooses a new terminal animation whenever an effect finishes.
- Dismisses instantly on keyboard, pointer, click, or scroll activity.
- Preserves GNOME's normal locking behavior, including `Super`+`L`.
- Includes a preferences panel and a small command-line controller.
- Uses an isolated Python environment and preserves your artwork on upgrades.

The current release is **0.1.0**. The native extension declares GNOME Shell
45–50 compatibility and has been exercised live on GNOME Shell 50 under
Wayland.

## Quick start on Linux

Ask the project for the correct dependency command for the current distro:

```sh
./scripts/dependency-hint.sh
```

Install those packages, then clone and install:

```sh
git clone git@github.com:RobbyBobby77/gnome-ascii-saver.git
cd gnome-ascii-saver
./install.sh
```

The repository is private, so the GitHub account or SSH key used to clone it
must have access. HTTPS cloning works too:

```sh
git clone https://github.com/RobbyBobby77/gnome-ascii-saver.git
```

On systemd-based desktops, the installer enables a user unit so idle
activation works immediately, before the next logout. Log out and back in once
if GNOME cannot load the newly installed extension in the current Shell
session. After login the extension stops the fallback service and becomes the
only idle watcher; turning the extension off or locking the screen does not
start that service again. On a non-systemd distro, the native extension owns
idle activation and may require that one logout/login before it can start.

The controller and launchers are installed to `~/.local/bin`. Add that
directory to `PATH` if `gnome-ascii-saverctl` is not found after install:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

The installer also prints absolute paths you can invoke directly. The Shell
extension UUID is `gnome-ascii-saver@local` while this project remains private.

## Use it

```sh
gnome-ascii-saverctl start        # start fullscreen now
gnome-ascii-saverctl preview      # open a decorated preview window
gnome-ascii-saverctl stop         # close the saver
gnome-ascii-saverctl edit         # edit the ASCII artwork
gnome-ascii-saverctl delay 180    # set the idle delay in seconds
gnome-ascii-saverctl disable      # pause automatic activation
gnome-ascii-saverctl enable       # resume automatic activation
gnome-ascii-saverctl prefs        # open extension preferences
gnome-ascii-saverctl status       # show runtime and integration state
```

The default delay is 120 seconds. Press a key, move the pointer, click, or
scroll to dismiss the saver.

## Customize it

Your user-owned settings live outside the checkout and survive upgrades:

```text
~/.config/gnome-ascii-saver/logo.txt
~/.config/gnome-ascii-saver/config.json
```

`config.json` accepts these values:

```json
{
  "font": "Monospace 18",
  "background": "#000000",
  "frame_rate": 60,
  "exclude_effects": ["bouncyballs", "overflow"]
}
```

Run `gnome-ascii-saverctl stop` and start it again after changing visual
settings. The idle delay and automatic-launch toggle can be changed live from
the extension preferences.

## Install on another computer

The easiest route is to clone the repository on the destination machine and
run `./install.sh`. If that machine cannot access GitHub, create an archive on
a machine that already has the checkout:

```sh
cd /path/to
tar --exclude='.git' -czf gnome-ascii-saver-0.1.0.tar.gz gnome-ascii-saver
```

Copy the archive by USB, `scp`, or cloud storage, then install it on the other
computer:

```sh
tar -xzf gnome-ascii-saver-0.1.0.tar.gz
cd gnome-ascii-saver
./install.sh
gnome-ascii-saverctl status
gnome-ascii-saverctl preview
```

Package names vary by distribution. Run `./scripts/dependency-hint.sh` for a
Fedora/RHEL, Debian/Ubuntu, Arch, or openSUSE command, or see the complete
[distribution guide](docs/DISTRIBUTIONS.md). The destination needs Python 3,
GTK 4, PyGObject, GTK4 VTE, GLib schema tools, GNOME Shell, and internet access
during installation so the isolated environment can fetch
TerminalTextEffects. A systemd user manager is optional.

To carry over your art and visual settings, copy this directory to the same
location on the destination computer:

```text
~/.config/gnome-ascii-saver/
```

## How it fits into GNOME

```text
GNOME Shell extension ─┐
                      ├─ idle reached ─> GTK/VTE renderer ─> TTE animation
systemd fallback* ────┘                         │
                                               └─ activity ─> exit
GNOME lock screen remains independent and authoritative

* optional; used only when a systemd user manager is available
```

The extension uses GNOME's core idle monitor and is the preferred integration.
The fallback watcher uses Mutter's session D-Bus idle monitor until the Shell
extension is available. Only one integration should be active at a time.

See [Architecture](docs/ARCHITECTURE.md) for the process model,
[Distributions](docs/DISTRIBUTIONS.md) for package-manager guidance,
[Security](SECURITY.md) for the trust boundary, and
[Contributing](CONTRIBUTING.md) for development checks.

## Upgrade or uninstall

Pull the latest source and rerun the installer. Existing config and artwork
are retained:

```sh
git pull --ff-only
./install.sh
```

To remove the application, extension, and service while keeping your artwork:

```sh
./uninstall.sh
```

`gnome-ascii-saverctl uninstall` performs the same steps once the controller is
installed. `./uninstall.sh` execs that launcher when present, then the checkout
`ctl.py`, so both paths stay on the controller.

Delete `~/.config/gnome-ascii-saver/` separately only if you also want to
remove your artwork and visual settings.

## Credits

Inspired by the elegant terminal screensaver experience in
[Omarchy](https://omarchy.org/) and powered by
[TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects).

Licensed under the [MIT License](LICENSE).
