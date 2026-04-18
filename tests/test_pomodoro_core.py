"""Tests for the Pomodoro core state machine."""

import sys
from pathlib import Path

# Add the bin directory so we can import pomodoro_core without installing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "home" / "dot_local" / "bin"))

from pomodoro_core import BREAK, WORK, PomodoroCore


class TestInitialState:
    def test_starts_in_work_mode(self):
        p = PomodoroCore()
        assert p.mode == WORK

    def test_default_work_duration(self):
        p = PomodoroCore()
        assert p.seconds_left == 25 * 60

    def test_custom_durations(self):
        p = PomodoroCore(work_minutes=10, break_minutes=3)
        assert p.seconds_left == 10 * 60

    def test_not_running_initially(self):
        p = PomodoroCore()
        assert p.running is False


class TestFormatTime:
    def test_full_work_timer(self):
        p = PomodoroCore()
        assert p.format_time() == "W 25:00"

    def test_break_mode_prefix(self):
        p = PomodoroCore()
        p.mode = BREAK
        assert p.format_time().startswith("B ")

    def test_partial_time(self):
        p = PomodoroCore()
        p.seconds_left = 65
        assert p.format_time() == "W 01:05"

    def test_zero(self):
        p = PomodoroCore()
        p.seconds_left = 0
        assert p.format_time() == "W 00:00"

    def test_single_digit_seconds(self):
        p = PomodoroCore()
        p.seconds_left = 9
        assert p.format_time() == "W 00:09"


class TestStart:
    def test_sets_running(self):
        p = PomodoroCore()
        p.start()
        assert p.running is True

    def test_resets_if_at_zero(self):
        p = PomodoroCore(work_minutes=25)
        p.seconds_left = 0
        p.start()
        assert p.seconds_left == 25 * 60
        assert p.running is True


class TestPause:
    def test_stops_running(self):
        p = PomodoroCore()
        p.start()
        p.pause()
        assert p.running is False


class TestReset:
    def test_resets_to_mode_duration(self):
        p = PomodoroCore(work_minutes=25)
        p.start()
        p.seconds_left = 100
        p.reset()
        assert p.seconds_left == 25 * 60
        assert p.running is False

    def test_resets_break_duration(self):
        p = PomodoroCore(work_minutes=25, break_minutes=5)
        p.mode = BREAK
        p.seconds_left = 10
        p.reset()
        assert p.seconds_left == 5 * 60


class TestTick:
    def test_decrements_when_running(self):
        p = PomodoroCore(work_minutes=1)
        p.start()
        initial = p.seconds_left
        result = p.tick()
        assert p.seconds_left == initial - 1
        assert result == "running"

    def test_returns_stopped_when_not_running(self):
        p = PomodoroCore()
        result = p.tick()
        assert result == "stopped"
        assert p.seconds_left == 25 * 60  # unchanged

    def test_returns_done_at_zero(self):
        p = PomodoroCore(work_minutes=1)
        p.start()
        p.seconds_left = 1
        result = p.tick()
        assert result == "done"
        assert p.seconds_left == 0
        assert p.running is False

    def test_full_countdown(self):
        p = PomodoroCore(work_minutes=1)
        p.start()
        results = []
        for _ in range(60):
            results.append(p.tick())
        assert results[-1] == "done"
        assert results.count("done") == 1
        assert results.count("running") == 59

    def test_tick_does_not_go_negative(self):
        p = PomodoroCore(work_minutes=1)
        p.start()
        p.seconds_left = 1
        p.tick()  # -> done, seconds_left = 0, running = False
        p.tick()  # -> stopped (not running), no further decrement
        assert p.seconds_left == 0


class TestExtend:
    def test_sets_time_and_starts(self):
        p = PomodoroCore()
        p.seconds_left = 0
        p.running = False
        p.extend(2)
        assert p.seconds_left == 2 * 60
        assert p.running is True

    def test_preserves_mode(self):
        p = PomodoroCore()
        p.mode = BREAK
        p.extend(1)
        assert p.mode == BREAK

    def test_extend_values(self):
        for mins in (1, 2, 3):
            p = PomodoroCore()
            p.extend(mins)
            assert p.seconds_left == mins * 60


class TestTransition:
    def test_work_to_break(self):
        p = PomodoroCore(work_minutes=25, break_minutes=5)
        p.transition()
        assert p.mode == BREAK
        assert p.seconds_left == 5 * 60
        assert p.running is True

    def test_break_to_work(self):
        p = PomodoroCore(work_minutes=25, break_minutes=5)
        p.mode = BREAK
        p.transition()
        assert p.mode == WORK
        assert p.seconds_left == 25 * 60
        assert p.running is True

    def test_double_transition_returns_to_original(self):
        p = PomodoroCore(work_minutes=25, break_minutes=5)
        p.transition()
        p.transition()
        assert p.mode == WORK
        assert p.seconds_left == 25 * 60


class TestFullCycle:
    """Integration-style test of a complete work -> extend -> break -> work cycle."""

    def test_work_extend_break_work(self):
        p = PomodoroCore(work_minutes=1, break_minutes=1)
        p.start()

        # Burn through work timer
        for _ in range(60):
            p.tick()
        assert p.running is False

        # Extend by 1 minute
        p.extend(1)
        assert p.running is True
        assert p.seconds_left == 60

        # Burn through extension
        for _ in range(60):
            p.tick()
        assert p.running is False

        # Transition to break
        p.transition()
        assert p.mode == BREAK
        assert p.seconds_left == 60

        # Burn through break
        for _ in range(60):
            p.tick()
        assert p.running is False

        # Back to work
        p.transition()
        assert p.mode == WORK
        assert p.seconds_left == 60
        assert p.running is True
