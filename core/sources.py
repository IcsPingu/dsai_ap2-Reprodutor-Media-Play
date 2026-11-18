"""Identificação de origens e validação de links, sem acesso à rede."""

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


PLATFORM_HOSTS = {
    "open.spotify.com": "Spotify",
    "youtube.com": "YouTube",
    "www.youtube.com": "YouTube",
    "m.youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "music.youtube.com": "YouTube Music",
    "music.apple.com": "Apple Music",
    "deezer.com": "Deezer",
    "www.deezer.com": "Deezer",
    "soundcloud.com": "SoundCloud",
    "www.soundcloud.com": "SoundCloud",
    "tidal.com": "Tidal",
    "www.tidal.com": "Tidal",
    "listen.tidal.com": "Tidal",
    "music.amazon.com": "Amazon Music",
    "music.amazon.com.br": "Amazon Music",
    "music.amazon.co.uk": "Amazon Music",
}
PLATFORMS = tuple(dict.fromkeys(("Local", *PLATFORM_HOSTS.values(), "Link externo")))
SOURCE_LABELS = {"Local": "local", "Link externo": "external"}


def normalize_external_url(value: str) -> str:
    """Retorna URL HTTPS canônica ou lança ValueError com mensagem para a UI."""
    message = "Informe uma URL HTTPS válida, sem credenciais, espaços internos ou controles."
    if not isinstance(value, str):
        raise ValueError(message)
    # urlsplit remove alguns controles silenciosamente: rejeitar antes do parsing.
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(message)
    value = value.strip()
    if not value or "\\" in value or any(char.isspace() for char in value):
        raise ValueError(message)
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() != "https" or not parts.netloc or not parts.hostname:
            raise ValueError(message)
        if parts.username is not None or parts.password is not None:
            raise ValueError(message)
        if parts.netloc.startswith("["):
            suffix = parts.netloc.split("]", 1)[1]
            if suffix and not re.fullmatch(r":\d+", suffix):
                raise ValueError(message)
        elif "[" in parts.netloc or "]" in parts.netloc:
            raise ValueError(message)
        host = parts.hostname.encode("idna").decode("ascii").lower()
        try:
            address = ipaddress.ip_address(host)
            host = address.compressed
            netloc = f"[{host}]" if address.version == 6 else host
        except ValueError:
            labels = host.split(".")
            if len(host) > 253 or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                for label in labels
            ):
                raise ValueError(message)
            netloc = host
        port = parts.port
        if parts.netloc.endswith(":") or port == 0:
            raise ValueError(message)
        if port is not None and port != 443:
            netloc += f":{port}"
        return urlunsplit(("https", netloc, parts.path, parts.query, ""))
    except (ValueError, UnicodeError) as error:
        raise ValueError(message) from error


def platform_for_url(value: str) -> str:
    url = normalize_external_url(value)
    return PLATFORM_HOSTS.get(urlsplit(url).hostname, "Link externo")


def is_local_track(track) -> bool:
    """Registros legados sem origem continuam locais; origens desconhecidas não."""
    return track.get("source_type", "local") == "local"


def local_tracks(tracks):
    return [track for track in tracks if is_local_track(track)]


def track_platform(track):
    """Derivar do link validado em vez de confiar em rótulos persistidos."""
    if is_local_track(track):
        return "Local"
    try:
        return platform_for_url(track.get("external_url", ""))
    except ValueError:
        return "Link externo"
