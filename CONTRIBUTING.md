# Contributing

Thanks for helping improve GNOME ASCII Saver. Keep changes focused, preserve
GNOME's lock-screen behavior, and test both the native extension path and the
fallback watcher when changing idle integration.

## Local setup

Use the dependency helper, then install the packages it lists for the current
distribution:

```sh
./scripts/dependency-hint.sh
git clone git@github.com:RobbyBobby77/gnome-ascii-saver.git
cd gnome-ascii-saver
./install.sh
```

Use a feature branch and make small commits. Before opening a pull request,
run the same static checks used by CI:

```sh
python3 -m py_compile app.py ctl.py watcher.py helpers.py \
  tests/test_helpers.py tests/test_ctl.py
python3 -m unittest discover -s tests -t . -v
bash -n install.sh uninstall.sh bin/gnome-ascii-saver \
  bin/gnome-ascii-saverctl bin/gnome-ascii-saver-watcher \
  scripts/dependency-hint.sh
python3 -m json.tool config/config.json >/dev/null
python3 -m json.tool extension/metadata.json >/dev/null
glib-compile-schemas --strict --dry-run extension/schemas
node --input-type=module --check <extension/extension.js
node --input-type=module --check <extension/prefs.js
```

Then perform a runtime smoke test from a GNOME Wayland session:

```sh
gnome-ascii-saverctl status
gnome-ascii-saverctl preview
gnome-ascii-saverctl start
```

Confirm that keyboard and pointer activity dismiss fullscreen mode, GNOME's
lock screen still activates normally, and `status` reports either the native
extension or the fallback service—not both.

Keep `VERSION` and `extension/metadata.json` `version-name` identical; the unit
tests assert that. There is no build step to rewrite metadata.

`GNOME_ASCII_SAVER_CONFIG_DIR`, `GNOME_ASCII_SAVER_DATA_DIR`, and
`GNOME_ASCII_SAVER_TTE` override renderer paths for tests.

`./uninstall.sh` and `gnome-ascii-saverctl uninstall` perform the same removal
steps. The script execs the installed controller when it is present.

## Pull requests

Describe the visible behavior, GNOME Shell version, display protocol, monitor
layout, distribution, init system, and tests you ran. Never commit generated schemas, virtual
environments, archives, logs, or personal artwork unless it is an intentional
change to the project default.

Security-sensitive reports should follow [SECURITY.md](SECURITY.md).
