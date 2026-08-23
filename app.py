#!/usr/bin/env python3
"""Fullscreen GTK/VTE renderer for GNOME ASCII Saver."""

from __future__ import annotations

import os
import signal
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Vte", "3.91")
from gi.repository import Gdk, Gio, GLib, Gtk, Pango, Vte  # noqa: E402

from helpers import (  # noqa: E402
    TTE_MAX_FAILURES,
    TTE_SUCCESS_RESTART_MS,
    config_dir,
    load_config,
    pid_file_path,
    read_version,
    tte_exit_ok,
    tte_failure_delay_ms,
    tte_path,
    windows_need_rebuild,
    write_pid_file,
)


APP_ID = "io.github.RobbyBobby77.GnomeAsciiSaver"
VERSION = read_version()


def parse_color(value: str, fallback: str) -> Gdk.RGBA:
    color = Gdk.RGBA()
    if not color.parse(value):
        color.parse(fallback)
    return color


class SaverWindow(Gtk.ApplicationWindow):
    def __init__(self, app: "SaverApplication", monitor: Gdk.Monitor | None, windowed: bool):
        super().__init__(application=app, title="GNOME ASCII Saver")
        self.app = app
        self.monitor = monitor
        self.windowed = windowed
        self.armed = False
        self.running = False
        self.closing = False
        self.tte_failures = 0
        self.cancellable = Gio.Cancellable()
        self.set_decorated(windowed)
        self.set_resizable(True)

        self.terminal = Vte.Terminal()
        self.terminal.set_hexpand(True)
        self.terminal.set_vexpand(True)
        self.terminal.set_font(Pango.FontDescription.from_string(str(app.config["font"])))
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.OFF)
        self.terminal.set_cursor_shape(Vte.CursorShape.BLOCK)
        background = parse_color(str(app.config["background"]), "#000000")
        foreground = parse_color("#f2f2f2", "#ffffff")
        self.terminal.set_colors(foreground, background, [])
        self.terminal.connect("child-exited", self._on_child_exited)
        self.set_child(self.terminal)

        key = Gtk.EventControllerKey()
        key.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key.connect("key-pressed", self._dismiss)
        self.add_controller(key)
        motion = Gtk.EventControllerMotion()
        motion.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        motion.connect("motion", self._dismiss)
        self.add_controller(motion)
        click = Gtk.GestureClick()
        click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        click.connect("pressed", self._dismiss)
        self.add_controller(click)
        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        scroll.connect("scroll", self._dismiss)
        self.add_controller(scroll)

        if windowed:
            self.set_default_size(1000, 700)
        elif monitor is not None:
            self.fullscreen_on_monitor(monitor)
        else:
            self.fullscreen()

        self.connect("close-request", self._on_close)
        self.present()
        if not windowed:
            self._hide_cursor()
        GLib.timeout_add(350, self._start)
        GLib.timeout_add(900, self._arm)

    def _hide_cursor(self) -> None:
        pixels = GLib.Bytes.new(bytes((0, 0, 0, 0)))
        texture = Gdk.MemoryTexture.new(1, 1, Gdk.MemoryFormat.R8G8B8A8, pixels, 4)
        self.set_cursor(Gdk.Cursor.new_from_texture(texture, 0, 0, None))

    def _arm(self) -> bool:
        self.armed = True
        return GLib.SOURCE_REMOVE

    def _dismiss(self, *_args):
        if self.armed:
            self.app.quit_saver()
        return True

    def _on_close(self, *_args):
        self.app.quit_saver()
        return False

    def _tte_argv(self) -> list[str]:
        background = str(self.app.config["background"]).lstrip("#")
        argv = [
            str(tte_path()),
            "-i",
            str(config_dir() / "logo.txt"),
            "--frame-rate",
            str(self.app.config["frame_rate"]),
            "--canvas-width",
            "0",
            "--canvas-height",
            "0",
            "--anchor-canvas",
            "c",
            "--anchor-text",
            "c",
            "--terminal-background-color",
            background,
            "--random-effect",
            "--no-eol",
            "--no-restore-cursor",
        ]
        excluded = self.app.config.get("exclude_effects", [])
        if excluded:
            argv.extend(["--exclude-effects", *excluded])
        return argv

    def _start(self) -> bool:
        if self.app.stopping or self.closing or self.running:
            return GLib.SOURCE_REMOVE
        self.running = True
        self.terminal.spawn_async(
            pty_flags=Vte.PtyFlags.DEFAULT,
            working_directory=str(Path.home()),
            argv=self._tte_argv(),
            envv=None,
            spawn_flags=GLib.SpawnFlags.SEARCH_PATH,
            child_setup=None,
            timeout=-1,
            cancellable=self.cancellable,
            callback=self._on_spawned,
            user_data=self,
        )
        return GLib.SOURCE_REMOVE

    def _on_spawned(self, _terminal, pid, error, _data) -> None:
        if error is not None:
            self.running = False
            if self.app.stopping or self.closing or self.cancellable.is_cancelled():
                return
            print(f"gnome-ascii-saver: could not start animation: {error.message}", file=sys.stderr)
            self.app.quit_saver()
        elif pid == -1:
            self.running = False
            if not self.app.stopping and not self.closing:
                self.app.quit_saver()

    def _on_child_exited(self, _terminal, status) -> None:
        self.running = False
        if self.app.once:
            self.app.quit_saver()
            return
        if self.app.stopping or self.closing:
            return
        if tte_exit_ok(status):
            self.tte_failures = 0
            GLib.timeout_add(TTE_SUCCESS_RESTART_MS, self._start)
            return
        self.tte_failures += 1
        delay = tte_failure_delay_ms(self.tte_failures)
        if delay is None:
            print(
                f"gnome-ascii-saver: animation exited with status {status}; "
                f"giving up after {TTE_MAX_FAILURES} failures",
                file=sys.stderr,
            )
            self.app.quit_saver()
            return
        print(
            f"gnome-ascii-saver: animation exited with status {status}; "
            f"retrying in {delay} ms ({self.tte_failures}/{TTE_MAX_FAILURES})",
            file=sys.stderr,
        )
        GLib.timeout_add(delay, self._start)


