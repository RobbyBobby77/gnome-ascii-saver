#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
test_dir=$(mktemp -d "${TMPDIR:-/tmp}/gnome-ascii-saver-installer-test.XXXXXX")
cleanup() { rm -rf -- "$test_dir"; }
trap cleanup EXIT INT TERM HUP
fail() { printf 'installer test failed: %s\n' "$1" >&2; exit 1; }

# Build fake latest and pinned release endpoints and exercise verified download.
version=9.8.7
package_root="$test_dir/package/gnome-ascii-saver-$version"
release_root="$test_dir/releases"
specific_dir="$release_root/download/v$version"
latest_dir="$release_root/latest/download"
marker="$test_dir/installer-ran"
args_file="$test_dir/installer-args"
mkdir -p "$package_root" "$specific_dir" "$latest_dir" "$test_dir/download-tmp"
cat >"$package_root/install.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$@" >"$TEST_INSTALL_ARGS"
printf 'yes\n' >"$TEST_INSTALL_MARKER"
EOF
chmod 0755 "$package_root/install.sh"
tar -czf "$specific_dir/gnome-ascii-saver-$version.tar.gz" \
    -C "$test_dir/package" "gnome-ascii-saver-$version"
(
    cd -- "$specific_dir"
    sha256sum "gnome-ascii-saver-$version.tar.gz" \
        >"gnome-ascii-saver-$version.tar.gz.sha256"
)
cp -- "$specific_dir/gnome-ascii-saver-$version.tar.gz" \
    "$latest_dir/gnome-ascii-saver.tar.gz"
(
    cd -- "$latest_dir"
    sha256sum gnome-ascii-saver.tar.gz >gnome-ascii-saver.tar.gz.sha256
)

TEST_INSTALL_MARKER="$marker" TEST_INSTALL_ARGS="$args_file" \
GNOME_ASCII_SAVER_RELEASE_BASE_URL="file://$release_root" TMPDIR="$test_dir/download-tmp" \
    "$project_dir/install-online.sh" --version "v$version" --no-start --non-interactive
[[ -f "$marker" ]] || fail 'verified versioned archive did not run its installer'
mapfile -t forwarded_args <"$args_file"
[[ "${forwarded_args[*]}" == '--no-start --non-interactive' ]] || \
    fail 'bootstrap did not forward installer options'
if find "$test_dir/download-tmp" -mindepth 1 -print -quit | grep -q .; then
    fail 'bootstrap left its temporary download directory behind'
fi

rm -f -- "$marker" "$args_file"
TEST_INSTALL_MARKER="$marker" TEST_INSTALL_ARGS="$args_file" \
GNOME_ASCII_SAVER_RELEASE_BASE_URL="file://$release_root" TMPDIR="$test_dir/download-tmp" \
    "$project_dir/install-online.sh"
[[ -f "$marker" ]] || fail 'latest release alias did not run its installer'

rm -f -- "$marker"
printf '%064d  %s\n' 0 "gnome-ascii-saver-$version.tar.gz" \
    >"$specific_dir/gnome-ascii-saver-$version.tar.gz.sha256"
if TEST_INSTALL_MARKER="$marker" TEST_INSTALL_ARGS="$args_file" \
    GNOME_ASCII_SAVER_RELEASE_BASE_URL="file://$release_root" \
    "$project_dir/install-online.sh" --version "$version" >/dev/null 2>&1; then
    fail 'bootstrap accepted a bad checksum'
fi
[[ ! -e "$marker" ]] || fail 'installer ran after checksum failure'

# Reject archive traversal even with a valid matching checksum.
python3 - "$specific_dir/gnome-ascii-saver-$version.tar.gz" <<'PY'
import io
import sys
import tarfile
with tarfile.open(sys.argv[1], "w:gz") as archive:
    info = tarfile.TarInfo("../escape")
    payload = b"unsafe\n"
    info.size = len(payload)
    archive.addfile(info, io.BytesIO(payload))
PY
(
    cd -- "$specific_dir"
    sha256sum "gnome-ascii-saver-$version.tar.gz" \
        >"gnome-ascii-saver-$version.tar.gz.sha256"
)
if GNOME_ASCII_SAVER_RELEASE_BASE_URL="file://$release_root" \
    "$project_dir/install-online.sh" --version "$version" >/dev/null 2>&1; then
    fail 'bootstrap accepted an unsafe archive member'
fi
[[ ! -e "$test_dir/escape" ]] || fail 'unsafe archive escaped extraction directory'

# Exercise transactional upgrade, private-preview UUID migration, rollback,
# idempotency, config preservation, and safe uninstall with lightweight fakes.
fake_bin="$test_dir/fake-bin"
install_home="$test_dir/install-home"
install_data="$test_dir/install-data"
install_config="$test_dir/install-config"
extension_root="$install_data/gnome-shell/extensions"
stable_extension="$extension_root/gnome-ascii-saver@robbybobby77.github.io"
legacy_extension="$extension_root/gnome-ascii-saver@local"
mkdir -p "$fake_bin" "$install_data/gnome-ascii-saver" "$legacy_extension" \
    "$install_data/applications" "$install_config/gnome-ascii-saver" \
    "$install_home/.local/bin"
cat >"$fake_bin/python3" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == - ]]; then
    while IFS= read -r _line; do :; done
