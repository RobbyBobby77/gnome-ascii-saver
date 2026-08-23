#!/usr/bin/env python3
"""Tests for fallback/extension mutual exclusion and lock behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import watcher  # noqa: E402


class Result:
    def __init__(self, value):
        self.value = value

    def unpack(self):
        return self.value


class ExtensionOwnershipTests(unittest.TestCase):
    def _target(self, info):
        target = watcher.IdleWatcher.__new__(watcher.IdleWatcher)
        target.extensions_proxy = Mock()
        target.extensions_proxy.call_sync.return_value = Result((info,))
        target._extension_unknown_logged = False
        return target

    def test_enabled_extension_owns_idle_activation(self) -> None:
        self.assertTrue(self._target({"state": 1})._extension_active())

    def test_real_glib_variant_response_is_supported(self) -> None:
        target = watcher.IdleWatcher.__new__(watcher.IdleWatcher)
        target.extensions_proxy = Mock()
        target.extensions_proxy.call_sync.return_value = watcher.GLib.Variant(
            "(a{sv})", ({"state": watcher.GLib.Variant("d", 1.0)},)
        )
        target._extension_unknown_logged = False
        self.assertTrue(target._extension_active())

    def test_disabled_extension_leaves_activation_to_fallback(self) -> None:
        self.assertFalse(self._target({"state": 2})._extension_active())

    def test_extension_transition_states_block_fallback(self) -> None:
        self.assertTrue(self._target({"state": 7})._extension_active())
        self.assertTrue(self._target({"state": 8})._extension_active())

    def test_unknown_extension_response_fails_closed(self) -> None:
        self.assertTrue(self._target({})._extension_active())

    def test_poll_stops_renderer_when_extension_becomes_active(self) -> None:
        target = watcher.IdleWatcher.__new__(watcher.IdleWatcher)
        target.process = Mock()
        target.process.poll.return_value = None
        target.settings = Mock()
        target.settings.get_boolean.return_value = True
        target._extension_active = Mock(return_value=True)
        target._stop = Mock()
        target._idle_msec = Mock()
        target._screen_locked = Mock()

        result = target.poll()

        self.assertEqual(result, watcher.GLib.SOURCE_CONTINUE)
        target._stop.assert_called_once_with()
        target._idle_msec.assert_not_called()

    def test_locked_session_never_starts_renderer(self) -> None:
        target = watcher.IdleWatcher.__new__(watcher.IdleWatcher)
        target.process = None
        target.ready = True
        target.settings = Mock()
        target.settings.get_boolean.return_value = True
        target.settings.get_uint.return_value = 10
        target._extension_active = Mock(return_value=False)
        target._idle_msec = Mock(return_value=10000)
        target._screen_locked = Mock(return_value=True)
        target._start = Mock()

        target.poll()

        target._start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
