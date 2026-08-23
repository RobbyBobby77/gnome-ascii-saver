#!/usr/bin/env python3
"""Lifecycle tests for lock handoff and GTK4 monitor reconciliation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


class Variant:
    def __init__(self, value):
        self.value = value

    def unpack(self):
        return self.value


class LockHandoffTests(unittest.TestCase):
    def test_active_changed_true_quits_renderer(self) -> None:
        target = SimpleNamespace(quit_saver=Mock())
        app.SaverApplication._on_active_changed(
            target, None, None, None, None, None, Variant((True,)), None
        )
        target.quit_saver.assert_called_once_with()

    def test_active_changed_false_keeps_renderer(self) -> None:
        target = SimpleNamespace(quit_saver=Mock())
        app.SaverApplication._on_active_changed(
            target, None, None, None, None, None, Variant((False,)), None
        )
        target.quit_saver.assert_not_called()

    def test_screen_saver_owner_loss_quits_renderer(self) -> None:
        target = SimpleNamespace(quit_saver=Mock())
        app.SaverApplication._on_screen_saver_owner_changed(
            target,
            None,
            None,
            None,
            None,
            None,
            Variant(("org.gnome.ScreenSaver", ":1.2", "")),
            None,
        )
        target.quit_saver.assert_called_once_with()

    def test_initial_locked_reply_never_activates(self) -> None:
        connection = Mock()
        connection.call_finish.return_value = Variant((True,))
        target = SimpleNamespace(
            stopping=False,
            activate=Mock(),
            quit_saver=Mock(),
            _finish_screen_lock_query=Mock(),
            _screen_lock_ready=False,
        )
        app.SaverApplication._on_get_active_finished(target, connection, object(), None)
        self.assertFalse(target._screen_lock_ready)
        target.activate.assert_not_called()
        target.quit_saver.assert_called_once_with()

    def test_initial_unlocked_reply_enables_activation(self) -> None:
        connection = Mock()
        connection.call_finish.return_value = Variant((False,))
        target = SimpleNamespace(
            stopping=False,
            activate=Mock(),
            quit_saver=Mock(),
            _finish_screen_lock_query=Mock(),
            _screen_lock_ready=False,
        )
        app.SaverApplication._on_get_active_finished(target, connection, object(), None)
        self.assertTrue(target._screen_lock_ready)
        target.activate.assert_called_once_with()
        target.quit_saver.assert_not_called()


class MonitorLifecycleTests(unittest.TestCase):
    def test_monitor_sync_replaces_fallback_with_one_window_per_monitor(self) -> None:
        first, second = object(), object()
        fallback = SimpleNamespace(windowed=False, monitor=None)
        windows = [fallback]
        model = Mock()
        model.get_n_items.return_value = 2
        model.get_item.side_effect = [first, second]
        target = SimpleNamespace(
            stopping=False,
            windowed=False,
            _monitors=model,
            get_windows=lambda: list(windows),
            _close_window=lambda window: windows.remove(window),
        )

        def create_window(_app, monitor, windowed):
            windows.append(SimpleNamespace(windowed=windowed, monitor=monitor))

        with patch("app.SaverWindow", side_effect=create_window):
            app.SaverApplication._sync_monitor_windows(target)

        self.assertEqual([window.monitor for window in windows], [first, second])

    def test_zero_monitor_transition_keeps_fallback_window_alive(self) -> None:
        old_monitor = object()
        windows = [SimpleNamespace(windowed=False, monitor=old_monitor)]
        model = Mock()
        model.get_n_items.return_value = 0
        target = SimpleNamespace(
            stopping=False,
            windowed=False,
            _monitors=model,
            get_windows=lambda: list(windows),
            _close_window=lambda window: windows.remove(window),
        )

        def create_window(_app, monitor, windowed):
            windows.append(SimpleNamespace(windowed=windowed, monitor=monitor))

        with patch("app.SaverWindow", side_effect=create_window):
            app.SaverApplication._sync_monitor_windows(target)

        self.assertEqual(len(windows), 1)
        self.assertIsNone(windows[0].monitor)


if __name__ == "__main__":
    unittest.main()
