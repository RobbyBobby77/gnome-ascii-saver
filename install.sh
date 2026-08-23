#!/bin/bash
set -euo pipefail

source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
app_dir="$data_home/gnome-ascii-saver"
extension_dir="$data_home/gnome-shell/extensions/gnome-ascii-saver@local"
bin_dir="$HOME/.local/bin"
systemd_dir="$config_home/systemd/user"
has_user_systemd=false

show_dependency_help() {
    "$source_dir/scripts/dependency-hint.sh" >&2
}

for command in python3 glib-compile-schemas gnome-extensions; do
    if ! command -v "$command" >/dev/null; then
        printf 'Missing required command: %s\n' "$command" >&2
        show_dependency_help
        exit 1
    fi
done

if ! python3 - <<'PY'
import gi
for namespace, version in (("Gtk", "4.0"), ("Vte", "3.91")):
    gi.require_version(namespace, version)
PY
then
    printf 'Missing required Python GTK 4 or VTE 3.91 bindings.\n' >&2
    show_dependency_help
    exit 1
fi

if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
    has_user_systemd=true
fi

mkdir -p "$app_dir" "$extension_dir/schemas" "$bin_dir" \
    "$config_home/gnome-ascii-saver" "$data_home/applications"
if "$has_user_systemd"; then
    mkdir -p "$systemd_dir"
fi

if [[ ! -x "$app_dir/venv/bin/python" ]]; then
    if ! python3 -m venv --system-site-packages "$app_dir/venv"; then
        printf 'Unable to create a Python virtual environment.\n' >&2
        show_dependency_help
        exit 1
    fi
fi
if ! "$app_dir/venv/bin/python" -m pip install --quiet --disable-pip-version-check \
    -r "$source_dir/requirements.txt"; then
    printf 'Unable to install TerminalTextEffects. Check network access and Python packaging support.\n' >&2
    exit 1
fi

install -m 0755 "$source_dir/app.py" "$app_dir/app.py"
install -m 0755 "$source_dir/ctl.py" "$app_dir/ctl.py"
install -m 0755 "$source_dir/watcher.py" "$app_dir/watcher.py"
install -m 0644 "$source_dir/helpers.py" "$app_dir/helpers.py"
install -m 0644 "$source_dir/VERSION" "$app_dir/VERSION"
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

if "$has_user_systemd"; then
    install -m 0644 "$source_dir/gnome-ascii-saver.service" "$systemd_dir/gnome-ascii-saver.service"
    systemctl --user daemon-reload
    systemctl --user enable --now gnome-ascii-saver.service
else
    rm -f -- "$systemd_dir/gnome-ascii-saver.service"
fi

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
    if "$has_user_systemd"; then
        extension_status=" (idle service active now; Shell extension loads after the next login)"
    else
        extension_status=" (Shell extension loads after the next login)"
    fi
fi

if "$has_user_systemd" && \
    gnome-extensions info gnome-ascii-saver@local 2>/dev/null | grep -q 'State: ACTIVE'; then
    systemctl --user stop gnome-ascii-saver.service
fi

printf '\nGNOME ASCII Saver installed.%s\n' "$extension_status"
if ! "$has_user_systemd"; then
    printf 'No systemd user manager was found; the Shell extension will own idle activation.\n'
    printf 'Log out and back in if the extension is not active yet.\n'
fi
printf 'Start now:  %s/gnome-ascii-saverctl start\n' "$bin_dir"
printf 'Edit art:   %s/gnome-ascii-saverctl edit\n' "$bin_dir"
printf 'Set delay:  %s/gnome-ascii-saverctl delay 180\n' "$bin_dir"
printf 'If those commands are not found, add %s to PATH.\n' "$bin_dir"