elif [[ "${1:-}" == -m && "${2:-}" == venv ]]; then
    destination=${!#}
    mkdir -p "$destination/bin"
    cp -- "$0" "$destination/bin/python"
    chmod 0755 "$destination/bin/python"
elif [[ "${1:-}" == -m && "${2:-}" == pip ]]; then
    printf '%s\n' '#!/nonexistent/staged/python' >"$(dirname -- "$0")/tte"
    chmod 0755 "$(dirname -- "$0")/tte"
else
    exit 2
fi
EOF
cat >"$fake_bin/glib-compile-schemas" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
destination=${!#}
touch "$destination/gschemas.compiled"
EOF
cat >"$fake_bin/gnome-extensions" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
cat >"$fake_bin/sed" <<'EOF'
#!/usr/bin/env bash
if [[ "${TEST_SED_FAIL:-0}" == 1 ]]; then exit 1; fi
exec /usr/bin/sed "$@"
EOF
chmod 0755 "$fake_bin/python3" "$fake_bin/glib-compile-schemas" \
    "$fake_bin/gnome-extensions" "$fake_bin/sed"

printf 'old application\n' >"$install_data/gnome-ascii-saver/old-marker"
printf 'legacy extension\n' >"$legacy_extension/old-marker"
printf 'custom art\n' >"$install_config/gnome-ascii-saver/logo.txt"
printf '{"idle_delay": 777}\n' >"$install_config/gnome-ascii-saver/config.json"
printf 'old launcher\n' >"$install_home/.local/bin/gnome-ascii-saver"
printf 'legacy desktop\n' \
    >"$install_data/applications/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop"
install_env=(
    HOME="$install_home"
    XDG_DATA_HOME="$install_data"
    XDG_CONFIG_HOME="$install_config"
    XDG_RUNTIME_DIR="$test_dir/no-systemd-runtime"
    GNOME_ASCII_SAVER_NO_SESSION=1
    PATH="$fake_bin:$PATH"
)

if env "${install_env[@]}" TEST_SED_FAIL=1 "$project_dir/install.sh" >/dev/null 2>&1; then
    fail 'installer did not report a staged upgrade failure'
fi
[[ -f "$install_data/gnome-ascii-saver/old-marker" ]] || \
    fail 'failed upgrade did not restore old application'
[[ -f "$legacy_extension/old-marker" ]] || \
    fail 'failed upgrade did not restore legacy extension'
[[ $(<"$install_home/.local/bin/gnome-ascii-saver") == 'old launcher' ]] || \
    fail 'failed upgrade did not restore managed launcher'

env "${install_env[@]}" "$project_dir/install.sh" >/dev/null
[[ ! -e "$install_data/gnome-ascii-saver/old-marker" ]] || \
    fail 'successful upgrade kept old application payload'
[[ -x "$install_data/gnome-ascii-saver/uninstall.sh" ]] || \
    fail 'successful install did not include hardened uninstaller'
[[ -f "$stable_extension/metadata.json" ]] || fail 'stable extension was not installed'
[[ ! -e "$legacy_extension" ]] || fail 'legacy extension directory survived migration'
[[ -f "$install_data/applications/io.github.RobbyBobby77.GnomeAsciiSaver.desktop" ]] || \
    fail 'stable desktop entry was not installed'
[[ ! -e "$install_data/applications/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop" ]] || \
    fail 'legacy desktop entry survived migration'
[[ $(<"$install_config/gnome-ascii-saver/logo.txt") == 'custom art' ]] || \
    fail 'upgrade overwrote custom art'
[[ $(<"$install_config/gnome-ascii-saver/config.json") == '{"idle_delay": 777}' ]] || \
    fail 'upgrade overwrote configuration'
grep -q 'python" -m terminaltexteffects' "$install_data/gnome-ascii-saver/venv/bin/tte" || \
    fail 'staged TTE launcher was not made relocatable'

env "${install_env[@]}" "$project_dir/install.sh" >/dev/null

HOME="$install_home" XDG_DATA_HOME="$install_data" XDG_CONFIG_HOME="$install_config" \
GNOME_ASCII_SAVER_NO_SESSION=1 "$project_dir/uninstall.sh" >/dev/null
[[ ! -e "$install_data/gnome-ascii-saver" ]] || fail 'uninstaller left app data behind'
[[ ! -e "$stable_extension" ]] || fail 'uninstaller left extension data behind'
[[ -f "$install_config/gnome-ascii-saver/logo.txt" ]] || \
    fail 'uninstaller removed custom art'
[[ -f "$install_config/gnome-ascii-saver/config.json" ]] || \
    fail 'uninstaller removed configuration'

# Unexpected symlink targets are never followed or removed.
outside="$test_dir/outside"
mkdir -p "$outside"
printf 'keep\n' >"$outside/marker"
ln -s "$outside" "$install_data/gnome-ascii-saver"
if HOME="$install_home" XDG_DATA_HOME="$install_data" XDG_CONFIG_HOME="$install_config" \
    GNOME_ASCII_SAVER_NO_SESSION=1 "$project_dir/uninstall.sh" >/dev/null 2>&1; then
    fail 'uninstaller accepted an unexpected application symlink'
fi
[[ -f "$outside/marker" ]] || fail 'uninstaller followed an unexpected symlink'

printf 'Installer tests passed.\n'
