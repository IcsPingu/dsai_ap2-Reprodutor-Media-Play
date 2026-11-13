"""Pure library queries; no Streamlit/session dependency."""

import os
import unicodedata


def normalized(value):
    value = unicodedata.normalize("NFKD", str(value))
    return "".join(c for c in value if not unicodedata.combining(c)).casefold().strip()


def track_format(track):
    return track.get("format") or os.path.splitext(track.get("filepath", ""))[1][1:].lower()


def missing_metadata(track):
    return any(not normalized(track.get(field, "")) or "desconhecido" in normalized(track.get(field, "")) for field in ("artist", "album"))


def filter_library(tracks, query="", formats=(), artists=(), albums=(), favorites=False, incomplete=False, sort="title", descending=False):
    if sort not in ("title", "artist", "album", "duration", "format"):
        raise ValueError("Ordenação inválida")
    result = []
    search = normalized(query)
    for track in tracks:
        if search and not any(search in normalized(track.get(field, "")) for field in ("title", "artist", "album")):
            continue
        if formats and track_format(track) not in formats:
            continue
        if artists and track.get("artist") not in artists:
            continue
        if albums and track.get("album") not in albums:
            continue
        if favorites and not track.get("favorite", False):
            continue
        if incomplete and not missing_metadata(track):
            continue
        result.append(track)
    def order(track):
        if sort == "duration":
            return float(track.get("duration", 0)), normalized(track.get("title", ""))
        value = track_format(track) if sort == "format" else track.get(sort, "")
        return normalized(value), normalized(track.get("title", ""))
    return sorted(result, key=order, reverse=descending)
