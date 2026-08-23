# Release acceptance record template

Copy this file to `ACCEPTANCE-<version>.md` for a release candidate. Replace
every placeholder, remove cases that truly do not apply with an explanation,
and leave unavailable cases explicitly untested. Automated success does not
substitute for observing desktop behavior.

## Candidate

- Version/tag: `<version>`
- Commit: `<full commit SHA>`
- Date: `<YYYY-MM-DD>`
- Tester: `<name or handle>`

## Environment

- Distribution: `<name and release>`
- GNOME Shell: `<version>`
- Session: `<Wayland or X11>`
- Init/user manager: `<systemd or other>`
- Displays: `<connectors, resolutions, refresh rates, scale factors, layout>`
- Hardware notes: `<GPU, dock, VM, remote session, or none>`

## Automated validation

- CI run: `<link>`
- Installer/release test result: `<pass/fail and command>`
- Release archive/checksum: `<artifact name and SHA-256>`

## Desktop results

Use `pass`, `fail`, or `untested` and add concise evidence.

| Case | Result | Evidence or notes |
| --- | --- | --- |
| Clean install | `<result>` | `<notes>` |
| Extension activation/reload | `<result>` | `<notes>` |
| Decorated preview | `<result>` | `<notes>` |
| Manual fullscreen | `<result>` | `<notes>` |
| Automatic idle launch | `<result>` | `<notes>` |
| Keyboard dismissal | `<result>` | `<notes>` |
| Pointer-motion dismissal | `<result>` | `<notes>` |
| Click dismissal | `<result>` | `<notes>` |
| Scroll dismissal | `<result>` | `<notes>` |
| Manual lock handoff | `<result>` | `<notes>` |
| Automatic lock handoff | `<result>` | `<notes>` |
| Unlock and re-arm | `<result>` | `<notes>` |
| Multiple monitors | `<result>` | `<notes>` |
| Mixed scale/rotation | `<result>` | `<notes>` |
| Monitor hotplug | `<result>` | `<notes>` |
| Preferences and controller | `<result>` | `<notes>` |
| Upgrade preservation | `<result>` | `<notes>` |
| Rollback | `<result>` | `<notes>` |
| Uninstall preservation | `<result>` | `<notes>` |

## Integration observations

- Extension state: `<state>`
- Fallback state: `<state or unavailable>`
- Duplicate watcher check: `<result>`
- Relevant logs: `<small redacted excerpt or link>`

## Remaining gaps

- `<untested protocol, Shell version, hardware, or lifecycle case>`

## Release assessment

State whether this evidence supports a preview, prerelease, or stable claim and
why. Never imply coverage for an untested GNOME version, session protocol, or
monitor arrangement.
