from pathlib import Path
from unittest.mock import Mock, patch
import os

from streamlit.testing.v1 import AppTest

from core import library, playlist
from core.user_storage import select_user, reset_user, user_directory
from storage_case import StorageCase


APP = str(Path(__file__).resolve().parents[1] / "app.py")


class AppTests(StorageCase):
    def setUp(self):
        super().setUp()
        self.stack.enter_context(patch("core.player.PYGAME_AVAILABLE", False))
        self.stack.callback(reset_user, select_user("link_test"))
        self.media = str(user_directory() / "media")
        os.makedirs(self.media, exist_ok=True)

    def open_app(self, menu):
        app = AppTest.from_file(APP)
        app.session_state["identity"] = "link_test"
        app.run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        app.sidebar.radio[0].set_value(menu).run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_add_and_remove_links_from_playlist_ui(self):
        tracks = self.add_links()
        app = self.open_app("🎵 Playlists")
        next(t for t in app.text_input if t.label == "Nome da Nova Playlist:").set_value("Mixed")
        next(b for b in app.button if b.label == "➕ Criar Playlist").click().run()
        created = playlist.load_playlists()[0]
        app.sidebar.radio[0].set_value("📚 Biblioteca de Mídias").run()
        for track in tracks:
            app.button(key=f"add_pl_{track['id']}").click().run()
        self.assertEqual(playlist.load_playlists()[0]["track_ids"],
                         [track["id"] for track in tracks])
        app.sidebar.radio[0].set_value("🎵 Playlists").run()
        app.button(key=f"rm_pl_{created['id']}_{tracks[0]['id']}").click().run()
        self.assertEqual(playlist.load_playlists()[0]["track_ids"], [tracks[1]["id"]])
        self.assertEqual(len(library.load_library()), 2)
        self.assertEqual(len(app.exception), 0)

    def submit_link(self, app, url, title):
        app.text_input(key="link_url").set_value(url)
        app.text_input(key="link_title").set_value(title)
        next(button for button in app.button if button.label == "🔗 Adicionar Link").click().run()
        self.assertEqual(len(app.exception), 0)

    def test_link_form_validation_duplicate_and_session(self):
        app = self.open_app("📁 Importar Áudios")
        self.submit_link(app, "https://open.spotify.com/track/123", " ")
        self.assertTrue(any("título" in error.value for error in app.error))
        self.assertEqual(library.load_library(), [])
        self.submit_link(app, "javascript:alert(1)", "Bad URL")
        self.assertTrue(app.error)
        self.assertEqual(library.load_library(), [])
        self.submit_link(app, "https://open.spotify.com/track/123", "My song")
        self.assertTrue(app.success)
        self.assertEqual(len(app.session_state["library"]), 1)
        self.submit_link(app, "https://OPEN.SPOTIFY.COM:443/track/123#x", "Replacement")
        self.assertTrue(any("já está" in warning.value for warning in app.warning))
        self.assertEqual(library.load_library()[0]["title"], "My song")

    def test_sources_links_invalid_persisted_url_and_plain_metadata(self):
        tracks = self.add_links()
        library.update_track_metadata(tracks[0]["id"], {
            "title": "<script>window.bad=true</script>", "artist": "<b>Artist</b>",
        })
        tracks = library.load_library()
        invalid = dict(tracks[0], id="bad", external_url="javascript:alert(1)")
        library.save_library(tracks + [invalid])
        pl = playlist.create_playlist("Mixed")
        for track in tracks + [invalid]:
            playlist.add_track_to_playlist(pl["id"], track["id"])
        app = self.open_app("📚 Biblioteca de Mídias")
        urls = [element.proto.url for element in app.get("link_button")]
        self.assertEqual(urls, [t["external_url"] for t in tracks])
        captions = [element.value for element in app.caption]
        self.assertTrue(any("Spotify" in text for text in captions))
        self.assertTrue(any("Link externo · example.org" in text for text in captions))
        self.assertTrue(any("inválido" in text for text in captions))
        self.assertTrue(any("<script>" in text.value for text in app.text))
        self.assertFalse(any(button.key and button.key.startswith("lib_play_")
                             for button in app.button))
        app.sidebar.radio[0].set_value("🎵 Playlists").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual([element.proto.url for element in app.get("link_button")], urls)
        self.assertFalse(any("<script>" in element.value
                             for element in app.markdown if element.proto.allow_html))

    def test_playback_entry_points_filter_and_preserve_state(self):
        tracks = self.add_links()
        path = os.path.join(self.media, "local.mp3")
        with open(path, "wb") as file:
            file.write(b"mock audio")
        local = dict(tracks[0], id="local", source_type="local",
                     filepath=path, title="Local song", duration_str="00:10", duration=10)
        library.save_library(tracks + [local])
        pl = playlist.create_playlist("Mixed")
        for track in tracks + [local]:
            playlist.add_track_to_playlist(pl["id"], track["id"])
        app = self.open_app("📚 Biblioteca de Mídias")
        player = app.session_state["player"]
        player._send = Mock()
        app.button(key="lib_play_local").click().run()
        self.assertEqual(player.get_current_track()["id"], "local")
        self.assertEqual([t["id"] for t in player.queue], ["local"])
        self.assertTrue(any("2 link(s)" in info.value for info in app.info))
        app.sidebar.radio[0].set_value("🎵 Playlists").run()
        next(b for b in app.button if b.label == "▶ Reproduzir Áudios Locais da Playlist").click().run()
        self.assertTrue(any("2 link(s)" in info.value for info in app.info))
        player.stop()
        player.queue = []
        # O modo web inicia pelo botão da coleção; controles ficam no componente.
        app.sidebar.radio[0].set_value("📚 Biblioteca de Mídias").run()
        next(b for b in app.button if b.label == "▶ Reproduzir Áudios Locais da Biblioteca").click().run()
        self.assertEqual([t["id"] for t in player.queue], ["local"])
        self.assertTrue(any("2 link(s)" in info.value for info in app.info))
        # Uma coleção externa não interrompe a faixa em execução.
        app.session_state["library"] = tracks
        app.sidebar.radio[0].set_value("📚 Biblioteca de Mídias").run()
        before = list(player.queue), player.current_index, player.is_playing
        player._send.reset_mock()
        next(b for b in app.button if b.label == "▶ Reproduzir Áudios Locais da Biblioteca").click().run()
        self.assertEqual(before, (player.queue, player.current_index, player.is_playing))
        player._send.assert_not_called()
        self.assertTrue(any("Não há faixas locais" in w.value for w in app.warning))
        self.assertEqual(len(app.exception), 0)

    def test_smart_links_only_preserves_player_and_mixed_selection_filters_links(self):
        tracks = self.add_links()
        path = os.path.join(self.media, "local.wav")
        with open(path, "wb") as file:
            file.write(b"mock audio")
        local = dict(tracks[0], id="local", source_type="local", filepath=path, title="Local")
        library.save_library(tracks + [local])
        smart = playlist.create_smart_playlist("External", {
            "rules": [{"field": "source_type", "operator": "equals", "value": "external"}],
        })
        app = self.open_app("🎵 Playlists")
        player = app.session_state["player"]
        player.set_queue([local])
        player.play(local)
        before = list(player.queue), player.command_version, player.current_index
        next(b for b in app.button if b.label == "Reproduzir seleção inteligente").click().run()
        self.assertEqual(before, (player.queue, player.command_version, player.current_index))
        self.assertTrue(any("Não há faixas locais" in w.value for w in app.warning))
        self.assertEqual(len(app.get("link_button")), 2)
        # Uma definição que inclui toda a coleção gera apenas a faixa local na fila.
        playlist.update_smart_playlist(smart["id"], "Mixed", {
            "rules": [{"field": "title", "operator": "not_contains", "value": "never-match"}],
        })
        app.run()
        next(b for b in app.button if b.label == "Reproduzir seleção inteligente").click().run()
        self.assertEqual([t["id"] for t in player.queue], ["local"])
        self.assertTrue(any("2 link(s)" in info.value for info in app.info))
        self.assertEqual(len(app.exception), 0)

    def test_origin_and_platform_ui_filters(self):
        self.add_links()
        app = self.open_app("📚 Biblioteca de Mídias")
        next(w for w in app.multiselect if w.label == "Plataforma").set_value(["Spotify"]).run()
        self.assertEqual(len(app.get("link_button")), 1)
        self.assertEqual(app.get("link_button")[0].proto.url, "https://open.spotify.com/track/123")
        next(w for w in app.multiselect if w.label == "Origem").set_value(["Local"]).run()
        self.assertEqual(len(app.get("link_button")), 0)

    def test_smart_editor_saves_origin_and_platform_rules(self):
        self.add_links()
        app = self.open_app("🎵 Playlists")
        app.text_input(key="smart_new_name").set_value("Spotify links")
        app.number_input(key="smart_new_count").set_value(2).run()
        app.selectbox(key="smart_new_rule_0_field").set_value("Origem").run()
        app.selectbox(key="smart_new_rule_0_source_type_value").set_value("Link externo").run()
        app.selectbox(key="smart_new_rule_1_field").set_value("Plataforma").run()
        app.selectbox(key="smart_new_rule_1_platform_value").set_value("Spotify").run()
        app.button(key="smart_new_save").click().run()
        saved = playlist.load_playlists()[0]
        self.assertEqual(saved["definition"]["rules"], [
            {"field": "source_type", "operator": "equals", "value": "external"},
            {"field": "platform", "operator": "equals", "value": "Spotify"},
        ])
        self.assertEqual(len(playlist.resolve_playlist_tracks(saved, library.load_library())), 1)
        self.assertEqual(len(app.exception), 0)
