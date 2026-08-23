#!/usr/bin/env bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
app_dir="$data_home/gnome-ascii-saver"
uuid=gnome-ascii-saver@robbybobby77.github.io
legacy_uuid=gnome-ascii-saver@local
extension_root="$data_home/gnome-shell/extensions"
extension_dir="$extension_root/$uuid"
legacy_extension_dir="$extension_root/$legacy_uuid"
bin_dir="$HOME/.local/bin"
systemd_dir="$config_home/systemd/user"
applications_dir="$data_home/applications"
desktop_file="$applications_dir/io.github.RobbyBobby77.GnomeAsciiSaver.desktop"
legacy_desktop_file="$applications_dir/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop"
manage_session=true
check_only=false
has_user_systemd=false
transaction_dir=
staged_app=
staged_extension=
backup_app=
backup_extension=
backup_legacy_extension=
app_swapped=false
extension_swapped=false
old_app_moved=false
old_extension_moved=false
legacy_extension_moved=false
install_complete=false
service_was_active=false
extension_was_active=false
legacy_extension_was_active=false
session_touched=false

usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Install GNOME ASCII Saver for the current user.

Options:
  --check             Check required system dependencies without installing
  --no-start          Do not stop, enable, start, or reload session services
  --non-interactive   Accepted for unattended installs (the installer never prompts)
  -h, --help          Show this help

Set GNOME_ASCII_SAVER_NO_SESSION=1 for the same behavior as --no-start. This
is useful with an isolated HOME/XDG environment in installer and package tests.
EOF
}

while (($#)); do
    case "$1" in
        --check) check_only=true ;;
        --no-start) manage_session=false ;;
        --non-interactive) ;;
        -h|--help) usage; exit 0 ;;
        *)
            printf 'Unknown option: %s\n\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

case "${GNOME_ASCII_SAVER_NO_SESSION:-0}" in
    1|true|TRUE|yes|YES) manage_session=false ;;
esac

show_dependency_help() {
    "$source_dir/scripts/dependency-hint.sh" >&2
}

check_dependencies() {
    local missing=false command
    for command in python3 glib-compile-schemas gnome-extensions; do
        if ! command -v "$command" >/dev/null; then
            printf 'Missing required command: %s\n' "$command" >&2
            missing=true
        fi
    done
    if "$missing"; then
        show_dependency_help
        return 1
    fi
    if ! python3 - <<'PY'
import gi
for namespace, version in (("Gtk", "4.0"), ("Vte", "3.91")):
    gi.require_version(namespace, version)
PY
    then
        printf 'Missing required Python GTK 4 or VTE 3.91 bindings.\n' >&2
        show_dependency_help
        return 1
    fi
}

managed_paths=()
managed_backups=()
managed_existed=()

