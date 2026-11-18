from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import soundfile as sf
from PIL import Image

from core import library, playlist
from core.user_storage import select_user, reset_user, user_directory
from storage_case import StorageCase


class LinkAccountTests(StorageCase):
    def test_same_link_is_private_and_covers_are_scoped(self):
        select_user("alice")
        alice = library.add_external_track("https://open.spotify.com/track/1", "Alice title")[0]
        image = BytesIO()
        Image.new("RGB", (8, 8), "red").save(image, format="PNG")
        cover = library.save_custom_cover(alice["id"], image)
        self.assertTrue(Path(cover).is_relative_to(user_directory()))
        created = playlist.create_playlist("Alice private")
        playlist.add_track_to_playlist(created["id"], alice["id"])
        select_user("bob")
        self.assertEqual(library.load_library(), [])
        self.assertEqual(playlist.load_playlists(), [])
        bob = library.add_external_track("https://open.spotify.com/track/1", "Bob title")[0]
        self.assertEqual(bob["id"], alice["id"])
        self.assertFalse(playlist.delete_playlist(created["id"]))
        library.update_track_metadata(bob["id"], {"title": "Bob edited"})
        library.set_favorite(bob["id"], True)
        self.assertEqual(library.resolve_coverpath(cover), "")
        select_user("alice")
        self.assertEqual(library.load_library()[0]["title"], "Alice title")
        self.assertFalse(library.load_library()[0]["favorite"])
        self.assertEqual(playlist.load_playlists()[0]["track_ids"], [alice["id"]])

    def test_parallel_duplicate_registration_is_atomic(self):
        def worker(_):
            token = select_user("alice")
            try:
                try:
                    library.add_external_track("https://example.org/song", "Song")
                    return "added"
                except library.DuplicateTrackError:
                    return "duplicate"
            finally:
                reset_user(token)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(worker, range(4)))
        self.assertEqual(results.count("added"), 1)
        select_user("alice")
        self.assertEqual(len(library.load_library()), 1)

    def test_real_uploads_preserve_links_for_every_format(self):
        select_user("alice")
        links = self.add_links()
        ids = [track["id"] for track in links]
        created = playlist.create_playlist("Mixed")
        for identity in ids:
            playlist.add_track_to_playlist(created["id"], identity)
        for extension in ("mp3", "wav", "flac"):
            upload = BytesIO()
            sf.write(upload, [0.] * 8000, 8000, format=extension.upper())
            upload.name = f"test.{extension}"
            tracks = library.import_uploaded_files([upload])
            self.assertEqual([track["id"] for track in tracks[:2]], ids)
            self.assertEqual(playlist.load_playlists()[0]["track_ids"], ids)
        self.assertEqual({t["format"] for t in tracks if t["source_type"] == "local"},
                         {"mp3", "wav", "flac"})
        with patch.object(library, "write_audio_tags") as write:
            library.update_track_metadata(ids[0], {"title": "Edited link"})
            write.assert_not_called()
        select_user("bob")
        self.assertEqual(library.load_library(), [])
