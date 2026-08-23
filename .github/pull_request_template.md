## Summary

Describe the user-visible and technical changes. Link related issues and
explain why this approach was chosen.

## Validation

- [ ] Python and shell tests pass
- [ ] Extension metadata, JavaScript, and schemas validate
- [ ] Installer/release tests pass, or are not affected
- [ ] Renderer preview works
- [ ] Idle launch and each relevant input dismissal were tested
- [ ] GNOME lock-screen handoff was tested
- [ ] Wayland was tested, or marked unavailable
- [ ] X11 was tested, or marked unavailable
- [ ] Multi-monitor behavior was tested, or marked unavailable
- [ ] Extension/fallback lifecycle was tested, or is not affected

List commands, distribution, GNOME Shell version, session protocol, init
system, and monitor arrangement. Mark unavailable manual cases as untested; do
not mark them as passing.

## Security

Confirm that the change does not weaken, inhibit, replace, unlock, or
reconfigure GNOME's lock screen. Describe changes to installer, process, path,
or release trust boundaries.

## Documentation and privacy

- [ ] User-visible behavior and installation changes are documented
- [ ] Logs and media contain no secrets or private information
- [ ] User configuration and artwork preservation were considered
