from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from core.library import save_library
from core.listening_history import (
    available_track, clear_history, confirmation_threshold, filter_history,
    history_path, history_state, history_statistics, record_confirmation,
)
from core.user_storage import select_user, reset_user


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, MEDIA_PLAY_DATA=self.directory.name)
        self.environment.start()
        self.token = select_user("alice")
        self.track = dict(id="a", title="Água", artist="Banda", album="Disco", duration=30)
        save_library([self.track, dict(id="short", duration=2), dict(id="external", source_type="external")])
        self.generation = history_state()["generation"]

    def tearDown(self):
        reset_user(self.token)
        self.environment.stop()
        self.directory.cleanup()

    def confirmation(self, **values):
        event = dict(attempt_id=str(uuid.uuid4()), track_id="a", listened_seconds=5.1, generation=self.generation)
        event.update(values)
        return event

    def test_confirmation_persists_snapshot_and_uses_server_timestamp(self):
        event = self.confirmation(played_at="1900-01-01T00:00:00+00:00")
        self.assertEqual(record_confirmation(event), "recorded")
        saved = history_state()["events"][0]
        self.assertEqual(saved["title"], "Água")
        self.assertEqual(saved["artist"], "Banda")
        self.assertNotEqual(saved["played_at"], event["played_at"])
        self.assertNotIn("filepath", saved)
        self.assertIsNotNone(datetime.fromisoformat(saved["played_at"]).tzinfo)

    def test_retries_do_not_duplicate_but_another_attempt_does(self):
        event = self.confirmation()
        self.assertEqual(record_confirmation(event), "recorded")
        self.assertEqual(record_confirmation(event), "duplicate")
        self.assertEqual(record_confirmation(self.confirmation()), "recorded")
        self.assertEqual(len(history_state()["events"]), 2)

    def test_invalid_or_unheard_tracks_are_not_recorded(self):
        invalid = [None, {}, self.confirmation(listened_seconds=4.9),
                   self.confirmation(listened_seconds=True), self.confirmation(listened_seconds=float("nan")),
                   self.confirmation(listened_seconds=float("inf")), self.confirmation(attempt_id="bad"),
                   self.confirmation(track_id="missing"), self.confirmation(track_id="external")]
        for event in invalid:
            with self.subTest(event=event):
                self.assertEqual(record_confirmation(event), "invalid")
        self.assertEqual(history_state()["events"], [])

    def test_short_tracks_require_half_their_duration(self):
        self.assertEqual(confirmation_threshold(dict(duration=2)), 1)
        self.assertEqual(confirmation_threshold(dict(duration=0)), 5)
        self.assertEqual(record_confirmation(self.confirmation(track_id="short", listened_seconds=.9)), "invalid")
        self.assertEqual(record_confirmation(self.confirmation(track_id="short", listened_seconds=1)), "recorded")

    def test_clear_rotates_generation_and_rejects_pending_old_events(self):
        old = self.confirmation()
        record_confirmation(old)
        generation = clear_history()
        self.assertNotEqual(generation, self.generation)
        self.assertEqual(record_confirmation(old), "stale")
        self.assertEqual(history_state()["events"], [])
        self.assertEqual(record_confirmation(self.confirmation(generation=generation)), "recorded")

    def test_user_isolation_and_no_anonymous_history(self):
        record_confirmation(self.confirmation())
        select_user("bob")
        self.assertEqual(history_state()["events"], [])
        clear_history()
        select_user("alice")
        self.assertEqual(len(history_state()["events"]), 1)
        select_user(None)
        with self.assertRaises(ValueError):
            history_state()

    def test_concurrent_retry_is_idempotent(self):
        event = self.confirmation()
        def worker(_):
            token = select_user("alice")
            try:
                return record_confirmation(event)
            finally:
                reset_user(token)
        with ThreadPoolExecutor(max_workers=3) as pool:
            outcomes = list(pool.map(worker, range(3)))
        self.assertEqual(outcomes.count("recorded"), 1)
        self.assertEqual(len(history_state()["events"]), 1)

    def test_bad_file_is_preserved(self):
        history_path().write_text("broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            history_state()
        self.assertEqual(history_path().read_text(encoding="utf-8"), "broken")

    @unittest.skipUnless(os.name == "nt", "Windows file sharing semantics")
    def test_atomic_write_retries_windows_reader_lock_and_preserves_old_file_on_failure(self):
        original_replace = os.replace
        attempts = []
        def temporary_lock(source, target):
            attempts.append(target)
            if len(attempts) == 1:
                raise PermissionError("reader temporarily holds file")
            return original_replace(source, target)
        with patch("core.user_storage.os.replace", side_effect=temporary_lock), patch("core.user_storage.time.sleep"):
            self.assertEqual(record_confirmation(self.confirmation()), "recorded")
        self.assertEqual(len(attempts), 2)
        saved = history_path().read_bytes()
        with patch("core.user_storage.os.replace", side_effect=PermissionError("locked")), patch("core.user_storage.time.sleep"):
            with self.assertRaises(PermissionError):
                record_confirmation(self.confirmation())
        self.assertEqual(history_path().read_bytes(), saved)

    def test_calendar_periods_use_sao_paulo_midnight(self):
        # 03:30 UTC is 00:30 in São Paulo.
        now = datetime(2026, 11, 19, 3, 30, tzinfo=timezone.utc)
        events = [dict(track_id="a", played_at=value) for value in (
            "2026-11-19T03:00:00+00:00", "2026-11-19T02:59:59+00:00",
            "2026-11-13T03:00:00+00:00", "2026-11-13T02:59:59+00:00",
            "2026-11-20T03:00:00+00:00")]
        self.assertEqual(len(filter_history(events, "today", now)), 1)
        self.assertEqual(len(filter_history(events, "week", now)), 3)
        self.assertEqual(len(filter_history(events, "all", now)), 4)
        with self.assertRaises(ValueError):
            filter_history(events, "invalid", now)

    def test_ranking_uses_counts_and_latest_snapshot(self):
        events = [dict(track_id="a", title="Old", artist="Band", played_at="2026-11-18T12:00:00+00:00"),
                  dict(track_id="b", title="Other", played_at="2026-11-18T13:00:00+00:00"),
                  dict(track_id="a", title="New", artist="Band", played_at="2026-11-19T12:00:00+00:00")]
        stats = history_statistics(events)
        self.assertEqual(stats["plays"], 3)
        self.assertEqual(stats["unique_tracks"], 2)
        self.assertEqual(stats["ranking"][0]["plays"], 2)
        self.assertEqual(stats["ranking"][0]["title"], "New")
        self.assertEqual(history_statistics([])["ranking"], [])

    def test_actions_require_file_still_available(self):
        path = history_path().parent / "a.wav"
        path.write_bytes(b"test")
        library = [dict(id="a", filepath=str(path))]
        self.assertIsNotNone(available_track(dict(track_id="a"), library))
        path.unlink()
        self.assertIsNone(available_track(dict(track_id="a"), library))
        self.assertIsNone(available_track(dict(track_id="missing"), library))


if __name__ == "__main__":
    unittest.main()