class SaverApplication(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )
        self.windowed = False
        self.once = False
        self.config = load_config(config_dir() / "config.json")
        self.stopping = False
        self.pid_file: Path | None = None
        self._monitors = None
        self._monitors_changed_id = 0
        self._screen_lock_bus: Gio.DBusConnection | None = None
        self._screen_lock_subscriptions: list[int] = []
        self._screen_lock_ready = False
        self._screen_lock_query_pending = False
        self.set_option_context_summary("Omarchy-style ASCII screensaver for GNOME")
        self.add_main_option(
            "windowed",
            0,
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "open one decorated preview window",
            None,
        )
        self.add_main_option(
            "once",
            0,
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "exit after one animation (for testing)",
            None,
        )
        self.add_main_option(
            "version",
            0,
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "show program version",
            None,
        )

    def do_handle_local_options(self, options: GLib.VariantDict) -> int:
        if options.contains("version"):
            print(f"GNOME ASCII Saver {VERSION}")
            return 0
        return -1

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        options = command_line.get_options_dict()
        self.windowed = options.contains("windowed")
        self.once = options.contains("once")
        self.activate()
        return 0

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        if not self._watch_screen_lock():
            print(
                "gnome-ascii-saver: could not monitor the GNOME lock screen; refusing to start",
                file=sys.stderr,
            )
            self.stopping = True
            self.quit()
            return
        css = Gtk.CssProvider()
        css.load_from_data(b"window, vte-terminal { background: #000; padding: 0; margin: 0; }")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.set_accels_for_action("app.quit", ["Escape"])

    def _existing_windowed(self) -> bool | None:
        windows = list(self.get_windows())
        if not windows:
            return None
        return all(window.windowed for window in windows)

    def _close_window(self, window: SaverWindow) -> None:
        if window.closing:
            return
        window.closing = True
        window.cancellable.cancel()
        try:
            window.terminal.feed_child(bytes((3,)))
        except GLib.Error:
            pass
        window.destroy()

    def _destroy_windows(self) -> None:
        for window in list(self.get_windows()):
            self._close_window(window)

    def _create_windows(self) -> None:
        if self.windowed:
            SaverWindow(self, None, True)
            return
        self._sync_monitor_windows()

    def _listen_for_monitors(self, enabled: bool) -> None:
        if enabled:
            display = Gdk.Display.get_default()
            if display is None or self._monitors_changed_id:
                return
            self._monitors = display.get_monitors()
            self._monitors_changed_id = self._monitors.connect(
                "items-changed", self._on_monitors_changed
            )
            return
        if self._monitors is not None and self._monitors_changed_id:
            self._monitors.disconnect(self._monitors_changed_id)
        self._monitors = None
        self._monitors_changed_id = 0

    def _on_monitors_changed(self, _model, _position, _removed, _added) -> None:
        self._sync_monitor_windows()

    def _sync_monitor_windows(self) -> None:
        """Keep exactly one fullscreen window on each current monitor."""
        if self.stopping or self.windowed:
            return
        monitors = self._monitors
        desired = (
            [monitors.get_item(index) for index in range(monitors.get_n_items())]
            if monitors is not None
            else []
        )
        fullscreen = [window for window in self.get_windows() if not window.windowed]
        if not desired:
            for window in fullscreen:
                if window.monitor is not None:
                    self._close_window(window)
            if not any(
                not window.windowed and window.monitor is None for window in self.get_windows()
            ):
                SaverWindow(self, None, False)
            return

        for window in fullscreen:
            if window.monitor is None or not any(window.monitor is monitor for monitor in desired):
                self._close_window(window)
        for monitor in desired:
            if not any(
                not window.windowed and window.monitor is monitor for window in self.get_windows()
            ):
                SaverWindow(self, monitor, False)

    def _watch_screen_lock(self) -> bool:
        """Subscribe before creating windows, then query current lock state."""
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            return False
        if bus is None:
            return False
        self._screen_lock_bus = bus
        self._screen_lock_subscriptions = [
            bus.signal_subscribe(
                "org.gnome.ScreenSaver",
                "org.gnome.ScreenSaver",
                "ActiveChanged",
                "/org/gnome/ScreenSaver",
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_active_changed,
                None,
            ),
            bus.signal_subscribe(
                "org.freedesktop.DBus",
                "org.freedesktop.DBus",
                "NameOwnerChanged",
                "/org/freedesktop/DBus",
                "org.gnome.ScreenSaver",
                Gio.DBusSignalFlags.NONE,
                self._on_screen_saver_owner_changed,
                None,
            ),
        ]
        self.hold()
        self._screen_lock_query_pending = True
        try:
            bus.call(
                "org.gnome.ScreenSaver",
                "/org/gnome/ScreenSaver",
                "org.gnome.ScreenSaver",
                "GetActive",
                None,
                GLib.VariantType.new("(b)"),
                Gio.DBusCallFlags.NONE,
                1000,
                None,
                self._on_get_active_finished,
                None,
            )
        except (GLib.Error, TypeError):
            self._finish_screen_lock_query()
            return False
        return True

    def _finish_screen_lock_query(self) -> None:
        if self._screen_lock_query_pending:
            self._screen_lock_query_pending = False
            self.release()

    def _on_active_changed(
        self,
        _connection,
        _sender_name,
        _object_path,
        _interface_name,
        _signal_name,
        parameters,
        _user_data,
    ) -> None:
        try:
            active = bool(parameters.unpack()[0])
        except (AttributeError, IndexError, TypeError):
            print("gnome-ascii-saver: malformed lock-screen signal; exiting", file=sys.stderr)
            self.quit_saver()
            return
        if active:
            self.quit_saver()

    def _on_screen_saver_owner_changed(
        self,
        _connection,
        _sender_name,
        _object_path,
        _interface_name,
        _signal_name,
        parameters,
        _user_data,
    ) -> None:
        try:
            name, _old_owner, new_owner = parameters.unpack()
        except (AttributeError, TypeError, ValueError):
            self.quit_saver()
            return
        if name == "org.gnome.ScreenSaver" and not new_owner:
            print("gnome-ascii-saver: lock-screen service disappeared; exiting", file=sys.stderr)
            self.quit_saver()

    def _on_get_active_finished(self, connection, result, _user_data) -> None:
        try:
            active = bool(connection.call_finish(result).unpack()[0])
        except (GLib.Error, AttributeError, IndexError, TypeError) as error:
            if not self.stopping:
                print(
                    f"gnome-ascii-saver: could not query the GNOME lock screen: {error}",
                    file=sys.stderr,
                )
                self.stopping = True
                self._finish_screen_lock_query()
                self.quit()
            return
        if self.stopping:
            self._finish_screen_lock_query()
            return
        if active:
            self._finish_screen_lock_query()
            self.quit_saver()
            return
        self._screen_lock_ready = True
        self.activate()
        self._finish_screen_lock_query()

    def do_activate(self) -> None:
        # Never create an overlay until the initial GetActive reply proves the
        # session is unlocked.
        if self.stopping or not self._screen_lock_ready:
            return
        existing = self._existing_windowed()
        if existing is not None:
            if not windows_need_rebuild(existing, self.windowed):
                for window in self.get_windows():
                    window.present()
                return
            self._destroy_windows()

        if self.pid_file is None:
            try:
                self.pid_file = write_pid_file(pid_file_path(), os.getpid())
            except (OSError, RuntimeError) as error:
                print(f"gnome-ascii-saver: {error}", file=sys.stderr)
                self.quit()
                return

        self._listen_for_monitors(not self.windowed)
        self._create_windows()

    def quit_saver(self) -> None:
        if self.stopping:
            return
        self.stopping = True
        self._listen_for_monitors(False)
        self._destroy_windows()
        self.quit()

    def do_shutdown(self) -> None:
        self._listen_for_monitors(False)
        bus = self._screen_lock_bus
        if bus is not None:
            for subscription in self._screen_lock_subscriptions:
                bus.signal_unsubscribe(subscription)
        self._screen_lock_subscriptions = []
        self._screen_lock_bus = None
        self._finish_screen_lock_query()
        pid_file = self.pid_file
        if pid_file is not None:
            try:
                if pid_file.read_text(encoding="ascii").strip() == str(os.getpid()):
                    pid_file.unlink(missing_ok=True)
            except OSError:
                pass
        Gtk.Application.do_shutdown(self)


def main() -> int:
    app = SaverApplication()
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, lambda *_unused: GLib.idle_add(app.quit_saver))
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
