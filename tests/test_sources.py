import unittest

from core.sources import (
    PLATFORM_HOSTS, is_local_track, normalize_external_url, platform_for_url,
)


class SourceTests(unittest.TestCase):
    def test_all_known_hosts(self):
        for host, platform in PLATFORM_HOSTS.items():
            with self.subTest(host=host):
                self.assertEqual(platform_for_url(f"https://{host}/track/123"), platform)

    def test_generic_and_deceptive_hosts(self):
        for url in (
            "https://example.org/music",
            "https://open.spotify.com.example.org/track",
            "https://example.org/open.spotify.com",
        ):
            self.assertEqual(platform_for_url(url), "Link externo")

    def test_normalization(self):
        self.assertEqual(
            normalize_external_url(" HTTPS://OPEN.SPOTIFY.COM:443/track/ABC?si=1#player "),
            "https://open.spotify.com/track/ABC?si=1",
        )
        self.assertEqual(normalize_external_url("https://example.org:8443/a"),
                         "https://example.org:8443/a")
        self.assertEqual(normalize_external_url("https://[::1]:443/a"), "https://[::1]/a")
        self.assertEqual(normalize_external_url("https://música.example/a"),
                         "https://xn--msica-7ua.example/a")

    def test_invalid_urls(self):
        for url in (
            "", "javascript:alert(1)", "data:text/plain,a", "file:///song.mp3",
            "http://example.org/a", "/relative", "https:///track", "https://",
            "https://user:secret@example.org/a", "https://@example.org/a",
            "https://example.org/a b", "https://example.org/\nfoo",
            "\thttps://example.org", "https://bad_host.example/a",
            "https://example.org:99999/a", "https://example.org:abc",
            "https://example.org:", "https://example.org:0/a",
            "https://example.org\\@evil.org/a", "https://[invalid]/a",
            "https://[::1]example.org/a",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_external_url(url)

    def test_legacy_origin(self):
        self.assertTrue(is_local_track({"id": "legacy"}))
        self.assertTrue(is_local_track({"source_type": "local"}))
        self.assertFalse(is_local_track({"source_type": "external"}))
        self.assertFalse(is_local_track({"source_type": "unknown"}))
