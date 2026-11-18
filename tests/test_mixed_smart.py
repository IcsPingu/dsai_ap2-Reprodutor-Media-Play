from core import library, playlist
from core.library_filters import filter_library, track_format
from core.smart_playlists import evaluate, validate_definition
from core.sources import track_platform
from storage_case import StorageCase


class MixedSmartTests(StorageCase):
    def setUp(self):
        super().setUp()
        self.links = self.add_links()
        self.local = dict(id="local", title="Local", artist="Artist", album="Album",
                          filepath="old.FLAC", duration=120)
        library.save_library([self.local] + self.links)

    def rule(self, field, value, operator="equals"):
        return {"rules": [{"field": field, "operator": operator, "value": value}]}

    def test_source_platform_filters_compose_with_existing_filters(self):
        tracks = library.load_library()
        self.assertEqual(filter_library(tracks, sources=["external"], platforms=["Spotify"]),
                         [tracks[1]])
        self.assertEqual(filter_library(tracks, sources=["local"], formats=["flac"]),
                         [tracks[0]])
        self.assertEqual(filter_library(tracks, sources=["external"], formats=["flac"]), [])
        self.assertEqual(track_format(dict(self.links[0], format="mp3", filepath="fake.mp3")), "")
        self.assertEqual(track_platform(dict(self.links[0], platform="Forged")), "Spotify")

    def test_dynamic_platform_playlist_and_source_negation(self):
        created = playlist.create_smart_playlist("Spotify", self.rule("platform", "Spotify"))
        self.assertEqual([t["id"] for t in playlist.resolve_playlist_tracks(
            created, library.load_library())], [self.links[0]["id"]])
        library.add_external_track("https://open.spotify.com/track/new", "New Spotify")
        self.assertEqual(len(playlist.resolve_playlist_tracks(created, library.load_library())), 2)
        selected = evaluate(self.rule("source_type", "external", "not_equals"),
                            library.load_library())
        self.assertEqual([t["id"] for t in selected], ["local"])

    def test_unknown_external_duration_never_matches_numeric_rule(self):
        for operator, duration in (("gte", 0), ("lte", 99999)):
            result = evaluate(self.rule("duration", duration, operator), library.load_library())
            self.assertEqual([track["id"] for track in result], ["local"])

    def test_invalid_source_definitions_do_not_overwrite(self):
        created = playlist.create_smart_playlist("Valid", self.rule("source_type", "external"))
        for field, value in (("source_type", "unknown"), ("platform", "Forged"),
                             ("platform", 123)):
            with self.assertRaises(ValueError):
                playlist.update_smart_playlist(created["id"], "Invalid", self.rule(field, value))
        self.assertEqual(playlist.load_playlists()[0], created)
        with self.assertRaises(ValueError):
            validate_definition(self.rule("source_type", "external", "contains"))
