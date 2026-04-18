"""Tests for the simple timer core state machine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "home" / "dot_local" / "bin"))

from pomodoro_core import TimerCore

ACTIVE = "active"
BREAK = "break"
IDLE = "idle"


class TestInitialState:
    def test_starts_idle(self):
        t = TimerCore()
        assert t.mode == IDLE

    def test_not_running(self):
        t = TimerCore()
        assert t.running is False

    def test_zero_seconds(self):
        t = TimerCore()
        assert t.seconds_left == 0


class TestFormatTime:
    def test_idle_format(self):
        t = TimerCore()
        assert t.format_time() == "T 00:00"

    def test_active_format(self):
        t = TimerCore()
        t.set_timer(10)
        assert t.format_time() == "T 10:00"

    def test_break_format(self):
        t = TimerCore()
        t.set_break(5)
        assert t.format_time() == "B 05:00"

    def test_partial_time(self):
        t = TimerCore()
        t.set_timer(1)
        t.seconds_left = 65
        assert t.format_time() == "T 01:05"


class TestSetTimer:
    def test_sets_duration_and_starts(self):
        t = TimerCore()
        t.set_timer(15)
        assert t.seconds_left == 15 * 60
        assert t.running is True
        assert t.mode == ACTIVE

    def test_various_durations(self):
        for mins in (1, 5, 30, 90):
            t = TimerCore()
            t.set_timer(mins)
            assert t.seconds_left == mins * 60


class TestSetBreak:
    def test_sets_break_duration_and_starts(self):
        t = TimerCore()
        t.set_break(10)
        assert t.seconds_left == 10 * 60
        assert t.running is True
        assert t.mode == BREAK

    def test_various_break_durations(self):
        for mins in (1, 3, 15):
            t = TimerCore()
            t.set_break(mins)
            assert t.seconds_left == mins * 60
            assert t.mode == BREAK


class TestTick:
    def test_decrements_when_running(self):
        t = TimerCore()
        t.set_timer(1)
        initial = t.seconds_left
        result = t.tick()
        assert t.seconds_left == initial - 1
        assert result == "running"

    def test_stopped_when_not_running(self):
        t = TimerCore()
        result = t.tick()
        assert result == "stopped"

    def test_done_at_zero(self):
        t = TimerCore()
        t.set_timer(1)
        t.seconds_left = 1
        result = t.tick()
        assert result == "done"
        assert t.running is False

    def test_full_countdown(self):
        t = TimerCore()
        t.set_timer(1)
        results = []
        for _ in range(60):
            results.append(t.tick())
        assert results[-1] == "done"
        assert results.count("running") == 59

    def test_no_negative(self):
        t = TimerCore()
        t.set_timer(1)
        t.seconds_left = 1
        t.tick()
        t.tick()
        assert t.seconds_left == 0


class TestPauseReset:
    def test_pause(self):
        t = TimerCore()
        t.set_timer(10)
        t.pause()
        assert t.running is False
        assert t.mode == ACTIVE  # mode preserved

    def test_resume_after_pause(self):
        t = TimerCore()
        t.set_timer(10)
        t.tick()
        t.tick()
        saved = t.seconds_left
        t.pause()
        t.start()
        assert t.seconds_left == saved
        assert t.running is True

    def test_reset(self):
        t = TimerCore()
        t.set_timer(10)
        t.tick()
        t.reset()
        assert t.running is False
        assert t.seconds_left == 0
        assert t.mode == IDLE


class TestExtend:
    def test_extend_sets_time_and_runs(self):
        t = TimerCore()
        t.set_timer(1)
        # burn through
        for _ in range(60):
            t.tick()
        t.extend(2)
        assert t.seconds_left == 2 * 60
        assert t.running is True

    def test_extend_preserves_mode(self):
        t = TimerCore()
        t.set_break(5)
        for _ in range(5 * 60):
            t.tick()
        t.extend(1)
        assert t.mode == BREAK

    def test_extend_values(self):
        for mins in (1, 2, 3):
            t = TimerCore()
            t.set_timer(1)
            t.seconds_left = 0
            t.running = False
            t.extend(mins)
            assert t.seconds_left == mins * 60


class TestStop:
    def test_stop_goes_idle(self):
        t = TimerCore()
        t.set_timer(10)
        t.stop()
        assert t.running is False
        assert t.mode == IDLE
        assert t.seconds_left == 0


class TestFullCycle:
    """Active timer -> extend -> break -> extend break -> stop."""

    def test_timer_extend_break_extend_stop(self):
        t = TimerCore()

        # Start 1-minute timer
        t.set_timer(1)
        assert t.mode == ACTIVE

        # Burn through
        for _ in range(60):
            t.tick()
        assert t.running is False

        # Extend by 1 min
        t.extend(1)
        assert t.running is True
        assert t.mode == ACTIVE

        # Burn through extension
        for _ in range(60):
            t.tick()
        assert t.running is False

        # Start 2-minute break
        t.set_break(2)
        assert t.mode == BREAK
        assert t.seconds_left == 120

        # Burn through break
        for _ in range(120):
            t.tick()
        assert t.running is False

        # Extend break by 1 min
        t.extend(1)
        assert t.mode == BREAK
        assert t.running is True

        # Burn through
        for _ in range(60):
            t.tick()
        assert t.running is False

        # Stop
        t.stop()
        assert t.mode == IDLE
        assert t.seconds_left == 0
