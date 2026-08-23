# Release and acceptance checklist

This checklist separates automated confidence from behavior that must be
observed in real GNOME sessions. Copy
[the acceptance template](ACCEPTANCE-TEMPLATE.md) for each candidate and record
the distribution, Shell version, session protocol, monitor arrangement, init
system, and result of every available case.

The current private preview evidence is recorded in
[the 0.1.0 acceptance record](ACCEPTANCE-0.1.0.md).

## Repository and documentation

- [ ] `VERSION`, extension `version-name`, changelog heading, tag, and release title agree.
- [ ] The working tree is clean and the release commit is on the default branch.
- [ ] CI passes on every supported validation image.
- [ ] README install commands work from a clean account.
- [ ] Documentation links and GitHub issue forms render correctly.
- [ ] Dependency commands match supported distribution releases.
- [ ] Release notes identify breaking configuration or dependency changes.
- [ ] No secrets, private URLs, build trees, virtual environments, or user config are present.

## Automated validation

- [ ] Python compilation and unit tests pass.
- [ ] Shell syntax, JSON, extension metadata, and GSettings schemas validate.
- [ ] GNOME extension JavaScript parses successfully.
- [ ] GTK 4 and VTE 3.91 imports pass in CI.
- [ ] Versioned and generic release archives and matching `.sha256` files are produced from the tagged commit.
- [ ] The online bootstrap rejects a deliberately incorrect checksum.
- [ ] Clean-environment install, upgrade, rollback, and uninstall tests pass.
- [ ] Release artifacts contain expected source and no unexpected files.

## GNOME Wayland acceptance

- [ ] Install in a clean user account.
- [ ] Extension loads after the documented logout/login path.
- [ ] Manual fullscreen launch and decorated preview both work.
- [ ] Idle timeout launches once and input dismisses every surface.
- [ ] Keyboard, pointer motion, click, and scroll each dismiss the saver.
- [ ] Manual lock removes the saver before authentication appears.
- [ ] Automatic lock removes the saver.
- [ ] Unlocking does not permanently suppress the next idle launch.
- [ ] One monitor is fully covered with correct focus and input behavior.
- [ ] Multiple monitors receive one correctly placed surface each.
- [ ] Mixed scale factors and rotations render correctly when hardware is available.
- [ ] Monitor hotplug adds and removes surfaces without leaving an overlay.
- [ ] Extension preferences update automatic activation and delay.

## GNOME X11 acceptance

- [ ] Repeat install and extension activation on a clean X11 login.
- [ ] Repeat manual launch, preview, idle launch, and every dismissal input.
- [ ] Repeat manual and automatic lock-screen handoff tests.
- [ ] Test one and multiple monitors using representative layouts.
- [ ] Test mixed scaling, rotation, and monitor hotplug when available.
- [ ] Confirm extension settings and renderer lifecycle after Shell restart.

## Integration and preservation

- [ ] Test the systemd fallback from install through extension takeover.
- [ ] Confirm the extension and fallback are never active watchers together.
- [ ] Test a live non-systemd GNOME session through logout/login.
- [ ] Reinstalling and upgrading do not create duplicate watchers.
- [ ] `disable`, `enable`, `delay`, `edit`, `prefs`, and `status` behave as documented.
- [ ] Upgrade preserves modified `config.json` and `logo.txt`.
- [ ] A simulated failed upgrade restores the prior version and integration state.
- [ ] A pinned older release can be installed as a documented rollback.
- [ ] Uninstall stops processes and removes application and extension files.
- [ ] Uninstall preserves modified configuration and artwork.
- [ ] Reinstall after uninstall reuses preserved configuration.

## Public release

- [ ] Real GNOME results and untested combinations are stated in release notes.
- [ ] The tag is signed or otherwise traceable to the reviewed release commit.
- [ ] GitHub release archives and `.sha256` files are published together.
- [ ] The public command downloads and verifies the published artifact.
- [ ] Install once using the public command after publication.
- [ ] Capture a real screenshot or short recording; do not advertise a placeholder.
- [ ] Privacy-review media for artwork, usernames, notifications, and personal data.
- [ ] Enable private vulnerability reporting and apply repository protections.
