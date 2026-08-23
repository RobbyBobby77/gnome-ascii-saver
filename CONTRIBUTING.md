# Contributing

Thanks for helping improve GNOME ASCII Saver. Keep changes focused, preserve
GNOME's lock-screen behavior, and test both the native extension and fallback
paths when changing idle integration. Participation is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Local setup

Fork or clone the repository, use a feature branch, and install the packages
listed for your distribution:

```sh
git clone https://github.com/RobbyBobby77/gnome-ascii-saver.git
cd gnome-ascii-saver
./scripts/dependency-hint.sh
./install.sh
```

The dependency helper only prints a package-manager command; it does not run
`sudo` or modify the system.

## Validation

Before opening a pull request, run the static checks used by CI:

```sh
python3 -m py_compile app.py ctl.py watcher.py helpers.py \
  tests/test_helpers.py tests/test_ctl.py
python3 -m unittest discover -s tests -t . -v
bash -n install.sh uninstall.sh bin/gnome-ascii-saver \
  bin/gnome-ascii-saverctl bin/gnome-ascii-saver-watcher \
  install-online.sh scripts/build-release.sh \
  scripts/dependency-hint.sh tests/test_installers.sh
python3 -m json.tool config/config.json >/dev/null
python3 -m json.tool extension/metadata.json >/dev/null
glib-compile-schemas --strict --dry-run extension/schemas
node --input-type=module --check <extension/extension.js
node --input-type=module --check <extension/prefs.js
```

Run installer/release tests when those paths are affected:

```sh
tests/test_installers.sh
```

Then perform a runtime smoke test inside a GNOME session:

```sh
gnome-ascii-saverctl status
gnome-ascii-saverctl preview
gnome-ascii-saverctl start
```

Confirm that each relevant input dismisses fullscreen mode, GNOME's lock screen
still takes precedence, and `status` reports either the extension or fallback
as active—not both. Use [the acceptance template](docs/ACCEPTANCE-TEMPLATE.md)
for release-candidate testing.

## Project invariants

- `VERSION` and `extension/metadata.json` `version-name` must agree.
- The stable extension UUID is
  `gnome-ascii-saver@robbybobby77.github.io`; changing it creates a different
  extension identity and migration problem.
- User artwork and configuration must survive install, upgrade, rollback, and
  uninstall unless the user explicitly removes them.
- The saver remains decorative and must not replace, inhibit, unlock, or
  reconfigure GNOME's lock screen.
- Installation remains user-local and must not invoke `sudo` or a package
  manager.
- Only one automatic idle integration may be active at a time.

`GNOME_ASCII_SAVER_CONFIG_DIR`, `GNOME_ASCII_SAVER_DATA_DIR`, and
`GNOME_ASCII_SAVER_TTE` override renderer paths for isolated tests.

## Pull requests

Describe user-visible behavior, implementation choices, and tests performed.
For desktop changes include the GNOME Shell version, display protocol, monitor
layout, scale factors, distribution, and init system. Mark unavailable manual
cases as untested; do not mark them as passing.

Keep commits focused. Do not commit generated schemas, virtual environments,
release archives, logs, screenshots containing personal data, or custom
artwork unless it is an intentional change to the project default.

Security-sensitive reports must follow [SECURITY.md](SECURITY.md).