remember_managed_file() {
    local target=$1 index backup
    index=${#managed_paths[@]}
    backup="$transaction_dir/managed-backup/$index"
    if [[ -e "$target" && ! -f "$target" && ! -L "$target" ]]; then
        printf 'Refusing to replace unexpected managed path: %s\n' "$target" >&2
        return 1
    fi
    managed_paths+=("$target")
    managed_backups+=("$backup")
    if [[ -e "$target" || -L "$target" ]]; then
        mkdir -p "$(dirname -- "$backup")"
        cp -a -- "$target" "$backup"
        managed_existed+=(1)
    else
        managed_existed+=(0)
    fi
}

install_managed_file() {
    local source=$1 target=$2 mode=$3 temporary
    temporary=$(mktemp "$(dirname -- "$target")/.gnome-ascii-saver-file.XXXXXX")
    if ! install -m "$mode" "$source" "$temporary"; then
        rm -f -- "$temporary"
        return 1
    fi
    mv -fT -- "$temporary" "$target"
}

write_managed_file() {
    local target=$1 mode=$2 temporary
    temporary=$(mktemp "$(dirname -- "$target")/.gnome-ascii-saver-file.XXXXXX")
    if ! cat >"$temporary"; then
        rm -f -- "$temporary"
        return 1
    fi
    chmod "$mode" "$temporary"
    mv -fT -- "$temporary" "$target"
}

restore_managed_files() {
    local index target
    for ((index=${#managed_paths[@]} - 1; index >= 0; index--)); do
        target=${managed_paths[$index]}
        rm -f -- "$target"
        if [[ "${managed_existed[$index]}" == 1 ]]; then
            mkdir -p "$(dirname -- "$target")"
            cp -a -- "${managed_backups[$index]}" "$target"
        fi
    done
}

cleanup() {
    local status=$?
    trap - EXIT INT TERM HUP
    if [[ "$install_complete" != true ]]; then
        if [[ "$app_swapped" == true || "$extension_swapped" == true || \
            "$old_app_moved" == true || "$old_extension_moved" == true || \
            "$legacy_extension_moved" == true ]]; then
            printf 'Installation did not complete; restoring the previous version.\n' >&2
        fi
        if [[ "$app_swapped" == true || "$extension_swapped" == true ]]; then
            restore_managed_files
        fi
        if [[ "$app_swapped" == true ]]; then rm -rf -- "$app_dir"; fi
        if [[ "$extension_swapped" == true ]]; then rm -rf -- "$extension_dir"; fi
        if [[ -d "$backup_app" ]]; then mv -- "$backup_app" "$app_dir"; fi
        if [[ -d "$backup_extension" ]]; then mv -- "$backup_extension" "$extension_dir"; fi
        if [[ -d "$backup_legacy_extension" ]]; then
            mv -- "$backup_legacy_extension" "$legacy_extension_dir"
        fi
        if "$manage_session" && "$session_touched"; then
            if "$has_user_systemd"; then
                systemctl --user daemon-reload >/dev/null 2>&1 || true
                if "$service_was_active"; then
                    systemctl --user start gnome-ascii-saver.service >/dev/null 2>&1 || true
                fi
            fi
            if "$extension_was_active"; then
                gnome-extensions enable "$uuid" >/dev/null 2>&1 || true
            fi
            if "$legacy_extension_was_active"; then
                gnome-extensions enable "$legacy_uuid" >/dev/null 2>&1 || true
            fi
        fi
    fi
    if [[ -n "$transaction_dir" && -d "$transaction_dir" ]]; then
        rm -rf -- "$transaction_dir"
    fi
    exit "$status"
}
trap cleanup EXIT INT TERM HUP

check_dependencies
if "$check_only"; then
    printf 'Required GNOME Shell, GTK/VTE runtime, and schema commands are available.\n'
    exit 0
fi

if "$manage_session" && command -v systemctl >/dev/null && \
    systemctl --user show-environment >/dev/null 2>&1; then
    has_user_systemd=true
elif ! "$manage_session" && command -v systemctl >/dev/null && \
    [[ -n "${XDG_RUNTIME_DIR:-}" && -S "$XDG_RUNTIME_DIR/systemd/private" ]]; then
    has_user_systemd=true
fi

mkdir -p "$data_home" "$config_home"
transaction_dir=$(mktemp -d "$data_home/.gnome-ascii-saver-install.XXXXXX")
chmod 0700 "$transaction_dir"
staged_app="$transaction_dir/app"
staged_extension="$transaction_dir/extension"
backup_app="$transaction_dir/previous-app"
backup_extension="$transaction_dir/previous-extension"
backup_legacy_extension="$transaction_dir/previous-legacy-extension"
mkdir -p "$staged_app" "$staged_extension/schemas"

if ! python3 -m venv --system-site-packages "$staged_app/venv"; then
    printf 'Unable to create a Python virtual environment.\n' >&2
    show_dependency_help
    exit 1
fi
if ! "$staged_app/venv/bin/python" -m pip install --quiet --disable-pip-version-check \
    --require-hashes -r "$source_dir/requirements.txt"; then
    printf 'Unable to install TerminalTextEffects. Check network access and Python packaging support.\n' >&2
    exit 1
fi

install -m 0755 "$source_dir/app.py" "$staged_app/app.py"
install -m 0755 "$source_dir/ctl.py" "$staged_app/ctl.py"
install -m 0755 "$source_dir/watcher.py" "$staged_app/watcher.py"
install -m 0755 "$source_dir/uninstall.sh" "$staged_app/uninstall.sh"
install -m 0644 "$source_dir/helpers.py" "$staged_app/helpers.py"
install -m 0644 "$source_dir/VERSION" "$staged_app/VERSION"

if [[ -f "$staged_app/venv/bin/tte" || -L "$staged_app/venv/bin/tte" ]]; then
    rm -f -- "$staged_app/venv/bin/tte"
    printf '%s\n' '#!/bin/sh' \
        'script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)' \
        'exec "$script_dir/python" -m terminaltexteffects "$@"' \
        >"$staged_app/venv/bin/tte"
    chmod 0755 "$staged_app/venv/bin/tte"
else
    printf 'TerminalTextEffects installed without its tte console script.\n' >&2
    exit 1
fi

for file in metadata.json extension.js prefs.js; do
    install -m 0644 "$source_dir/extension/$file" "$staged_extension/$file"
done
install -m 0644 "$source_dir/extension/schemas/"*.xml "$staged_extension/schemas/"
glib-compile-schemas --strict "$staged_extension/schemas"

mkdir -p "$bin_dir" "$config_home/gnome-ascii-saver" "$applications_dir" \
    "$systemd_dir" "$extension_root"
remember_managed_file "$bin_dir/gnome-ascii-saver"
remember_managed_file "$bin_dir/gnome-ascii-saverctl"
remember_managed_file "$bin_dir/gnome-ascii-saver-watcher"
remember_managed_file "$desktop_file"
remember_managed_file "$legacy_desktop_file"
remember_managed_file "$systemd_dir/gnome-ascii-saver.service"

for target in "$app_dir" "$extension_dir" "$legacy_extension_dir"; do
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ -L "$target" || ! -d "$target" ]]; then
            printf 'Refusing to replace unexpected application path: %s\n' "$target" >&2
            exit 1
        fi
    fi
done

if "$manage_session"; then
    session_touched=true
    if gnome-extensions info "$uuid" 2>/dev/null | grep -q 'State: ACTIVE'; then
        extension_was_active=true
        gnome-extensions disable "$uuid" >/dev/null 2>&1 || true
    fi
    if gnome-extensions info "$legacy_uuid" 2>/dev/null | grep -q 'State: ACTIVE'; then
        legacy_extension_was_active=true
    fi
    # Disable the preview UUID even when Shell reports it as inactive. This
    # removes enabled-but-not-loaded entries and prevents duplicate activation.
    gnome-extensions disable "$legacy_uuid" >/dev/null 2>&1 || true
    if [[ -x "$bin_dir/gnome-ascii-saverctl" ]]; then
        "$bin_dir/gnome-ascii-saverctl" stop >/dev/null 2>&1 || true
    fi
    if "$has_user_systemd"; then
        if systemctl --user is-active --quiet gnome-ascii-saver.service; then
            service_was_active=true
        fi
        systemctl --user stop gnome-ascii-saver.service >/dev/null 2>&1 || true
    fi
fi

if [[ -d "$app_dir" ]]; then mv -- "$app_dir" "$backup_app"; old_app_moved=true; fi
if [[ -d "$extension_dir" ]]; then
    mv -- "$extension_dir" "$backup_extension"
    old_extension_moved=true
fi
if [[ -d "$legacy_extension_dir" ]]; then
    mv -- "$legacy_extension_dir" "$backup_legacy_extension"
    legacy_extension_moved=true
fi
mv -- "$staged_app" "$app_dir"
app_swapped=true
mv -- "$staged_extension" "$extension_dir"
extension_swapped=true

install_managed_file "$source_dir/bin/gnome-ascii-saver" "$bin_dir/gnome-ascii-saver" 0755
install_managed_file "$source_dir/bin/gnome-ascii-saverctl" "$bin_dir/gnome-ascii-saverctl" 0755
install_managed_file "$source_dir/bin/gnome-ascii-saver-watcher" "$bin_dir/gnome-ascii-saver-watcher" 0755

if [[ ! -e "$config_home/gnome-ascii-saver/config.json" && \
    ! -L "$config_home/gnome-ascii-saver/config.json" ]]; then
    install_managed_file "$source_dir/config/config.json" \
        "$config_home/gnome-ascii-saver/config.json" 0644
fi
if [[ ! -e "$config_home/gnome-ascii-saver/logo.txt" && \
    ! -L "$config_home/gnome-ascii-saver/logo.txt" ]]; then
    install_managed_file "$source_dir/config/logo.txt" \
        "$config_home/gnome-ascii-saver/logo.txt" 0644
fi

escaped_exec=$(printf '%s' "$bin_dir/gnome-ascii-saver" | sed 's/[&|]/\\&/g')
sed "s|@EXEC@|$escaped_exec|" "$source_dir/io.github.RobbyBobby77.GnomeAsciiSaver.desktop.in" \
    | write_managed_file "$desktop_file" 0644
rm -f -- "$legacy_desktop_file"
update-desktop-database "$applications_dir" 2>/dev/null || true

install_managed_file "$source_dir/gnome-ascii-saver.service" \
    "$systemd_dir/gnome-ascii-saver.service" 0644
if "$manage_session" && "$has_user_systemd"; then
    systemctl --user daemon-reload
    systemctl --user enable --now gnome-ascii-saver.service
fi

# Also clean stale preview UUID entries when installing with --no-start or when
# gnome-extensions cannot contact the current Shell. A missing settings backend
# is non-fatal because the obsolete extension payload is already gone.
python3 - "$legacy_uuid" <<'PY' || true
import sys
from gi.repository import Gio

legacy_uuid = sys.argv[1]
source = Gio.SettingsSchemaSource.get_default()
schema = source.lookup("org.gnome.shell", True) if source is not None else None
if schema is None:
    raise SystemExit(0)
settings = Gio.Settings.new_full(schema, None, None)
enabled = [item for item in settings.get_strv("enabled-extensions") if item != legacy_uuid]
settings.set_strv("enabled-extensions", enabled)
PY

extension_status=' (Shell extension loads after the next login)'
if "$manage_session"; then
    if gnome-extensions enable "$uuid" 2>/dev/null; then
        extension_status=$(gnome-extensions info "$uuid" 2>/dev/null | sed -n 's/^ *State: */ /p')
    elif python3 - "$uuid" "$legacy_uuid" <<'PY'
import sys
from gi.repository import Gio

uuid, legacy_uuid = sys.argv[1:]
source = Gio.SettingsSchemaSource.get_default()
schema = source.lookup("org.gnome.shell", True) if source is not None else None
if schema is None:
    raise SystemExit(1)
settings = Gio.Settings.new_full(schema, None, None)
enabled = [item for item in settings.get_strv("enabled-extensions") if item != legacy_uuid]
if uuid not in enabled:
    enabled.append(uuid)
settings.set_strv("enabled-extensions", enabled)
PY
    then
        extension_status=' (Shell extension loads after the next login)'
    else
        printf 'Unable to enable the GNOME Shell extension.\n' >&2
        exit 1
    fi
fi

if "$manage_session" && "$has_user_systemd" && \
    gnome-extensions info "$uuid" 2>/dev/null | grep -q 'State: ACTIVE'; then
    systemctl --user stop gnome-ascii-saver.service
fi

install_complete=true
rm -rf -- "$backup_app" "$backup_extension" "$backup_legacy_extension"

printf '\nGNOME ASCII Saver %s installed.%s\n' "$(head -n 1 "$app_dir/VERSION")" "$extension_status"
if "$manage_session"; then
    printf 'The extension owns idle activation when active; the user service is its fallback.\n'
else
    printf 'Session integration was installed but not started (--no-start).\n'
fi
printf 'Start now:  %s/gnome-ascii-saverctl start\n' "$bin_dir"
printf 'Edit art:   %s/gnome-ascii-saverctl edit\n' "$bin_dir"
printf 'Set delay:  %s/gnome-ascii-saverctl delay 180\n' "$bin_dir"
printf 'If those commands are not found, add %s to PATH.\n' "$bin_dir"
