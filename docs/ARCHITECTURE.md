# Architecture

GNOME ASCII Saver separates idle detection from rendering. GNOME Shell owns
the preferred idle integration; on systemd desktops, a user service provides
continuity when a newly installed extension cannot be loaded until the next
session.

## Process model

```text
GNOME Shell
  └─ gnome-ascii-saver@local
       ├─ observes Meta.IdleMonitor
       ├─ stops the fallback service while active
       └─ launches app.py at the configured threshold

systemd --user (optional fallback only)
  └─ gnome-ascii-saver-watcher
       └─ watcher.py
            ├─ polls Mutter's idle-monitor D-Bus API
            ├─ observes org.gnome.ScreenSaver lock state
            └─ launches app.py at the configured threshold

app.py
  ├─ creates one Gtk.ApplicationWindow per GDK monitor
  └─ embeds one Vte.Terminal per window
       └─ runs TerminalTextEffects against logo.txt
```

The installer enables the user unit so idle activation works during the
pre-logout window. After login, the extension stops the fallback in
`enable()` and does **not** start it from `disable()`. GNOME calls `disable()`
on lock-screen teardown and when the user turns the extension off; starting
the watcher in those cases would cover the lock screen or keep a screensaver
armed after the extension was disabled. The unit remains enabled, so a later
graphical session can still start the watcher until the extension loads and
stops it. The installer also stops the fallback after confirming the extension
is already active. If no systemd user manager is available, no fallback unit is
installed and the native extension becomes active after the next GNOME login.

## Renderer lifecycle

`app.py` records its process ID in the XDG runtime directory. Each monitor gets
a borderless fullscreen window and an independent animation process. When an
effect finishes, another random effect begins. Input controllers on every
window request a single application-wide shutdown.

There is a short input-arming delay during startup so the pointer event that
helped reveal the window does not immediately dismiss it. `--windowed` skips
fullscreen mode for safe previews, and `--once` exits after one effect for
automated or manual smoke tests.

## Configuration

Extension settings use the schema
`org.gnome.shell.extensions.gnome-ascii-saver`:

- `enabled`: whether idle activation is armed.
- `idle-delay`: activation threshold in seconds, from 10 through 86400.

Visual configuration and artwork are intentionally ordinary user files under
`$XDG_CONFIG_HOME/gnome-ascii-saver`. The installer creates defaults only when
those files do not already exist.

## Installed paths

Defaults are shown below; XDG environment variables are honored where noted.

| Purpose | Default path |
| --- | --- |
| Runtime and isolated environment | `~/.local/share/gnome-ascii-saver/` |
| GNOME Shell extension | `~/.local/share/gnome-shell/extensions/gnome-ascii-saver@local/` |
| Artwork and visual config | `~/.config/gnome-ascii-saver/` |
| Optional user service | `~/.config/systemd/user/gnome-ascii-saver.service` |
| Launchers | `~/.local/bin/gnome-ascii-saver*` |
| Desktop entry | `~/.local/share/applications/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop` |
| PID file | `$XDG_RUNTIME_DIR/gnome-ascii-saver-$UID.pid` (never world-writable `/tmp`) |

## Lock-screen behavior

No component calls GNOME's lock or inhibit APIs. GNOME Shell disables ordinary
user-session extensions when transitioning to its lock-screen session mode;
the renderer is stopped during extension disable, and the fallback is not
started from that teardown. The fallback independently checks
`org.gnome.ScreenSaver.GetActive` and will not launch when the session is
locked. If that call fails, lock state is treated as unknown and the overlay
is not started (fail closed). The user unit is GNOME-scoped
(`After=gnome-session.target`, a GNOME `XDG_CURRENT_DESKTOP` check) so it does
not arm under other desktops.

## Compatibility and testing

The metadata declares GNOME Shell 45–50. The current live test environment is
GNOME Shell 50 on Wayland. Changes to GNOME Shell JavaScript APIs should be
feature-detected when practical and exercised on every declared major version
before a stable release. CI validates the portable source and declared runtime
libraries on both Fedora and Debian; see [Distributions](DISTRIBUTIONS.md).
