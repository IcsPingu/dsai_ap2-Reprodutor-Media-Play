import copy
import tempfile
import unittest
from pathlib import Path

from core.player import AudioPlayer
from core.playback_queue import duration_seconds, format_duration


def track(identity, duration=60):
    return {"id": identity, "title": identity, "filepath": identity + ".wav", "duration": duration}


class EditableQueueTests(unittest.TestCase):
    def setUp(self):
        self.player = AudioPlayer(browser=True)
        self.player.set_queue([track("a"), track("b"), track("c")])
        self.player.is_playing = True
        self.player._paused_at_pos = 12.5

    def ids(self):
        return [item["id"] for item in self.player.queue]

    def event(self, **values):
        event = {
            "command": self.player.command_version,
            "queue_version": self.player.queue_version,
            "entry_id": self.player.queue[0]["_queue_id"],
            "order": [item["_queue_id"] for item in self.player.queue],
            "position": 22,
            "status": "playing",
            "repeat": "off",
        }
        event.update(values)
        return event

    def test_enqueue_next_and_append_preserve_transport(self):
        command = self.player.command_version
        current = self.player.get_current_track()
        self.player.enqueue(track("d"), next_up=True)
        self.player.enqueue(track("e"))
        self.assertEqual(self.ids(), ["a", "d", "b", "c", "e"])
        self.assertIs(self.player.get_current_track(), current)
        self.assertEqual(self.player.command_version, command)
        self.assertEqual(self.player.get_position(), 12.5)
        self.assertTrue(self.player.is_playing)

    def test_duplicates_have_distinct_occurrences_without_mutating_library(self):
        original = track("a")
        snapshot = copy.deepcopy(original)
        first = self.player.enqueue(original)
        second = self.player.enqueue(original)
        self.assertNotEqual(first, second)
        self.assertEqual(original, snapshot)
        self.assertEqual(len({item["_queue_id"] for item in self.player.queue}), 5)

    def test_move_upcoming_keeps_current_index_and_audio(self):
        self.player.move_queue_entry(2, 1)
        self.assertEqual(self.ids(), ["a", "c", "b"])
        self.assertEqual(self.player.current_index, 0)
        self.assertEqual(self.player._paused_at_pos, 12.5)
        self.assertEqual(self.player.command_version, 0)

    def test_remove_specific_duplicate(self):
        self.player.enqueue(track("b"))
        remaining = self.player.queue[3]["_queue_id"]
        self.player.remove_queue_entry(1)
        self.assertEqual(self.ids(), ["a", "c", "b"])
        self.assertEqual(self.player.queue[2]["_queue_id"], remaining)

    def test_current_history_and_invalid_indexes_are_protected(self):
        self.player.current_index = 1
        for index in (-1, 0, 1, 3, True, "2"):
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.player.remove_queue_entry(index)
        with self.assertRaises(ValueError):
            self.player.move_queue_entry(2, 1)
        self.assertEqual(self.ids(), ["a", "b", "c"])

    def test_clear_keeps_history_and_current_without_restart(self):
        self.player.current_index = 1
        self.assertEqual(self.player.clear_upcoming(), 1)
        self.assertEqual(self.ids(), ["a", "b"])
        self.assertEqual(self.player.current_index, 1)
        version = self.player.queue_version
        self.assertEqual(self.player.clear_upcoming(), 0)
        self.assertEqual(self.player.queue_version, version)

    def test_empty_queue_add_selects_first_without_autoplay(self):
        self.player = AudioPlayer(browser=True)
        self.player.enqueue(track("a"), next_up=True)
        self.assertEqual(self.player.current_index, 0)
        self.assertFalse(self.player.is_playing)
        self.player.set_queue([])
        self.assertIsNone(self.player.get_current_track())
        self.assertEqual(self.player.current_index, -1)

    def test_edit_paused_queue_does_not_resume(self):
        self.player.is_paused = True
        self.player.enqueue(track("d"))
        self.assertTrue(self.player.is_paused)
        self.assertEqual(self.player._paused_at_pos, 12.5)

    def test_edit_updates_shuffle_baseline_without_resurrecting_removed_items(self):
        self.player.shuffle_mode = True
        self.player.remove_queue_entry(1)
        self.assertFalse(self.player.shuffle_mode)
        self.assertEqual([item["id"] for item in self.player.original_queue], ["a", "c"])
        self.player.toggle_shuffle()
        self.player.toggle_shuffle()
        self.assertEqual(self.ids(), ["a", "c"])

    def test_feedback_reconciles_actual_browser_order_and_current_occurrence(self):
        order = [self.player.queue[i]["_queue_id"] for i in (2, 0, 1)]
        self.assertTrue(self.player.apply_browser_feedback(self.event(order=order, entry_id=order[0], shuffled=True)))
        self.assertEqual(self.ids(), ["c", "a", "b"])
        self.assertEqual(self.player.current_index, 0)
        self.assertEqual(self.player.get_position(), 22)
        self.assertTrue(self.player.shuffle_mode)

    def test_stale_command_and_queue_feedback_are_ignored(self):
        event = self.event()
        self.player.enqueue(track("d"))
        self.assertFalse(self.player.apply_browser_feedback(event))
        self.assertFalse(self.player.apply_browser_feedback(self.event(command=-1)))
        self.assertEqual(self.ids(), ["a", "b", "c", "d"])

    def test_foreign_entry_or_malformed_order_does_not_inject_tracks(self):
        self.assertFalse(self.player.apply_browser_feedback(self.event(entry_id="foreign")))
        self.assertFalse(self.player.apply_browser_feedback(self.event(entry_id=[])))
        self.assertTrue(self.player.apply_browser_feedback(self.event(order=["foreign"])))
        self.assertEqual(self.ids(), ["a", "b", "c"])
        self.assertTrue(self.player.apply_browser_feedback(self.event(position=float("nan"))))
        self.assertEqual(self.player.get_position(), 0)

    def test_duration_and_display_ignore_invalid_metadata(self):
        self.player.enqueue(track("d", float("nan")))
        self.player.enqueue(track("e", "invalid"))
        self.assertEqual(self.player.upcoming_duration(), 120)
        self.assertEqual(duration_seconds(track("bad", -1)), 0)
        self.assertEqual(format_duration(3661), "1:01:01")
        self.assertEqual(format_duration(61), "01:01")

    def test_play_uses_queue_occurrence_rather_than_first_matching_filepath(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "same.wav"
            path.write_bytes(b"placeholder; decoder not called in browser mode")
            original = {**track("a"), "filepath": str(path)}
            self.player.set_queue([original, original])
            self.assertTrue(self.player.play(self.player.queue[1]))
            self.assertEqual(self.player.current_index, 1)

    def test_sessions_do_not_share_queue_mutations(self):
        other = AudioPlayer(browser=True)
        other.set_queue([track("a")])
        self.player.enqueue(track("d"))
        self.assertEqual(len(other.queue), 1)
        self.assertNotEqual(self.player.queue[0]["_queue_id"], other.queue[0]["_queue_id"])


if __name__ == "__main__":
    unittest.main()
