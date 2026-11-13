import io
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import soundfile as sf
from core import library, playlist
from core.user_storage import register, authenticate, select_user, reset_user, data_root
from core.library_filters import filter_library, missing_metadata


class UserLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, MEDIA_PLAY_DATA=self.temp.name)
        self.environment.start()
        self.token = select_user(None)

    def tearDown(self):
        reset_user(self.token)
        self.environment.stop()
        self.temp.cleanup()

    def upload(self):
        content = io.BytesIO()
        sf.write(content, [0.] * 8000, 8000, format='WAV')
        content.name = 'same.wav'
        return content

    def test_credentials_and_hashes_survive_reopen(self):
        register('Alice', 'a long test password')
        self.assertEqual(authenticate('alice', 'a long test password'), 'alice')
        self.assertIsNone(authenticate('alice', 'wrong password'))
        self.assertIsNone(authenticate('nobody', 'a long test password'))
        with self.assertRaises(ValueError):
            register('alice', 'another long password')
        self.assertNotIn(b'a long test password', (data_root() / 'accounts.sqlite').read_bytes())

    def test_users_cannot_read_or_modify_each_others_media(self):
        select_user('alice')
        track = library.import_uploaded_files([self.upload()])[0]
        library.set_favorite(track['id'], True)
        created = playlist.create_playlist('Private')
        playlist.add_track_to_playlist(created['id'], track['id'])
        select_user('bob')
        self.assertEqual(library.load_library(), [])
        self.assertEqual(playlist.load_playlists(), [])
        self.assertFalse(library.set_favorite(track['id'], False))
        self.assertEqual(library.resolve_filepath(track['filepath']), '')
        with self.assertRaises(ValueError):
            library.import_files([track['filepath']])
        own = library.import_uploaded_files([self.upload()])[0]
        self.assertNotEqual(own['filepath'], track['filepath'])
        select_user('alice')
        self.assertTrue(library.load_library()[0]['favorite'])
        self.assertEqual(playlist.load_playlists()[0]['track_ids'], [track['id']])

    def test_concurrent_users_have_distinct_contexts(self):
        def worker(name):
            token = select_user(name)
            try:
                playlist.create_playlist(name)
                return [item['name'] for item in playlist.load_playlists()]
            finally:
                reset_user(token)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, ['alice', 'bob']))
        self.assertEqual(results, [['alice'], ['bob']])

    def test_filter_combination_legacy_format_and_sort(self):
        tracks = [
            dict(id='1', title='Água', artist='Banda', album='Disco', filepath='one.FLAC', favorite=True, duration=2),
            dict(id='2', title='B', artist='Artista Desconhecido', album='', filepath='two.wav', duration=10),
        ]
        self.assertTrue(missing_metadata(tracks[1]))
        self.assertFalse(missing_metadata(tracks[0]))
        self.assertEqual(filter_library(tracks, 'agua', ['flac'], ['Banda'], ['Disco'], True), [tracks[0]])
        self.assertEqual(filter_library(tracks, incomplete=True), [tracks[1]])
        self.assertEqual(filter_library(tracks, sort='duration', descending=True), list(reversed(tracks)))


if __name__ == '__main__':
    unittest.main()
