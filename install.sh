#!/bin/bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
app_dir="$data_home/gnome-ascii-saver"
extension_dir="$data_home/gnome-shell/extensions/gnome-ascii-saver@local"
bin_dir="$HOME/.local/bin"
systemd_dir="$config_home/systemd/user"

for command in python3 glib-compile-schemas gnome-extensions; do
    if ! command -v "$command" >/dev/null; then
        printf 'Missing required command: %s\n' "$command" >&2
        exit 1
    fi
done

python3 - <<'PY'
import gi
for namespace, version in (("Gtk", "4.0"), ("Vte", "3.91")):
    gi.require_version(namespace, version)
PY

mkdir -p "$app_dir" "$extension_dir/schemas" "$bin_dir" \
    "$config_home/gnome-ascii-saver" "$data_home/applications" "$systemd_dir"

if [[ ! -x "$app_dir/venv/bin/python" ]]; then
    python3 -m venv --system-site-packages "$app_dir/venv"
fi
"$app_dir/venv/bin/python" -m pip install --quiet --disable-pip-version-check -r "$source_dir/requirements.txt"

install -m 0755 "$source_dir/app.py" "$app_dir/app.py"
install -m 0755 "$source_dir/ctl.py" "$app_dir/ctl.py"
install -m 0755 "$source_dir/watcher.py" "$app_dir/watcher.py"
install -m 0755 "$source_dir/bin/gnome-ascii-saver" "$bin_dir/gnome-ascii-saver"
install -m 0755 "$source_dir/bin/gnome-ascii-saverctl" "$bin_dir/gnome-ascii-saverctl"
install -m 0755 "$source_dir/bin/gnome-ascii-saver-watcher" "$bin_dir/gnome-ascii-saver-watcher"

# GNOME Shell monitors extension files. Updating an active extension in place
# can make Shell unload it after the installer has already checked its state.
# Disable it cleanly before replacing the files, then enable it again below.
if gnome-extensions info gnome-ascii-saver@local 2>/dev/null | grep -q 'State: ACTIVE'; then
    gnome-extensions disable gnome-ascii-saver@local
fi

for file in metadata.json extension.js prefs.js; do
    install -m 0644 "$source_dir/extension/$file" "$extension_dir/$file"
done
install -m 0644 "$source_dir/extension/schemas/"*.xml "$extension_dir/schemas/"
glib-compile-schemas "$extension_dir/schemas"

[[ -f "$config_home/gnome-ascii-saver/config.json" ]] || \
    install -m 0644 "$source_dir/config/config.json" "$config_home/gnome-ascii-saver/config.json"
[[ -f "$config_home/gnome-ascii-saver/logo.txt" ]] || \
    install -m 0644 "$source_dir/config/logo.txt" "$config_home/gnome-ascii-saver/logo.txt"

escaped_exec=$(printf '%s' "$bin_dir/gnome-ascii-saver" | sed 's/[&|]/\\&/g')
sed "s|@EXEC@|$escaped_exec|" "$source_dir/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop.in" \
    >"$data_home/applications/io.github.gnome_ascii_saver.GnomeAsciiSaver.desktop"
update-desktop-database "$data_home/applications" 2>/dev/null || true

install -m 0644 "$source_dir/gnome-ascii-saver.service" "$systemd_dir/gnome-ascii-saver.service"
systemctl --user daemon-reload
systemctl --user enable --now gnome-ascii-saver.service

if gnome-extensions enable gnome-ascii-saver@local 2>/dev/null; then
    extension_status=$(gnome-extensions info gnome-ascii-saver@local 2>/dev/null | sed -n 's/^ *State: */ /p')
else
    python3 - <<'PY'
from gi.repository import Gio
settings = Gio.Settings.new("org.gnome.shell")
enabled = list(settings.get_strv("enabled-extensions"))
uuid = "gnome-ascii-saver@local"
if uuid not in enabled:
    enabled.append(uuid)
    settings.set_strv("enabled-extensions", enabled)
PY
    extension_status=" (idle service active now; Shell extension loads after the next login)"
fi

if gnome-extensions info gnome-ascii-saver@local 2>/dev/null | grep -q 'State: ACTIVE'; then
    systemctl --user stop gnome-ascii-saver.service
fi

printf '\nGNOME ASCII Saver installed.%s\n' "$extension_status"
printf 'Start now:  %s/gnome-ascii-saverctl start\n' "$bin_dir"
printf 'Edit art:   %s/gnome-ascii-saverctl edit\n' "$bin_dir"
printf 'Set delay:  %s/gnome-ascii-saverctl delay 180\n' "$bin_dir"
