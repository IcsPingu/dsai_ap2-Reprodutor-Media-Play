import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
from streamlit.testing.v1 import AppTest

from core.library import save_library
from core.listening_history import history_path, history_state, record_confirmation
from core.user_storage import select_user, reset_user


SCRIPT = '''
import streamlit as st
from core.user_storage import select_user
from core.player import AudioPlayer
from ui.listening_history import render_listening_history
select_user("alice")
if "player" not in st.session_state:
    st.session_state.player = AudioPlayer(browser=True)
render_listening_history(st.session_state.player)
'''


class HistoryUITests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, MEDIA_PLAY_DATA=self.directory.name)
        self.environment.start()
        self.token = select_user("alice")
        self.file = history_path().parent / "track.wav"
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_bytes(b"test file; playback decoded in browser E2E")
        save_library([dict(id="a", title="Música", artist="Banda", duration=30, filepath=str(self.file))])
        record_confirmation(dict(attempt_id=str(uuid.uuid4()), track_id="a", listened_seconds=5.2,
                                 generation=history_state()["generation"]))
        self.app = AppTest.from_string(SCRIPT).run()

    def tearDown(self):
        reset_user(self.token)
        self.environment.stop()
        self.directory.cleanup()

    def button(self, label):
        return next(button for button in self.app.button if button.label == label)

    def test_statistics_and_enqueue_do_not_start_playback(self):
        self.assertEqual(self.app.metric[0].value, "1")
        self.assertEqual(self.app.metric[1].value, "1")
        self.button("Adicionar ao final da fila").click().run()
        self.assertEqual(len(self.app.exception), 0)
        player = self.app.session_state.player
        self.assertEqual(player.queue[0]["id"], "a")
        self.assertFalse(player.is_playing)
        select_user("alice")
        self.assertEqual(len(history_state()["events"]), 1)

    def test_play_again_is_not_counted_before_browser_confirmation(self):
        self.button("Tocar novamente").click().run()
        self.assertTrue(self.app.session_state.player.is_playing)
        select_user("alice")
        self.assertEqual(len(history_state()["events"]), 1)

    def test_clear_requires_confirmation_and_preserves_queue(self):
        self.button("Adicionar ao final da fila").click().run()
        queue = list(self.app.session_state.player.queue)
        self.assertTrue(self.button("Limpar histórico").disabled)
        next(w for w in self.app.checkbox if w.label.startswith("Confirmo")).set_value(True).run()
        self.button("Limpar histórico").click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.metric[0].value, "0")
        self.assertEqual(self.app.session_state.player.queue, queue)
        self.assertFalse(next(w for w in self.app.checkbox if w.label.startswith("Confirmo")).value)

    def test_missing_file_keeps_history_but_disables_actions(self):
        self.file.unlink()
        self.app.run()
        self.assertEqual(self.app.metric[0].value, "1")
        self.assertTrue(self.button("Tocar novamente").disabled)
        self.assertTrue(self.button("Adicionar ao final da fila").disabled)

    def test_history_is_available_in_main_app_navigation(self):
        app = AppTest.from_file("app.py")
        app.session_state["identity"] = "alice"
        app.run()
        navigation = next(w for w in app.radio if w.label == "Navegação")
        navigation.set_value("📊 Histórico").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, "1")


if __name__ == "__main__":
    unittest.main()
