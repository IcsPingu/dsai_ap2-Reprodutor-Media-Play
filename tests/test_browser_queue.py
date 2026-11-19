from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ui import browser_player
from storage_case import StorageCase
from core.user_storage import user_directory
from core.listening_history import history_state


class BrowserQueueTests(StorageCase):
    def test_component_excludes_even_directly_injected_external_record(self):
        path = Path(self.root) / "local.wav"
        path.write_bytes(b"local audio fixture")
        local = dict(_queue_id="local_entry", id="local", filepath=str(path), title="Local")
        external = dict(id="link", source_type="external", filepath=str(path),
                        external_url="https://example.org/track")
        player = SimpleNamespace(
            queue=[external, local], get_current_track=lambda: local,
            queue_version=1, command_version=1, is_playing=True, is_paused=False,
            _paused_at_pos=0, volume=.8, repeat_mode="off",
        )
        with patch.object(browser_player, "_component", return_value=None) as component:
            browser_player.render_browser_player.__wrapped__(player)
        sent = component.call_args.kwargs
        self.assertEqual([track["id"] for track in sent["queue"]], ["local"])
        self.assertTrue(sent["queue"][0]["src"].startswith("data:audio/wav;base64,"))

    def test_fragment_restores_authenticated_context_before_loading_history(self):
        player = SimpleNamespace(
            queue=[], get_current_track=lambda: None, queue_version=0,
            command_version=0, is_playing=False, is_paused=False,
            _paused_at_pos=0, volume=.8, repeat_mode="off",
        )
        with patch.object(browser_player.st, "session_state", {"identity": "alice"}):
            with patch.object(browser_player, "_component", return_value=None) as component:
                browser_player.render_browser_player.__wrapped__(player)
        self.assertIsNotNone(user_directory())
        self.assertEqual(component.call_args.kwargs["history_generation"], history_state()["generation"])
