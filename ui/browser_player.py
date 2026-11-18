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
            "entry_id": track["_queue_id"], "duration": track.get("duration", 0),
            "src": f"data:{audio_mime_type(path)};base64,{base64.b64encode(content).decode()}",
        })
    track = player.get_current_track()
    event = _component(
        queue=queue, selected=track["_queue_id"] if track else None,
        queue_version=player.queue_version,
        command=player.command_version, playing=player.is_playing and not player.is_paused,
        position=player._paused_at_pos, volume=player.volume,
        repeat=player.repeat_mode, key="browser_transport", default=None,
    )
    if event and event.get("sequence") != st.session_state.get("audio_event_sequence"):
        st.session_state.audio_event_sequence = event.get("sequence")
        if player.apply_browser_feedback(event):
            st.rerun()
