# Security policy

## Supported versions

Security fixes are applied to the latest release and default branch during the
initial 0.x series. Older releases may receive fixes only when a practical
backport is available. Check the current release before reporting a problem.

## Important boundary

GNOME ASCII Saver is decorative software. It does not provide authentication,
screen locking, session inhibition, or protection from local access. GNOME's
own lock screen remains the security boundary and must be configured
independently in system settings.

The saver intentionally exits on user input and does not request elevated
privileges. Installation writes only to the current user's XDG data and config
locations, `~/.local/bin`, the user extension directory, and the optional
systemd user-unit directory. It never invokes `sudo` or a system package
manager.

## Installation trust boundary

The recommended bootstrap is delivered from this repository, selects a tagged
GitHub release, downloads its archive and published SHA-256 file, verifies the
archive, and runs that release's installer. A checksum protects against damage
and accidental mismatch; it does not make a compromised repository or GitHub
release trustworthy. Users who need a stronger review boundary should download
the bootstrap and release assets separately, inspect them, verify the checksum,
and then install.

Runtime Python packages are version-pinned and hash-verified from
`requirements.txt` into an application-local virtual environment. The project
does not collect telemetry or upload configuration or artwork.

## Reporting a vulnerability

Use GitHub's private vulnerability-reporting feature:

<https://github.com/RobbyBobby77/gnome-ascii-saver/security/advisories/new>

Include the affected version, GNOME Shell version, Wayland/X11 session,
reproduction steps, impact, and any suggested mitigation. Do not open a public
issue for an unresolved vulnerability. In particular, privately report:

- behavior that could cover or interfere with lock-screen authentication;
- unsafe archive extraction, checksum bypass, or installer command execution;
- signaling or deleting files belonging to another process or application; and
- a path by which untrusted configuration becomes unintended code execution.

Redact tokens, usernames, hostnames, private artwork, and unrelated logs. You
should receive acknowledgement through GitHub; public disclosure should be
coordinated after a fix or mitigation is available.
