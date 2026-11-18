"""Queue edits preserve transport state and identify repeated tracks individually."""

import math
import uuid


def queue_entry(track):
    if not isinstance(track, dict) or not track.get("id"):
        raise ValueError("Escolha uma faixa válida da biblioteca.")
    entry = dict(track)
    entry["_queue_id"] = uuid.uuid4().hex
    return entry


def duration_seconds(track):
    try:
        duration = float(track.get("duration", 0))
    except (TypeError, ValueError):
        return 0.0
    return duration if math.isfinite(duration) and duration >= 0 else 0.0


def format_duration(seconds):
    seconds = int(max(0, seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


class EditableQueue:
    def _queue_changed(self):
        self.queue_version += 1
        self.original_queue = list(self.queue)
        self.shuffle_mode = False

    def enqueue(self, track, next_up=False):
        entry = queue_entry(track)
        if next_up and self.get_current_track():
            self.queue.insert(self.current_index + 1, entry)
        else:
            self.queue.append(entry)
        if self.current_index < 0 or len(self.queue) == 1:
            self.current_index = 0
        self._queue_changed()
        return entry["_queue_id"]

    def _editable_index(self, index):
        if isinstance(index, bool) or not isinstance(index, int):
            raise ValueError("Posição da fila inválida.")
        if index <= self.current_index or index >= len(self.queue):
            raise ValueError("Somente as próximas faixas podem ser alteradas.")

    def move_queue_entry(self, index, destination):
        self._editable_index(index)
        self._editable_index(destination)
        if index == destination:
            return False
        entry = self.queue.pop(index)
        self.queue.insert(destination, entry)
        self._queue_changed()
        return True

    def remove_queue_entry(self, index):
        self._editable_index(index)
        removed = self.queue.pop(index)
        self._queue_changed()
        return removed

    def clear_upcoming(self):
        start = max(0, self.current_index + 1)
        removed = len(self.queue) - start
        if removed:
            del self.queue[start:]
            self._queue_changed()
        return removed

    def upcoming_duration(self):
        return sum(duration_seconds(track) for track in self.queue[self.current_index + 1:])

    def apply_browser_feedback(self, event):
        """Ignore old queue snapshots and feedback for superseded play commands."""
        if not isinstance(event, dict):
            return False
        if event.get("command") != self.command_version:
            return False
        if event.get("queue_version") != self.queue_version:
            return False
        entries = {track["_queue_id"]: track for track in self.queue}
        if not isinstance(event.get("entry_id"), str) or event["entry_id"] not in entries:
            return False
        order = event.get("order")
        if isinstance(order, list) and all(isinstance(value, str) for value in order):
            if len(order) == len(entries) and set(order) == set(entries):
                self.queue = [entries[value] for value in order]
        index = next((i for i, track in enumerate(self.queue) if track["_queue_id"] == event.get("entry_id")), None)
        if index is None:
            return False
        self.current_index = index
        try:
            position = float(event.get("position", 0))
        except (TypeError, ValueError):
            position = 0
        self._paused_at_pos = position if math.isfinite(position) and position >= 0 else 0
        self.is_playing = event.get("status") == "playing"
        self.is_paused = event.get("status") == "paused"
        if event.get("repeat") in ("off", "all", "one"):
            self.repeat_mode = event["repeat"]
        self.shuffle_mode = bool(event.get("shuffled", False))
        return True
