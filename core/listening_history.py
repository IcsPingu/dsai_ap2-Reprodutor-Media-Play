"""Per-account, idempotent playback confirmations and calendar-based summaries."""

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

from core.library import load_library
from core.playback_queue import duration_seconds
from core.sources import is_local_track
from core.user_storage import user_directory, serialized, atomic_json

LOCAL_ZONE = ZoneInfo("America/Sao_Paulo")
PERIODS = ("today", "week", "all")


def history_path():
    directory = user_directory()
    if directory is None:
        raise ValueError("Entre na sua conta para acessar o histórico.")
    return directory / "history.json"


def _new_state():
    return {"version": 1, "generation": uuid.uuid4().hex, "events": []}


@serialized
def history_state():
    path = history_path()
    if not path.exists():
        state = _new_state()
        atomic_json(path, state)
        return state
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("Não foi possível ler o histórico. O arquivo foi preservado.") from error
    if (not isinstance(state, dict) or state.get("version") != 1
            or not isinstance(state.get("generation"), str)
            or not isinstance(state.get("events"), list)):
        raise ValueError("Formato de histórico inválido. O arquivo foi preservado.")
    for event in state["events"]:
        if not isinstance(event, dict) or not all(isinstance(event.get(key), str) for key in ("attempt_id", "track_id", "played_at")):
            raise ValueError("Registro inválido no histórico. O arquivo foi preservado.")
        try:
            timestamp = datetime.fromisoformat(event["played_at"])
            if timestamp.tzinfo is None:
                raise ValueError("Timestamp sem fuso")
        except ValueError as error:
            raise ValueError("Data inválida no histórico. O arquivo foi preservado.") from error
    return state


def confirmation_threshold(track):
    duration = duration_seconds(track)
    return min(5.0, duration / 2) if duration > 0 else 5.0


@serialized
def record_confirmation(confirmation):
    """Return an acknowledgement outcome; never accept a browser-supplied timestamp."""
    if not isinstance(confirmation, dict):
        return "invalid"
    attempt = confirmation.get("attempt_id")
    try:
        uuid.UUID(attempt)
    except (ValueError, TypeError, AttributeError):
        return "invalid"
    heard = confirmation.get("listened_seconds")
    if isinstance(heard, bool) or not isinstance(heard, (int, float)) or not math.isfinite(heard):
        return "invalid"
    state = history_state()
    if confirmation.get("generation") != state["generation"]:
        return "stale"
    if any(event["attempt_id"] == attempt for event in state["events"]):
        return "duplicate"
    track = next((track for track in load_library() if track["id"] == confirmation.get("track_id")), None)
    if not track or not is_local_track(track) or heard < confirmation_threshold(track):
        return "invalid"
    state["events"].append({
        "attempt_id": attempt,
        "track_id": track["id"],
        "title": str(track.get("title", "Sem título")),
        "artist": str(track.get("artist", "Artista Desconhecido")),
        "album": str(track.get("album", "Album Desconhecido")),
        "played_at": datetime.now(timezone.utc).isoformat(),
    })
    atomic_json(history_path(), state)
    return "recorded"


@serialized
def clear_history():
    # Rotating generation also invalidates confirmations still queued in other tabs.
    state = _new_state()
    atomic_json(history_path(), state)
    return state["generation"]


def filter_history(events, period="all", now=None):
    if period not in PERIODS:
        raise ValueError("Período inválido.")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("A data de referência deve informar o fuso horário.")
    local_now = now.astimezone(LOCAL_ZONE)
    start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        start -= timedelta(days=6)
    result = []
    for event in events:
        timestamp = datetime.fromisoformat(event["played_at"])
        if timestamp > now:
            continue
        if period == "all" or timestamp >= start:
            result.append(dict(event))
    return sorted(result, key=lambda event: datetime.fromisoformat(event["played_at"]), reverse=True)


def history_statistics(events):
    ranked = {}
    for event in sorted(events, key=lambda event: datetime.fromisoformat(event["played_at"])):
        identity = event["track_id"]
        previous = ranked.get(identity, {})
        ranked[identity] = {
            "track_id": identity,
            "title": event.get("title", "Sem título"),
            "artist": event.get("artist", "Artista Desconhecido"),
            "plays": previous.get("plays", 0) + 1,
            "last_played": event["played_at"],
        }
    ranking = sorted(ranked.values(), key=lambda row: (-row["plays"], row["title"].casefold(), row["track_id"]))
    return {"plays": len(events), "unique_tracks": len(ranking), "ranking": ranking}


def available_track(event, library):
    from core.library import resolve_filepath
    track = next((track for track in library if track["id"] == event["track_id"] and is_local_track(track)), None)
    if track:
        path = resolve_filepath(track.get("filepath", ""))
        if path and Path(path).is_file():
            return track
    return None
