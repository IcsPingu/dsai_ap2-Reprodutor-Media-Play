import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from core.library import save_library
from core.playlist import load_playlists
from core.playlist import create_smart_playlist
from core.user_storage import select_user, reset_user


SCRIPT = '''
import streamlit as st
from core.user_storage import select_user
from core.player import AudioPlayer
from ui.smart_playlists import render_smart_playlists
select_user("alice")
if "player" not in st.session_state:
    st.session_state.player = AudioPlayer(browser=True)
render_smart_playlists(st.session_state.player)
'''


class SmartPlaylistUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, MEDIA_PLAY_DATA=self.temp.name)
        self.environment.start()
        self.token = select_user("alice")
        save_library([
            dict(id="a", title="Rock favorito", artist="Banda", album="Disco", favorite=True, duration=100, filepath="", cover_path=""),
            dict(id="b", title="Outra faixa", artist="Outra", album="Outro", favorite=False, duration=200, filepath="", cover_path=""),
        ])
        self.app = AppTest.from_string(SCRIPT).run()

    def tearDown(self):
        reset_user(self.token)
        self.environment.stop()
        self.temp.cleanup()

    def button(self, label):
        return next(button for button in self.app.button if button.label == label)

    def test_create_preview_edit_and_delete(self):
        self.app.text_input(key="smart_new_name").set_value("Favoritas")
        self.button("Pré-visualizar seleção").click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.dataframe[0].value), 1)
        self.button("Salvar playlist inteligente").click().run()
        self.assertEqual(len(self.app.exception), 0)
        select_user("alice")
        playlist = load_playlists()[0]
        self.assertEqual(playlist["name"], "Favoritas")
        self.assertEqual(len(self.app.dataframe[0].value), 1)
        self.app.text_input(key=f"smart_edit_{playlist['id']}_name").set_value("Renomeada")
        self.button("Salvar alterações da inteligente").click().run()
        self.assertEqual(len(self.app.exception), 0)
        select_user("alice")
        self.assertEqual(load_playlists()[0]["name"], "Renomeada")
        self.button("Excluir playlist inteligente").click().run()
        select_user("alice")
        self.assertEqual(load_playlists(), [])
        self.assertEqual(len(self.app.exception), 0)

    def test_invalid_name_shows_error_without_saving(self):
        self.button("Salvar playlist inteligente").click().run()
        self.assertTrue(self.app.error)
        self.assertEqual(len(self.app.exception), 0)
        select_user("alice")
        self.assertEqual(load_playlists(), [])

    def test_main_app_integrates_smart_and_manual_sections(self):
        create_smart_playlist("Favoritas", {
            "rules": [{"field": "favorite", "operator": "equals", "value": True}],
        })
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
        app.session_state["identity"] = "alice"
        app.run()
        navigation = next(widget for widget in app.radio if widget.label == "Navegação")
        navigation.set_value("🎵 Playlists").run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn("Playlists inteligentes", [heading.value for heading in app.subheader])
        self.assertIn("🎵 Playlists manuais", [heading.value for heading in app.subheader])
        self.assertTrue(any(button.label == "Reproduzir seleção inteligente" for button in app.button))


if __name__ == "__main__":
    unittest.main()
