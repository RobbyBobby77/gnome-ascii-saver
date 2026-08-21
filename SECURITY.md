# Security policy

## Supported versions

Security fixes are applied to the latest code on the default branch while the
project is in its initial 0.x series.

## Important boundary

GNOME ASCII Saver is decorative software. It does not provide authentication,
screen locking, session inhibition, or protection from local access. GNOME's
own lock screen remains the security boundary and should be configured
independently in the system settings.

The saver intentionally exits on user input and does not request elevated
privileges. Installation writes only to the current user's XDG data and config
locations, `~/.local/bin`, and the systemd user-unit directory. The only
downloaded runtime dependency is installed into the application's isolated
Python environment from the package index.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting feature for this
repository. Include the affected version, GNOME Shell version, reproduction
steps, impact, and any suggested mitigation. Do not open a public issue for an
unresolved vulnerability.
