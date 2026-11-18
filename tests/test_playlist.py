from core import library, playlist
from storage_case import StorageCase


class PlaylistTests(StorageCase):
    def test_mixed_playlist_lifecycle(self):
        library.save_library([{"id": "legacy", "filepath": "old.mp3", "title": "MP3"}])
        tracks = self.add_links()
        ids = [track["id"] for track in tracks]
        created = playlist.create_playlist("Mixed")
        for track_id in ids:
            self.assertTrue(playlist.add_track_to_playlist(created["id"], track_id))
        self.assertFalse(playlist.add_track_to_playlist(created["id"], ids[1]))
        self.assertEqual(playlist.load_playlists()[0]["track_ids"], ids)
        self.assertTrue(playlist.rename_playlist(created["id"], "Renamed"))
        self.assertEqual(playlist.get_playlist_by_id(created["id"])["name"], "Renamed")
        self.assertTrue(playlist.remove_track_from_playlist(created["id"], ids[1]))
        self.assertEqual(playlist.load_playlists()[0]["track_ids"], [ids[0], ids[2]])
        self.assertEqual([track["id"] for track in library.load_library()], ids)
        self.assertTrue(playlist.delete_playlist(created["id"]))
        self.assertEqual(playlist.load_playlists(), [])
