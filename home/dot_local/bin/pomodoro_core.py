"""Pure state machine for the Pomodoro timer — no GTK dependency."""

# --- Configuration (minutes) ---
WORK_MINUTES = 25
BREAK_MINUTES = 5

# --- Modes ---
WORK = "work"
BREAK = "break"


class PomodoroCore:
    def __init__(self, work_minutes=WORK_MINUTES, break_minutes=BREAK_MINUTES):
        self.work_minutes = work_minutes
        self.break_minutes = break_minutes
        self.mode = WORK
        self.seconds_left = work_minutes * 60
        self.running = False

    def format_time(self):
        m, s = divmod(self.seconds_left, 60)
        prefix = "W" if self.mode == WORK else "B"
        return f"{prefix} {m:02d}:{s:02d}"

    def start(self):
        if self.seconds_left <= 0:
            self._reset_timer()
        self.running = True

    def pause(self):
        self.running = False

    def reset(self):
        self.running = False
        self._reset_timer()

    def tick(self):
        """Advance one second. Returns 'running', 'stopped', or 'done'."""
        if not self.running:
            return "stopped"

        self.seconds_left -= 1

        if self.seconds_left <= 0:
            self.running = False
            return "done"

        return "running"

    def extend(self, minutes):
        self.seconds_left = minutes * 60
        self.running = True

    def transition(self):
        self.mode = BREAK if self.mode == WORK else WORK
        self._reset_timer()
        self.running = True

    def _reset_timer(self):
        duration = self.work_minutes if self.mode == WORK else self.break_minutes
        self.seconds_left = duration * 60


# --- Simple Timer ---
ACTIVE = "active"
IDLE = "idle"


class TimerCore:
    def __init__(self):
        self.mode = IDLE
        self.seconds_left = 0
        self.running = False

    def format_time(self):
        m, s = divmod(self.seconds_left, 60)
        prefix = "T" if self.mode != BREAK else "B"
        return f"{prefix} {m:02d}:{s:02d}"

    def set_timer(self, minutes):
        self.mode = ACTIVE
        self.seconds_left = minutes * 60
        self.running = True

    def set_break(self, minutes):
        self.mode = BREAK
        self.seconds_left = minutes * 60
        self.running = True

    def start(self):
        self.running = True

    def pause(self):
        self.running = False

    def reset(self):
        self.running = False
        self.seconds_left = 0
        self.mode = IDLE

    def stop(self):
        self.running = False
        self.seconds_left = 0
        self.mode = IDLE

    def tick(self):
        """Advance one second. Returns 'running', 'stopped', or 'done'."""
        if not self.running:
            return "stopped"

        self.seconds_left -= 1

        if self.seconds_left <= 0:
            self.running = False
            return "done"

        return "running"

    def extend(self, minutes):
        self.seconds_left = minutes * 60
        self.running = True
