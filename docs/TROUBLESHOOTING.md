# Troubleshooting

## Collect status first

Run these commands in a terminal inside the affected GNOME session:

```sh
gnome-ascii-saverctl --version
gnome-ascii-saverctl status
gnome-extensions info gnome-ascii-saver@robbybobby77.github.io
printf 'session=%s desktop=%s runtime=%s\n' \
  "${XDG_SESSION_TYPE:-unset}" "${XDG_CURRENT_DESKTOP:-unset}" \
  "${XDG_RUNTIME_DIR:-unset}"
```

Do not post a complete environment dump. It can contain tokens and private
paths.

## The command is not found

Launchers are installed in `~/.local/bin`. Start a new login session or add the
directory to the current shell:

```sh
export PATH="$HOME/.local/bin:$PATH"
```

You can also run `$HOME/.local/bin/gnome-ascii-saverctl` directly.

## The extension is not active

Confirm that GNOME knows about the stable extension UUID:

```sh
gnome-extensions list | grep -F gnome-ascii-saver@robbybobby77.github.io
gnome-extensions enable gnome-ascii-saver@robbybobby77.github.io
gnome-extensions info gnome-ascii-saver@robbybobby77.github.io
```

If the extension was installed or upgraded in this GNOME session, log out and
back in. This is the normal reload path on Wayland. On X11, restarting Shell
with `Alt`+`F2`, `r` may work, but logout/login tests the same path users have
on both display protocols.

An `ERROR` state usually indicates incompatible extension JavaScript or schema
loading. Capture focused Shell logs:

```sh
journalctl --user -b -o cat | grep -iE 'gnome-ascii-saver|gnome-shell'
```

Rerun the current installer to replace incomplete extension files and compile
its schema.

## The fallback service is inactive

The systemd user service is only a fallback. It should be stopped when the
GNOME Shell extension is active. If both are inactive before the extension has
loaded, inspect:

```sh
systemctl --user status gnome-ascii-saver.service
journalctl --user -u gnome-ascii-saver.service -b
systemctl --user restart gnome-ascii-saver.service
```

The unit is scoped to GNOME and should not arm on another desktop. If
`systemctl --user` is unavailable, there is intentionally no fallback service;
log out and back in so GNOME Shell can load the extension.

## The preview or saver does not open

Test rendering independently from idle detection:

```sh
gnome-ascii-saverctl preview
```

If it fails silently, run the launcher in the foreground:

```sh
gnome-ascii-saver --windowed
```

Typical causes are missing GTK 4/VTE introspection bindings, a damaged Python
environment, or running outside a graphical session. From a source checkout,
review dependency guidance and reinstall:

```sh
./scripts/dependency-hint.sh
./install.sh
```

## Wayland or X11 behavior differs

Include `echo "$XDG_SESSION_TYPE"` in a report. Fullscreen and input delivery
are compositor-dependent, so test the failure in a normal GNOME session rather
than a nested or remote desktop first. The extension reload procedure differs:
Wayland requires logout/login; X11 may also support `Alt`+`F2`, `r`.

GNOME ASCII Saver never changes session protocol, display settings, lock
timing, or power settings.

## A monitor is missing or an overlay remains

Stop any current instance before retrying:

```sh
gnome-ascii-saverctl stop
gnome-ascii-saverctl start
```

The renderer creates one window per monitor and listens for monitor add/remove
events while active. If hotplug, mixed scaling, rotation, or docking leaves an
incorrect window, record the monitor layout, scale factors, protocol, GNOME
Shell version, and whether the layout changed before or after launch. Do not
claim a multi-monitor problem from a windowed preview; preview is intentionally
not equivalent to fullscreen placement.

## Configuration warnings or unexpected defaults

Validate the JSON syntax:

```sh
python3 -m json.tool \
  "${XDG_CONFIG_HOME:-$HOME/.config}/gnome-ascii-saver/config.json"
```

Invalid values are ignored with a warning. The accepted frame rate and color
formats are release-specific; compare your file with `config/config.json` from
the installed release. Preserve a copy before editing by hand.

## Lock-screen behavior

GNOME ASCII Saver should disappear when GNOME transitions to the lock screen,
but it does not control whether or when the desktop locks. Verify GNOME's own
lock settings independently. If the decorative saver remains above a locked
session or interferes with authentication, stop it, retain the smallest
relevant log excerpt, and follow the private reporting instructions in
[Security](../SECURITY.md).

## Ask for help

Search existing issues, then use the bug-report form. Include the project
version, distribution, GNOME Shell version, Wayland/X11 session, monitor setup,
extension state, reproduction steps, and a focused log excerpt. Redact
usernames, hostnames, tokens, artwork, notifications, and other private data.
See [Support](../SUPPORT.md).
