# GNOME ASCII Saver 0.1.0 acceptance record

This record separates automated launch-readiness checks from behavior observed
in a real GNOME session. The available host was not running GNOME, so no live
GNOME desktop result is inferred from CI or from KDE behavior.

## Candidate

- Version: `0.1.0` (untagged preview candidate)
- Reviewed commit: `c58ca49acd9aab45d3c645bff104e6d2ed886f39`
- Date: 2026-08-22 (America/Los_Angeles)
- Repository state: private; no tag or GitHub release created

## Available environment

- Distribution: CachyOS (Arch-family rolling release)
- Desktop: KDE Plasma 6.7.4
- Session: Wayland
- Display: one built-in `eDP-1`, 2560x1600 at 180 Hz, 1.6 scale
- GNOME Shell: unavailable on this host
- GNOME extension tooling: unavailable on this host

Because this is not a GNOME session, installing or launching the extension here
would not exercise its actual Shell lifecycle and was intentionally skipped.

## Passed automated validation

- 78 Python lifecycle, controller, watcher, configuration, and process-safety tests
- Python bytecode compilation and shell syntax checks
- strict GSettings schema, JSON, desktop-entry, and YAML validation
- stable extension UUID and GTK application-ID consistency checks
- initial lock-state gate, lock activation, lock-service loss, and monitor-model tests
- exact renderer process identity and pidfd-safe signaling tests
- extension/fallback mutual-exclusion and transition-state tests
- latest and pinned online bootstrap tests
- checksum-tampering and archive-traversal rejection
- transactional rollback and idempotent upgrade tests
- legacy UUID and desktop-entry migration
- configuration and artwork preservation
- symlink-safe uninstall behavior
- deterministic versioned and generic release archives with matching SHA-256 files
- exact committed release install, upgrade, and uninstall with TerminalTextEffects 0.15.0
- Fedora 44 and Debian 13 CI, including GNOME extension packing and GTK/VTE imports

Main-branch CI passed at:
<https://github.com/RobbyBobby77/gnome-ascii-saver/actions/runs/32613351261>

## Desktop acceptance

| Case | Result | Notes |
| --- | --- | --- |
| Clean install in GNOME | Untested | No GNOME session was available. |
| Extension activation/reload | Untested | Packaging passed in CI only. |
| Decorated preview | Untested | Requires GTK/VTE in a GNOME user session. |
| Manual fullscreen | Untested | Requires a GNOME user session. |
| Automatic idle launch | Untested | Requires the GNOME idle monitor. |
| Keyboard dismissal | Untested | Unit-level capture-phase behavior passed. |
| Pointer-motion dismissal | Untested | Unit-level capture-phase behavior passed. |
| Click dismissal | Untested | Unit-level capture-phase behavior passed. |
| Scroll dismissal | Untested | Unit-level capture-phase behavior passed. |
| Manual lock handoff | Untested | Lock-state unit coverage passed; live behavior remains required. |
| Automatic lock handoff | Untested | Requires GNOME session policy and timing. |
| Unlock and idle re-arm | Untested | Requires a live GNOME session. |
| Multiple monitors | Untested | Monitor-model lifecycle tests passed only. |
| Mixed scale/rotation | Untested | Suitable GNOME hardware/session unavailable. |
| Monitor hotplug | Untested | Monitor-model lifecycle tests passed only. |
| Preferences and controller | Untested | Schema and controller automation passed. |
| systemd fallback takeover | Untested | State-transition automation passed. |
| Non-systemd integration | Untested | No non-systemd GNOME session was available. |
| GNOME X11 | Untested | No GNOME X11 session was available. |

## Assessment

The evidence supports a private `0.1.0` preview candidate and public-launch
infrastructure, not a stable desktop-compatibility claim. Before publication,
run the release checklist in at least one real supported GNOME Wayland session
and record extension loading, every dismissal input, idle activation, manual
and automatic lock handoff, unlock/re-arm, and available monitor behavior.
GNOME X11, multi-monitor, mixed-scale, hotplug, and non-systemd results must
remain explicitly untested until those environments are exercised.
