#!/bin/bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}

# Prefer the installed controller so both uninstall paths stay identical.
ctl="$HOME/.local/bin/gnome-ascii-saverctl"
if [[ -x "$ctl" ]]; then
    exec "$ctl" uninstall
fi

# Next, the checkout copy of ctl.py so this script does not drift from
# command_uninstall when the launcher is already gone.
if [[ -f "$source_dir/ctl.py" ]]; then
    exec python3 "$source_dir/ctl.py" uninstall
fi

# Last-resort copy of ctl.command_uninstall. Keep the steps below aligned
# with that function; do not add behavior the controller does not have.

gnome-extensions disable gnome-ascii-saver@local 2>/dev/null || true
if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user disable --now gnome-ascii-saver.service >/dev/null 2>&1 || true
fi
if [[ -n "${XDG_RUNTIME_DIR:-}" ]]; then
    pid_file="$XDG_RUNTIME_DIR/gnome-ascii-saver-$(id -u).pid"
    if [[ -r "$pid_file" ]]; then
        read -r pid <"$pid_file" || pid=
        if [[ "$pid" =~ ^[0-9]+$ ]] && [[ -r "/proc/$pid/cmdline" ]] && \
            grep -aqE 'gnome-ascii-saver|app.py' "/proc/$pid/cmdline"; then
            kill "$pid" 2>/dev/null || true
        fi
        rm -f -- "$pid_file"
    fi
fi

rm -r -- "$data_home/gnome-ascii-saver" 2>/dev/null || true
rm -r -- "$data_home/gnome-shell/extensions/gnome-ascii-saver@local" 2>/dev/null || true
rm -f -- "$data_home/applications/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop" \
    "$HOME/.local/bin/gnome-ascii-saver" "$HOME/.local/bin/gnome-ascii-saverctl" \
    "$HOME/.local/bin/gnome-ascii-saver-watcher" \
    "$config_home/systemd/user/gnome-ascii-saver.service"
if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user daemon-reload
fi

python3 - <<'PY' || true
from gi.repository import Gio
settings = Gio.Settings.new("org.gnome.shell")
uuid = "gnome-ascii-saver@local"
settings.set_strv("enabled-extensions", [item for item in settings.get_strv("enabled-extensions") if item != uuid])
PY

printf 'GNOME ASCII Saver removed. Your art is preserved in %s/gnome-ascii-saver\n' "$config_home"
