import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from core.player import AudioPlayer, start_local_collection


class PlayerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = self.track("a")
        self.b = self.track("b")
        self.external = {"id": "ext", "source_type": "external",
                         "external_url": "https://example.org/track", "filepath": ""}
        with patch("core.player.PYGAME_AVAILABLE", False):
            self.player = AudioPlayer()
        self.player._send = Mock()

    def track(self, name):
        path = os.path.join(self.temp.name, name + ".mp3")
        with open(path, "wb") as file:
            file.write(b"mock audio")
        return {"id": name, "filepath": path, "duration": 100}

    def test_mixed_queue_selection_and_direct_rejection(self):
        self.player.set_queue([self.external, self.a, self.b], start_index=2)
        self.assertEqual(self.player.get_current_track()["id"], "b")
        self.assertEqual([{k: v for k, v in t.items() if k != "_queue_id"} for t in self.player.queue], [self.a, self.b])
        self.assertEqual([{k: v for k, v in t.items() if k != "_queue_id"} for t in self.player.original_queue], [self.a, self.b])
        self.assertTrue(self.player.play(self.b))
        self.player._send.reset_mock()
        state = (list(self.player.queue), self.player.current_index,
                 self.player.is_playing, self.player._play_start_time)
        self.assertFalse(self.player.play(self.external))
        self.assertEqual(state, (self.player.queue, self.player.current_index,
                                 self.player.is_playing, self.player._play_start_time))
        self.player._send.assert_not_called()

    def test_navigation_shuffle_and_repeat_stay_local(self):
        self.player.set_queue([self.external, self.a, self.external, self.b])
        self.player.play(self.a)
        self.assertEqual(self.player.next_track()["id"], "b")
        self.assertEqual(self.player.prev_track()["id"], "a")
        self.player.repeat_mode = "one"
        self.assertEqual(self.player.next_track()["id"], "a")
        self.player.repeat_mode = "all"
        self.player.play(self.b)
        self.assertEqual(self.player.next_track()["id"], "a")
        for _ in range(2):
            self.player.toggle_shuffle()
            self.assertEqual({t["id"] for t in self.player.queue}, {"a", "b"})
            self.assertEqual({t["id"] for t in self.player.original_queue}, {"a", "b"})
        self.player.set_queue([self.external])
        self.assertEqual(self.player.queue, [])
        self.assertIsNone(self.player.get_current_track())

    def test_collection_entry_points(self):
        mixed = [self.external, self.a, self.external, self.b]
        self.assertEqual(start_local_collection(self.player, mixed, "b"), (True, 2))
        self.assertEqual(self.player.get_current_track()["id"], "b")
        self.assertEqual([{k: v for k, v in t.items() if k != "_queue_id"} for t in self.player.queue], [self.a, self.b])
        self.player._send.reset_mock()
        before = list(self.player.queue), self.player.current_index
        self.assertEqual(start_local_collection(self.player, [self.external]), (False, 1))
        self.assertEqual(before, (self.player.queue, self.player.current_index))
        self.player._send.assert_not_called()
        self.assertEqual(start_local_collection(self.player, mixed, "ext"), (False, 2))
        self.assertEqual(before, (self.player.queue, self.player.current_index))
        self.assertEqual(start_local_collection(self.player, mixed), (True, 2))
        self.assertEqual(self.player.get_current_track()["id"], "a")
