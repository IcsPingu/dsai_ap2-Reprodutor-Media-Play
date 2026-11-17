import os
from unittest.mock import patch
from io import BytesIO
from PIL import Image

from core import library, playlist
from storage_case import StorageCase


class LibraryTests(StorageCase):
    def test_external_round_trip_and_legacy_ids(self):
        legacy = {"id": "old-id", "filepath": "old.mp3", "title": "Original",
                  "artist": "Artist", "album": "Album", "cover_path": ""}
        library.save_library([legacy])
        pl = playlist.create_playlist("Old playlist")
        playlist.add_track_to_playlist(pl["id"], "old-id")
        result = library.add_external_track(
            " HTTPS://OPEN.SPOTIFY.COM:443/track/ABC#player ", " Title "
        )
        loaded = library.load_library()
        self.assertEqual([t["id"] for t in result], [t["id"] for t in loaded])
        self.assertEqual(loaded[0]["id"], "old-id")
        self.assertEqual(loaded[0]["title"], "Original")
        self.assertEqual(loaded[0]["source_type"], "local")
        self.assertEqual(loaded[1]["external_url"], "https://open.spotify.com/track/ABC")
        self.assertEqual(loaded[1]["artist"], "Artista Desconhecido")
        self.assertEqual(loaded[1]["title"], "Title")
        self.assertTrue(loaded[1]["id"].startswith("ext_"))
        self.assertEqual(playlist.load_playlists()[0]["track_ids"], ["old-id"])

    def test_invalid_and_duplicate_do_not_write(self):
        self.add_links()
        with open(library.LIBRARY_JSON, "rb") as file:
            before = file.read()
        with self.assertRaises(library.DuplicateTrackError):
            library.add_external_track(
                "https://OPEN.SPOTIFY.COM:443/track/123#x", "Replacement"
            )
        for url, title in (("http://example.org/a", "Title"),
                           ("https://example.org/a", "  ")):
            with self.assertRaises(ValueError):
                library.add_external_track(url, title)
        with open(library.LIBRARY_JSON, "rb") as file:
            self.assertEqual(file.read(), before)

    def test_loading_does_not_rewrite_legacy_json(self):
        library.save_library([{"id": "old", "filepath": "old.mp3"}])
        with open(library.LIBRARY_JSON, "rb") as file:
            before = file.read()
        library.load_library()
        with open(library.LIBRARY_JSON, "rb") as file:
            self.assertEqual(file.read(), before)

    def test_every_import_preserves_links_and_playlist(self):
        links = self.add_links()
        ids = [track["id"] for track in links]
        pl = playlist.create_playlist("Mixed")
        for track_id in ids:
            playlist.add_track_to_playlist(pl["id"], track_id)
        path = os.path.join(self.root, "physical.mp3")
        with open(path, "wb") as file:
            file.write(b"mock audio")
        uploaded = BytesIO(b"mock uploaded audio")
        uploaded.name = "uploaded.mp3"

        def metadata(filepath):
            return {"id": library.generate_track_id(filepath), "filepath": filepath,
                    "title": "Local", "source_type": "local", "cover_path": ""}

        with patch.object(library, "parse_audio_metadata", side_effect=metadata), \
                patch.object(library, "read_audio"):
            results = [
                library.import_files([path, path]),
                library.import_uploaded_files([uploaded]),
                library.scan_directory(self.root),
            ]
        for result in results:
            self.assertEqual([t["id"] for t in result[:2]], ids)
            self.assertEqual(len({t["id"] for t in result}), len(result))
            self.assertEqual(playlist.load_playlists()[0]["track_ids"], ids)
        self.assertEqual(len(library.load_library()), 4)

    def test_external_metadata_and_cover_never_use_id3(self):
        track = self.add_links()[0]
        image = BytesIO()
        Image.new("RGB", (8, 8), "blue").save(image, format="PNG")
        with patch.object(library, "write_audio_tags", side_effect=AssertionError("Tags accessed")):
            self.assertTrue(library.update_track_metadata(
                track["id"], {"title": "Updated", "artist": "Artist", "id": "changed"}
            ))
            cover = library.save_custom_cover(track["id"], image)
            self.assertTrue(os.path.exists(cover))
            with self.assertRaises(ValueError):
                library.update_track_metadata(track["id"], {"title": "  "})
        updated = library.load_library()[0]
        self.assertEqual(updated["title"], "Updated")
        self.assertEqual(updated["cover_path"], cover)
        for field in ("id", "external_url", "platform", "source_type"):
            self.assertEqual(updated[field], track[field])
