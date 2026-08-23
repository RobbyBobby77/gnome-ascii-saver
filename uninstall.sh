#!/usr/bin/env bash
set -euo pipefail

data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
app_dir="$data_home/gnome-ascii-saver"
uuid=gnome-ascii-saver@robbybobby77.github.io
legacy_uuid=gnome-ascii-saver@local
extension_root="$data_home/gnome-shell/extensions"
bin_dir="$HOME/.local/bin"
manage_session=true
remove_complete=true

usage() {
    cat <<'EOF'
Usage: ./uninstall.sh [OPTIONS]

Remove GNOME ASCII Saver for the current user. Configuration and custom ASCII
art in $XDG_CONFIG_HOME/gnome-ascii-saver are always preserved.

Options:
  --no-stop           Do not contact GNOME Shell, user services, or processes
  --non-interactive   Accepted for unattended removal (the script never prompts)
  -h, --help          Show this help

Set GNOME_ASCII_SAVER_NO_SESSION=1 for the same behavior as --no-stop.
EOF
}

while (($#)); do
    case "$1" in
        --no-stop) manage_session=false ;;
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

has_user_systemd=false
if "$manage_session" && command -v systemctl >/dev/null && \
    systemctl --user show-environment >/dev/null 2>&1; then
    has_user_systemd=true
fi
if "$manage_session"; then
    gnome-extensions disable "$uuid" >/dev/null 2>&1 || true
    gnome-extensions disable "$legacy_uuid" >/dev/null 2>&1 || true
    "$bin_dir/gnome-ascii-saverctl" stop >/dev/null 2>&1 || true
    if "$has_user_systemd"; then
        systemctl --user disable --now gnome-ascii-saver.service >/dev/null 2>&1 || true
    fi
fi

for target in "$app_dir" "$extension_root/$uuid" "$extension_root/$legacy_uuid"; do
    if [[ -d "$target" && ! -L "$target" ]]; then
        rm -rf -- "$target"
    elif [[ -e "$target" || -L "$target" ]]; then
        printf 'Not removing unexpected application path: %s\n' "$target" >&2
        remove_complete=false
    fi
done
rm -f -- "$data_home/applications/io.github.RobbyBobby77.GnomeAsciiSaver.desktop" \
    "$data_home/applications/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop" \
    "$bin_dir/gnome-ascii-saver" "$bin_dir/gnome-ascii-saverctl" \
    "$bin_dir/gnome-ascii-saver-watcher" \
    "$config_home/systemd/user/gnome-ascii-saver.service"
update-desktop-database "$data_home/applications" 2>/dev/null || true
if "$manage_session" && "$has_user_systemd"; then systemctl --user daemon-reload; fi

if "$manage_session"; then
    python3 - "$uuid" "$legacy_uuid" <<'PY' || true
import sys
from gi.repository import Gio

removed = set(sys.argv[1:])
source = Gio.SettingsSchemaSource.get_default()
schema = source.lookup("org.gnome.shell", True) if source is not None else None
if schema is None:
    raise SystemExit(0)
settings = Gio.Settings.new_full(schema, None, None)
settings.set_strv(
    "enabled-extensions",
    [item for item in settings.get_strv("enabled-extensions") if item not in removed],
)
PY
fi

printf 'GNOME ASCII Saver removed. Your settings and art are preserved in %s/gnome-ascii-saver\n' "$config_home"
if ! "$remove_complete"; then
    printf 'Some application files remain; remove them only after inspecting the paths above.\n' >&2
    exit 1
fi
