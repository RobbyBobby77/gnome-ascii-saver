# Installation and maintenance

## Before installing

GNOME ASCII Saver is intended for Linux desktops running GNOME Shell 45–50.
It needs Python 3 with virtual-environment support, PyGObject, GTK 4, GTK4 VTE
(`Vte 3.91`), GLib schema tools, and the `gnome-extensions` command.

The online bootstrap requires Bash, `curl`, Python 3, and either `sha256sum` or
`shasum`. The installer is user-local: it does not invoke `sudo` or a system
package manager. See [Distribution support](DISTRIBUTIONS.md) for package names.

## Recommended online install

```sh
curl -fsSL https://raw.githubusercontent.com/RobbyBobby77/gnome-ascii-saver/main/install-online.sh | bash
```

The bootstrap obtains the latest stable tagged release archive and its
published SHA-256 checksum, verifies the archive, extracts it to a temporary
directory, and runs the included installer. Installation stops on a missing or
mismatched checksum. The checksum detects a damaged or mismatched archive;
GitHub, the repository, and the release assets remain part of the trust
boundary.

Piping a network response to a shell is convenient but requires trusting that
URL at execution time. To review exactly what will run first:

```sh
curl -fsSLO https://raw.githubusercontent.com/RobbyBobby77/gnome-ascii-saver/main/install-online.sh
less install-online.sh
bash install-online.sh
```

To install or roll back to a specific published version with the reviewed
bootstrap:

```sh
GNOME_ASCII_SAVER_VERSION=v0.1.0 bash install-online.sh
```

The bootstrap also accepts `--version v0.1.0`. Run
`bash install-online.sh --help` for non-interactive and no-start options.

## Install from a Git clone

This route is useful for development or for reviewing the complete source:

```sh
git clone https://github.com/RobbyBobby77/gnome-ascii-saver.git
cd gnome-ascii-saver
./scripts/dependency-hint.sh
./install.sh
```

The dependency helper only prints a package-manager command. Run that command
yourself if dependencies are missing, then rerun `./install.sh`.

To validate required commands and GTK/VTE bindings without installing:

```sh
./install.sh --check
```

## Installed files

The defaults are shown below. XDG environment variables override data and
configuration roots where noted.

| Purpose | Default path |
| --- | --- |
| Application and isolated environment | `~/.local/share/gnome-ascii-saver/` (`XDG_DATA_HOME`) |
| GNOME Shell extension | `~/.local/share/gnome-shell/extensions/gnome-ascii-saver@robbybobby77.github.io/` |
| Artwork and visual configuration | `~/.config/gnome-ascii-saver/` (`XDG_CONFIG_HOME`) |
| Optional fallback user service | `~/.config/systemd/user/gnome-ascii-saver.service` |
| Launchers | `~/.local/bin/gnome-ascii-saver*` |
| Desktop entry | `~/.local/share/applications/io.github.RobbyBobby77.GnomeAsciiSaver.desktop` |

Python packages are installed into the application environment, never the
global interpreter.

## Finish extension loading

The installer enables the extension. GNOME Shell may not load newly installed
extension code into the current session, especially on Wayland. When the
installer asks you to, log out and back in once, then verify:

```sh
gnome-extensions info gnome-ascii-saver@robbybobby77.github.io
gnome-ascii-saverctl status
gnome-ascii-saverctl preview
```

Do not restart GNOME Shell with `Alt`+`F2`, `r` on Wayland; that restart method
is an X11-only GNOME feature. A normal logout/login is the reliable path.

On desktops with a systemd user manager, a fallback watcher can cover the
interval before the native extension loads. The extension stops that service
when it becomes active. Without systemd, automatic activation begins after the
extension is loaded; there is no second autostart mechanism to configure.

## Upgrade

Rerun the online install command to install the current stable release. The
installer stages replacement application files and refreshes the extension and
idle integration while preserving:

```text
~/.config/gnome-ascii-saver/config.json
~/.config/gnome-ascii-saver/logo.txt
```

If replacement fails, the prior application and integration state are
restored. GNOME Shell may still require a logout/login before it loads updated
extension JavaScript.

For a Git clone, update and rerun the installer:

```sh
git pull --ff-only
./install.sh
```

Review release notes before upgrading. To return to an older release, use the
pinned-version command above. Back up the configuration directory first when
moving backward, because an older release may not understand newer settings.

## Uninstall

From any directory after installation:

```sh
gnome-ascii-saverctl uninstall
```

Or, from a source checkout:

```sh
./uninstall.sh
```

Both methods disable and remove the extension, stop the renderer and fallback,
and remove installed program files. They preserve your configuration and
artwork. Remove that directory separately only if you no longer want it:

```sh
rm -r -- "${XDG_CONFIG_HOME:-$HOME/.config}/gnome-ascii-saver"
```

That final command is irreversible unless the directory is backed up. A logout
and login may be needed for GNOME Shell to fully discard already-loaded
extension code after removal.

## Offline installation

Download a release archive and its `.sha256` file on a connected computer,
verify the checksum there, and transfer both files to the GNOME system. Extract
the verified archive and run `./install.sh`. System dependencies and the Python
package listed in `requirements.txt` must already be available; otherwise the
normal installer may need network access to create its isolated environment.
