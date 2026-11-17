import os
import tempfile
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from core import library, playlist
from core.user_storage import select_user, reset_user


class StorageCase(unittest.TestCase):
    """Todos os testes usam storage descartável, nunca a coleção do usuário."""

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.dict(os.environ, MEDIA_PLAY_DATA=os.path.join(self.root, "private")))
        self.stack.callback(reset_user, select_user(None))
        covers = os.path.join(self.root, "covers")
        self.media = os.path.join(self.root, "media")
        values = {
            "STORAGE_DIR": self.root,
            "COVERS_DIR": covers,
            "MEDIA_DIR": self.media,
            "LIBRARY_JSON": os.path.join(self.root, "library.json"),
            "DEFAULT_COVER": os.path.join(covers, "default_cover.png"),
        }
        for name, value in values.items():
            self.stack.enter_context(patch.object(library, name, value))
        self.stack.enter_context(patch.object(playlist, "STORAGE_DIR", self.root))
        self.stack.enter_context(patch.object(
            playlist, "PLAYLISTS_JSON", os.path.join(self.root, "playlists.json")
        ))

    def add_links(self):
        library.add_external_track("https://open.spotify.com/track/123", "Spotify test")
        return library.add_external_track("https://example.org/music/456", "Generic test")
