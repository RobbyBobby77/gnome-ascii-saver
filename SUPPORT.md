# Support

## Before opening an issue

Read the [installation guide](docs/INSTALLATION.md) and
[troubleshooting guide](docs/TROUBLESHOOTING.md), then search existing issues.
Many first-session extension problems are resolved by logging out and back in
after installation.

Collect only focused diagnostics:

```sh
gnome-ascii-saverctl --version
gnome-ascii-saverctl status
gnome-extensions info gnome-ascii-saver@robbybobby77.github.io
printf 'session=%s desktop=%s\n' \
  "${XDG_SESSION_TYPE:-unset}" "${XDG_CURRENT_DESKTOP:-unset}"
```

If `status` names the fallback service, include the smallest useful excerpt
from:

```sh
journalctl --user -u gnome-ascii-saver.service -b
```

## Bug reports

Use the bug-report form and include:

- GNOME ASCII Saver version;
- distribution and GNOME Shell version;
- Wayland or X11 session;
- monitor count, layout, resolution, scale, and rotation where relevant;
- systemd or non-systemd user session;
- extension and fallback state;
- minimal reproduction steps, expected behavior, and actual behavior; and
- a short, relevant log excerpt.

Mark untested cases as untested. Do not infer X11 behavior from Wayland or
single-monitor behavior from a windowed preview.

## Feature requests

Describe the user problem first, the smallest useful behavior, and alternatives
you considered. Proposals must preserve GNOME's lock screen as a separate,
authoritative security boundary.

## Privacy and security

Redact usernames, hostnames, tokens, private paths, notifications, and custom
artwork. Never post a full environment dump or unrelated journal output.

Do not open a public issue for a suspected vulnerability, lock-screen bypass,
unsafe installer behavior, or command execution issue. Follow the private
instructions in [SECURITY.md](SECURITY.md).

Support is community-provided on a best-effort basis. The latest release and
default branch receive priority; distribution packaging and downstream patches
may need support from their maintainers.
