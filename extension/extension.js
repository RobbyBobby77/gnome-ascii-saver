import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Meta from 'gi://Meta';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const SIGTERM = 15;
const KILL_TIMEOUT_SECONDS = 3;
const FALLBACK_RETRY_SECONDS = 5;

export default class GnomeAsciiSaverExtension extends Extension {
    enable() {
        this._disabled = false;
        this._process = null;
        this._idleWatchId = 0;
        this._activeWatchId = 0;
        this._retrySourceId = 0;
        this._fallbackRetrySourceId = 0;
        this._killSources = new Map();
        this._ownsIdleActivation = false;
        this._idleMonitor = global.backend?.get_core_idle_monitor?.() ?? Meta.IdleMonitor.get_core();
        this._settings = this.getSettings();
        this._settingsChangedId = this._settings.connect('changed', () => this._reconfigure());
        // Wait for stop so the fallback cannot launch alongside the extension.
        this._claimFallbackOwnership();
    }

    _claimFallbackOwnership() {
        this._manageFallback('stop', successful => {
            if (this._disabled)
                return;
            this._ownsIdleActivation = successful;
            if (successful) {
                this._reconfigure();
                return;
            }
            if (!this._fallbackRetrySourceId) {
                this._fallbackRetrySourceId = GLib.timeout_add_seconds(
                    GLib.PRIORITY_DEFAULT,
                    FALLBACK_RETRY_SECONDS,
                    () => {
                        this._fallbackRetrySourceId = 0;
                        this._claimFallbackOwnership();
                        return GLib.SOURCE_REMOVE;
                    }
                );
            }
        });
    }

    disable() {
        this._disabled = true;
        if (this._settingsChangedId)
            this._settings.disconnect(this._settingsChangedId);
        this._settingsChangedId = 0;
        this._removeWatches();
        this._stopSaver(false);
        if (this._fallbackRetrySourceId) {
            GLib.source_remove(this._fallbackRetrySourceId);
            this._fallbackRetrySourceId = 0;
        }
        this._ownsIdleActivation = false;
        this._settings = null;
        this._idleMonitor = null;
        // Lock-screen teardown and user disable must not start the fallback.
    }

    _manageFallback(action, onDone) {
        const done = successful => {
            if (onDone)
                onDone(successful);
        };
        const unit = GLib.build_filenamev([
            GLib.get_user_config_dir(),
            'systemd',
            'user',
            'gnome-ascii-saver.service',
        ]);
        if (!GLib.find_program_in_path('systemctl') || !GLib.file_test(unit, GLib.FileTest.EXISTS)) {
            done(true);
            return;
        }
        try {
            const process = Gio.Subprocess.new(
                ['systemctl', '--user', action, 'gnome-ascii-saver.service'],
                Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE
            );
            process.wait_async(null, (_source, result) => {
                try {
                    process.wait_finish(result);
                    if (!process.get_successful()) {
                        const status = process.get_if_exited() ? process.get_exit_status() : 'unknown';
                        console.error(`Unable to ${action} GNOME ASCII Saver fallback (status ${status})`);
                        done(false);
                        return;
                    }
                } catch (error) {
                    console.error(`Unable to ${action} GNOME ASCII Saver fallback: ${error.message}`);
                    done(false);
                    return;
                }
                done(true);
            });
        } catch (error) {
            console.error(`Unable to ${action} GNOME ASCII Saver fallback: ${error.message}`);
            done(false);
        }
    }

    _removeWatches() {
        if (this._idleWatchId) {
            this._idleMonitor.remove_watch(this._idleWatchId);
            this._idleWatchId = 0;
        }
        if (this._activeWatchId) {
            this._idleMonitor.remove_watch(this._activeWatchId);
            this._activeWatchId = 0;
        }
        if (this._retrySourceId) {
            GLib.source_remove(this._retrySourceId);
            this._retrySourceId = 0;
        }
    }

    _reconfigure() {
        this._removeWatches();
        this._stopSaver(false);
        if (!this._disabled && this._ownsIdleActivation && this._settings.get_boolean('enabled'))
            this._armIdleWatch();
    }

    _armIdleWatch() {
        if (this._disabled || !this._ownsIdleActivation || this._idleWatchId ||
            !this._settings.get_boolean('enabled'))
            return;
        const delayMs = Math.max(10, this._settings.get_uint('idle-delay')) * 1000;
        this._idleWatchId = this._idleMonitor.add_idle_watch(delayMs, () => {
            this._idleWatchId = 0;
            this._startSaver();
        });
    }

    _startSaver() {
        if (this._disabled || !this._ownsIdleActivation || this._process ||
            !this._settings.get_boolean('enabled'))
            return;

        const dataDir = GLib.build_filenamev([GLib.get_user_data_dir(), 'gnome-ascii-saver']);
        const argv = [
            GLib.build_filenamev([dataDir, 'venv', 'bin', 'python']),
            GLib.build_filenamev([dataDir, 'app.py']),
        ];
        try {
            const process = Gio.Subprocess.new(argv, Gio.SubprocessFlags.NONE);
            this._process = process;
            this._activeWatchId = this._idleMonitor.add_user_active_watch(() => {
                this._activeWatchId = 0;
                this._stopSaver(true);
            });
            process.wait_async(null, (source, result) => {
                try {
                    source.wait_finish(result);
                } catch (error) {
                    console.error(`GNOME ASCII Saver process error: ${error.message}`);
                }
                this._clearKillTimeout(process);
                if (this._process !== process)
                    return;
                this._process = null;
                if (this._activeWatchId && this._idleMonitor) {
                    this._idleMonitor.remove_watch(this._activeWatchId);
                    this._activeWatchId = 0;
                }
                this._scheduleRetry();
            });
        } catch (error) {
            console.error(`Unable to launch GNOME ASCII Saver: ${error.message}`);
            this._scheduleRetry();
        }
    }

    _clearKillTimeout(process) {
        const sourceId = this._killSources.get(process) ?? 0;
        if (sourceId) {
            GLib.source_remove(sourceId);
            this._killSources.delete(process);
        }
    }

    _stopSaver(rearm) {
        if (this._process) {
            const process = this._process;
            this._process = null;
            try {
                process.send_signal(SIGTERM);
            } catch (error) {
                console.error(`Unable to terminate GNOME ASCII Saver: ${error.message}`);
            }
            this._clearKillTimeout(process);
            const sourceId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, KILL_TIMEOUT_SECONDS, () => {
                this._killSources.delete(process);
                try {
                    process.force_exit();
                } catch (error) {
                    console.error(`Unable to kill GNOME ASCII Saver: ${error.message}`);
                }
                return GLib.SOURCE_REMOVE;
            });
            this._killSources.set(process, sourceId);
        }
        if (rearm)
            this._armIdleWatch();
    }

    _scheduleRetry() {
        if (this._disabled || !this._ownsIdleActivation || this._retrySourceId ||
            !this._settings?.get_boolean('enabled'))
            return;
        this._retrySourceId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 5, () => {
            this._retrySourceId = 0;
            this._armIdleWatch();
            return GLib.SOURCE_REMOVE;
        });
    }
}
