#!/bin/bash
set -euo pipefail

data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}

gnome-extensions disable gnome-ascii-saver@local 2>/dev/null || true
"$HOME/.local/bin/gnome-ascii-saverctl" stop >/dev/null 2>&1 || true
if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user disable --now gnome-ascii-saver.service >/dev/null 2>&1 || true
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
