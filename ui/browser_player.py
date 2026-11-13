"""Browser owns timing, transport and queue completion; Python supplies media."""

import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from core.audio_formats import audio_mime_type
from core.library import resolve_filepath

_component = components.declare_component("media_play_browser", path=str(Path(__file__).parent / "browser_player"))


def render_browser_player(player):
    queue = []
    for track in player.queue:
        path = resolve_filepath(track.get("filepath", ""))
        if not path or not Path(path).is_file():
            st.warning(f"Arquivo indisponível: {track.get('title', '')}")
            continue
        content = Path(path).read_bytes()
        queue.append({
            "id": track["id"], "title": track.get("title", ""),
            "src": f"data:{audio_mime_type(path)};base64,{base64.b64encode(content).decode()}",
        })
    track = player.get_current_track()
    event = _component(
        queue=queue, selected=track["id"] if track else None,
        command=player.command_version, playing=player.is_playing and not player.is_paused,
        position=player._paused_at_pos, volume=player.volume,
        repeat=player.repeat_mode, key="browser_transport", default=None,
    )
    if event and event.get("sequence") != st.session_state.get("audio_event_sequence"):
        st.session_state.audio_event_sequence = event.get("sequence")
        # Ignore feedback for a superseded Python command.
        if event.get("command") != player.command_version:
            return
        index = next((i for i, t in enumerate(player.queue) if t["id"] == event.get("id")), None)
        if index is not None:
            player.current_index = index
        player._paused_at_pos = max(0, float(event.get("position", 0)))
        player.is_playing = event.get("status") == "playing"
        player.is_paused = event.get("status") == "paused"
        if event.get("repeat") in ("off", "all", "one"):
            player.repeat_mode = event["repeat"]
        st.rerun()
