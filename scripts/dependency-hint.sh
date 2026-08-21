#!/bin/sh
set -eu

distro_id=unknown
distro_like=
if [ -r /etc/os-release ]; then
    # OS-provided values; used only to select a printed package hint.
    . /etc/os-release
    distro_id=${ID:-unknown}
    distro_like=${ID_LIKE:-}
fi

case " $distro_id $distro_like " in
    *" fedora "*|*" rhel "*)
        cat <<'EOF'
Install dependencies with:
  sudo dnf install python3 python3-gobject gtk4 vte291-gtk4 gnome-shell glib2 desktop-file-utils
EOF
        ;;
    *" debian "*|*" ubuntu "*)
        cat <<'EOF'
Install dependencies with:
  sudo apt update
  sudo apt install python3 python3-gi python3-venv gir1.2-gtk-4.0 gir1.2-vte-3.91 gnome-shell libglib2.0-bin desktop-file-utils
EOF
        ;;
    *" arch "*)
        cat <<'EOF'
Install dependencies with:
  sudo pacman -S --needed python python-gobject gtk4 vte4 gnome-shell glib2 desktop-file-utils
EOF
        ;;
    *" opensuse "*|*" suse "*)
        cat <<'EOF'
Install dependencies with:
  sudo zypper install python3 python3-gobject typelib-1_0-Gtk-4_0 typelib-1_0-Vte-3_91 gnome-shell glib2-tools desktop-file-utils
EOF
        ;;
    *)
        cat <<'EOF'
Install your distribution's packages for Python 3 (including venv/pip),
PyGObject, GTK 4, GTK4 VTE (Vte 3.91), GNOME Shell, GLib schema tools, and
desktop-file-utils. Then rerun ./install.sh.
EOF
        ;;
esac
