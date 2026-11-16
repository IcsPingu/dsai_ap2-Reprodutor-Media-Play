import copy
import os
import tempfile
import unittest
from unittest.mock import patch

from core.smart_playlists import evaluate, validate_definition
from core.playlist import (
    create_playlist, create_smart_playlist, update_smart_playlist,
    resolve_playlist_tracks, load_playlists, delete_playlist,
    add_track_to_playlist, remove_track_from_playlist, reorder_playlist_tracks,
)
from core.user_storage import select_user, reset_user


def rule(field, value, operator="equals"):
    return {"field": field, "operator": operator, "value": value}


def definition(*rules, **options):
    return {"rules": list(rules), **options}


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.library = [
            dict(id="a", title="Água", artist="Banda", album="Primeiro", genre="Rock", duration=120, filepath="a.FLAC", favorite=True),
            dict(id="b", title="Brisa", artist="Outra", album="Segundo", genre="Jazz", duration=300, format="mp3", favorite=False),
            dict(id="c", title="Céu", artist="Banda", album="Album Desconhecido", genre="Rock", duration=400, format="wav"),
        ]

    def ids(self, spec, library=None):
        return [t["id"] for t in evaluate(spec, self.library if library is None else library)]

    def test_all_combines_favorites_format_and_duration(self):
        spec = definition(rule("favorite", True), rule("format", "flac"), rule("duration", 120, "lte"))
        self.assertEqual(self.ids(spec), ["a"])

    def test_any_combines_alternative_matches(self):
        spec = definition(rule("artist", "Outra"), rule("format", "wav"), match="any")
        self.assertEqual(self.ids(spec), ["b", "c"])

    def test_text_ignores_accents_and_case(self):
        self.assertEqual(self.ids(definition(rule("title", "AGUA"))), ["a"])
        self.assertEqual(self.ids(definition(rule("title", "CE", "contains"))), ["c"])
        self.assertEqual(self.ids(definition(rule("genre", "rock"))), ["a", "c"])
        self.assertEqual(self.ids(definition(rule("album", "seg", "contains"))), ["b"])

    def test_negative_text_and_format(self):
        self.assertEqual(self.ids(definition(rule("artist", "banda", "not_contains"))), ["b"])
        self.assertEqual(self.ids(definition(rule("format", "mp3", "not_equals"))), ["a", "c"])

    def test_boolean_false_and_missing_metadata(self):
        self.assertEqual(self.ids(definition(rule("favorite", False))), ["b", "c"])
        self.assertEqual(self.ids(definition(rule("missing_metadata", True))), ["c"])

    def test_duration_range_includes_boundaries(self):
        spec = definition(rule("duration", 120, "gte"), rule("duration", 300, "lte"))
        self.assertEqual(self.ids(spec), ["a", "b"])

    def test_numeric_sort_and_limit_after_matching(self):
        spec = definition(rule("genre", "rock"), sort="duration", descending=True, limit=1)
        self.assertEqual(self.ids(spec), ["c"])

    def test_supported_sort_fields(self):
        for sort in ("title", "artist", "album", "duration", "format"):
            with self.subTest(sort=sort):
                result = self.ids(definition(rule("duration", 0, "gte"), sort=sort))
                self.assertEqual(set(result), {"a", "b", "c"})

    def test_empty_library_and_no_match(self):
        self.assertEqual(self.ids(definition(rule("favorite", True)), []), [])
        self.assertEqual(self.ids(definition(rule("artist", "ausente"))), [])

    def test_duplicate_ids_and_input_not_modified(self):
        original = copy.deepcopy(self.library)
        result = self.ids(definition(rule("duration", 0, "gte")), self.library + [self.library[0]])
        self.assertEqual(result, ["a", "b", "c"])
        self.assertEqual(self.library, original)

    def test_invalid_duration_in_track_does_not_match(self):
        for value in (None, "bad", float("nan"), float("inf"), -1):
            track = dict(id="bad", duration=value)
            self.assertEqual(self.ids(definition(rule("duration", 0, "gte")), [track]), [])

    def test_invalid_definitions_rejected(self):
        invalid = [
            None, {}, definition(), definition(*[rule("favorite", True)] * 21),
            definition(rule("unknown", "x")), definition(rule("artist", "")),
            definition(rule("artist", "x", "execute")),
            definition(rule("format", "aac")), definition(rule("favorite", "true")),
            definition(rule("duration", True, "gte")),
            definition(rule("duration", float("nan"), "lte")),
            definition(rule("duration", -1, "lte")),
            definition(rule("favorite", True), match="bad"),
            definition(rule("favorite", True), limit=-1),
            definition(rule("favorite", True), limit=True),
            definition(rule("favorite", True), sort="invalid"),
            definition(rule("favorite", True), descending="yes"),
        ]
        for spec in invalid:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                validate_definition(spec)


class SmartPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, MEDIA_PLAY_DATA=self.temp.name)
        self.environment.start()
        self.token = select_user("alice")
        self.spec = definition(rule("favorite", True))

    def tearDown(self):
        reset_user(self.token)
        self.environment.stop()
        self.temp.cleanup()

    def test_create_reload_edit_and_delete(self):
        created = create_smart_playlist("Favoritas", self.spec)
        self.assertEqual(load_playlists()[0]["definition"]["rules"], self.spec["rules"])
        updated = definition(rule("format", "flac"))
        self.assertTrue(update_smart_playlist(created["id"], "FLAC", updated))
        self.assertEqual(load_playlists()[0]["name"], "FLAC")
        self.assertTrue(delete_playlist(created["id"]))
        self.assertEqual(load_playlists(), [])

    def test_selection_updates_with_current_library(self):
        playlist = create_smart_playlist("Favoritas", self.spec)
        library = [dict(id="a", favorite=True), dict(id="b", favorite=False)]
        self.assertEqual(len(resolve_playlist_tracks(playlist, library)), 1)
        library[1]["favorite"] = True
        library.append(dict(id="c", favorite=True))
        self.assertEqual(len(resolve_playlist_tracks(playlist, library)), 3)
        self.assertEqual(playlist["track_ids"], [])

    def test_manual_playlists_are_compatible(self):
        manual = create_playlist("Manual")
        add_track_to_playlist(manual["id"], "a")
        playlist = load_playlists()[0]
        self.assertEqual(resolve_playlist_tracks(playlist, [dict(id="a")]), [dict(id="a")])
        self.assertFalse(update_smart_playlist(manual["id"], "Smart", self.spec))

    def test_smart_playlists_reject_manual_membership_operations(self):
        playlist = create_smart_playlist("Smart", self.spec)
        for function, argument in ((add_track_to_playlist, "a"), (remove_track_from_playlist, "a"), (reorder_playlist_tracks, ["a"])):
            with self.subTest(function=function.__name__), self.assertRaises(ValueError):
                function(playlist["id"], argument)

    def test_other_user_cannot_read_edit_or_delete(self):
        playlist = create_smart_playlist("Alice", self.spec)
        select_user("bob")
        self.assertEqual(load_playlists(), [])
        self.assertFalse(update_smart_playlist(playlist["id"], "Bob", self.spec))
        self.assertFalse(delete_playlist(playlist["id"]))
        select_user("alice")
        self.assertEqual(load_playlists()[0]["name"], "Alice")

    def test_invalid_changes_do_not_overwrite_saved_rules(self):
        playlist = create_smart_playlist("Original", self.spec)
        with self.assertRaises(ValueError):
            update_smart_playlist(playlist["id"], "Original", {"rules": []})
        self.assertEqual(load_playlists()[0], playlist)
        for name in ("", " " * 4, "x" * 101):
            with self.assertRaises(ValueError):
                create_smart_playlist(name, self.spec)


if __name__ == "__main__":
    unittest.main()
