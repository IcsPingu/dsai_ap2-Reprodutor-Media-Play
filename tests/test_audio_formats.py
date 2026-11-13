import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import soundfile as sf
from mutagen.flac import Picture
from PIL import Image
from core import library
from core.audio_formats import read_audio, write_audio_tags, audio_mime_type


class AudioImportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.patches = []
        for name, value in {
            'STORAGE_DIR': str(self.root / 'storage'),
            'MEDIA_DIR': str(self.root / 'storage/media'),
            'COVERS_DIR': str(self.root / 'storage/covers'),
            'LIBRARY_JSON': str(self.root / 'storage/library.json'),
            'DEFAULT_COVER': str(self.root / 'storage/covers/default.png'),
        }.items():
            item = patch.object(library, name, value)
            item.start()
            self.patches.append(item)

    def tearDown(self):
        for item in self.patches:
            item.stop()
        self.directory.cleanup()

    def audio(self, extension):
        path = self.root / ('sample.' + extension)
        sf.write(path, [0.0] * 8000, 8000, format=extension.upper())
        return path

    def test_formats_metadata_roundtrip_and_duration(self):
        for extension in ('wav', 'flac', 'mp3'):
            with self.subTest(extension=extension):
                path = self.audio(extension)
                values = dict(title='Faixa', artist='Artista', album='Album', year='2026', genre='Teste')
                write_audio_tags(path, values)
                track = library.parse_audio_metadata(str(path))
                for key, value in values.items():
                    self.assertEqual(track[key], value)
                self.assertEqual(track['duration'], 1)
                self.assertEqual(track['mime_type'], audio_mime_type(path))
                self.assertEqual(track['id'], library.parse_mp3_metadata(str(path))['id'])

    def test_flac_cover(self):
        path = self.audio('flac')
        picture = Picture()
        picture.type = 3
        picture.mime = 'image/png'
        buffer = io.BytesIO()
        Image.new('RGB', (8, 8), 'red').save(buffer, format='PNG')
        picture.data = buffer.getvalue()
        audio = read_audio(path)
        audio.add_picture(picture)
        audio.save()
        track = library.parse_audio_metadata(str(path))
        self.assertTrue(Path(track['cover_path']).is_file())

    def test_scan_nested_uppercase_and_duplicate(self):
        path = self.audio('wav')
        folder = self.root / 'nested'
        folder.mkdir()
        path.rename(folder / 'SAMPLE.WAV')
        self.audio('flac')
        self.audio('mp3')
        (folder / 'ignore.txt').write_text('text')
        self.assertEqual(len(library.scan_directory(str(self.root))), 3)
        self.assertEqual(len(library.scan_directory(str(self.root))), 3)

    def test_reject_corrupt_and_disguised_audio(self):
        bad = self.root / 'bad.wav'
        bad.write_bytes(b'not audio')
        with self.assertRaises(ValueError):
            library.import_files([str(bad)])
        path = self.audio('wav')
        disguised = self.root / 'wrong.flac'
        disguised.write_bytes(path.read_bytes())
        with self.assertRaises(ValueError):
            read_audio(disguised)

    def test_upload_safe_name_and_idempotency(self):
        path = self.audio('wav')
        upload = io.BytesIO(path.read_bytes())
        upload.name = '../sample.wav'
        tracks = library.import_uploaded_files([upload])
        self.assertEqual(len(tracks), 1)
        self.assertEqual(Path(tracks[0]['filepath']).parent, Path(library.MEDIA_DIR))
        self.assertEqual(len(library.import_uploaded_files([upload])), 1)

    def test_local_decoder_loads_all_formats(self):
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        import pygame
        pygame.mixer.init()
        try:
            for extension in ('wav', 'flac', 'mp3'):
                with self.subTest(extension=extension):
                    pygame.mixer.music.load(str(self.audio(extension)))
                    pygame.mixer.music.play()
                    self.assertTrue(pygame.mixer.music.get_busy())
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
        finally:
            pygame.mixer.quit()

    def test_update_metadata_preserves_audio(self):
        for extension in ('wav', 'flac', 'mp3'):
            path = self.audio(extension)
            tracks = library.import_files([str(path)])
            track = next(t for t in tracks if t['filepath'] == str(path))
            self.assertTrue(library.update_track_metadata(track['id'], {'artist': 'Novo'}))
            self.assertEqual(library.parse_audio_metadata(str(path))['artist'], 'Novo')
            self.assertEqual(library.parse_audio_metadata(str(path))['duration'], 1)


if __name__ == '__main__':
    unittest.main()
