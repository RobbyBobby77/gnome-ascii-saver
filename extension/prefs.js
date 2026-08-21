import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Gtk from 'gi://Gtk';

import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

export default class GnomeAsciiSaverPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        const page = new Adw.PreferencesPage({
            title: 'GNOME ASCII Saver',
            icon_name: 'preferences-desktop-wallpaper-symbolic',
        });
        const group = new Adw.PreferencesGroup({
            title: 'Idle screensaver',
            description: 'GNOME’s regular lock screen remains unchanged.',
        });

        const enabled = new Adw.SwitchRow({
            title: 'Launch automatically',
            subtitle: 'Show animated ASCII art when the desktop is idle',
        });
        settings.bind('enabled', enabled, 'active', Gio.SettingsBindFlags.DEFAULT);
        group.add(enabled);

        const adjustment = new Gtk.Adjustment({
            lower: 10,
            upper: 86400,
            step_increment: 10,
            page_increment: 60,
        });
        const delay = new Adw.SpinRow({
            title: 'Idle delay',
            subtitle: 'Seconds before the animation starts',
            adjustment,
            numeric: true,
        });
        settings.bind('idle-delay', delay, 'value', Gio.SettingsBindFlags.DEFAULT);
        group.add(delay);

        const edit = new Adw.ActionRow({
            title: 'ASCII artwork',
            subtitle: '~/.config/gnome-ascii-saver/logo.txt',
        });
        const button = new Gtk.Button({label: 'Edit', valign: Gtk.Align.CENTER});
        button.connect('clicked', () => {
            const file = Gio.File.new_for_path(`${GLib.get_user_config_dir()}/gnome-ascii-saver/logo.txt`);
            Gio.AppInfo.launch_default_for_uri(file.get_uri(), null);
        });
        edit.add_suffix(button);
        group.add(edit);

        page.add(group);
        window.add(page);
    }
}
