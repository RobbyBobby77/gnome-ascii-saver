# Distribution support

GNOME ASCII Saver does not depend on Fedora-specific APIs or filesystem paths.
It needs a GNOME Shell version declared in `extension/metadata.json`, Python 3,
GTK 4, PyGObject, the GTK4 build of VTE (`Vte 3.91`), GLib schema tools, and a
working Python virtual-environment module.

The installer never runs `sudo` or invokes a system package manager. Run the
matching command yourself, review the packages, and then run `./install.sh`.
`./scripts/dependency-hint.sh` prints the appropriate known command based on
`/etc/os-release`.

## Known package commands

### Fedora and RPM-family desktops

```sh
sudo dnf install python3 python3-gobject gtk4 vte291-gtk4 gnome-shell glib2 desktop-file-utils
```

### Debian 13 and compatible Ubuntu releases

```sh
sudo apt update
sudo apt install python3 python3-gi python3-venv gir1.2-gtk-4.0 \
  gir1.2-vte-3.91 gnome-shell libglib2.0-bin desktop-file-utils
```

### Arch, EndeavourOS, and Manjaro

```sh
sudo pacman -S --needed python python-gobject gtk4 vte4 gnome-shell glib2 \
  desktop-file-utils
```

### openSUSE Tumbleweed

```sh
sudo zypper install python3 python3-gobject typelib-1_0-Gtk-4_0 \
  typelib-1_0-Vte-3_91 gnome-shell glib2-tools desktop-file-utils
```

Package availability on fixed-release enterprise derivatives may lag behind
the GNOME 45–50 compatibility window. In that case, use the distribution's
backports or wait for its supported desktop stack; do not mix core GNOME
libraries from unrelated releases.

## Other distributions

Map these runtime capabilities to the native package manager:

- `python3` with `venv` and `pip` support;
- the `gi` Python module;
- introspection namespaces `Gtk 4.0` and `Vte 3.91`;
- `glib-compile-schemas`;
- `gnome-extensions` and a compatible GNOME Shell; and
- `desktop-file-utils` (recommended, not required).

Then run:

```sh
./install.sh
gnome-ascii-saverctl status
gnome-ascii-saverctl preview
```

NixOS and other declarative/read-only systems should provide the dependencies
through their native environment or package definition before running the
user-level installer. Flatpak is not a drop-in packaging option because the
GNOME Shell extension and session idle APIs intentionally live outside an app
sandbox.

## Init systems

The native GNOME Shell extension works independently of the system init. When
`systemctl --user` is available, the installer also enables a fallback watcher
so idle activation works before the first logout/login and during extension
reloads. Without a systemd user manager, the installer skips that fallback and
prints a reminder to log out and back in if Shell cannot activate the new
extension immediately.

## Validation levels

- Fedora 44 and Debian 13 are continuously checked for syntax, metadata,
  schema compilation, extension packaging, and GTK/VTE bindings.
- GNOME Shell 50 on Fedora Wayland has live runtime coverage.
- Other listed distributions are package-mapped but still need desktop runtime
  acceptance reports, especially across GNOME Shell major versions.
