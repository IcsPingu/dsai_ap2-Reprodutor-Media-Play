"""Browser owns timing, transport and queue completion; Python supplies media."""

import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from core.audio_formats import audio_mime_type
from core.library import resolve_filepath
from core.sources import is_local_track
from core.user_storage import user_directory, select_user
from core.listening_history import history_state, record_confirmation

_component = components.declare_component("media_play_browser", path=str(Path(__file__).parent / "browser_player"))


@st.fragment
def render_browser_player(player):
    # A fragment rerun does not execute app.py's authentication/context setup.
    select_user(st.session_state.get("identity"))
    generation = None
    if user_directory() is not None:
        try:
            generation = history_state()["generation"]
        except ValueError as error:
            st.error(str(error))
    queue = []
    for track in player.queue:
        if not is_local_track(track):
            continue
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
        action=getattr(player, "last_action", None),
        history_generation=generation,
        history_acknowledgements=st.session_state.get("history_acknowledgements", []),
        position=player._paused_at_pos, volume=player.volume,
        repeat=player.repeat_mode, key="browser_transport", default=None,
    )
    if event and event.get("sequence") != st.session_state.get("audio_event_sequence"):
        st.session_state.audio_event_sequence = event.get("sequence")
        acknowledgements = st.session_state.get("history_acknowledgements", [])
        changed = False
        confirmations = event.get("history", [])
        if generation and isinstance(confirmations, list):
            for confirmation in confirmations[:50]:
                if not isinstance(confirmation, dict) or not isinstance(confirmation.get("attempt_id"), str):
                    continue
                try:
                    record_confirmation(confirmation)
                except ValueError as error:
                    st.error(str(error))
                    break
                identity = confirmation["attempt_id"]
                if identity not in acknowledgements:
                    acknowledgements = (acknowledgements + [identity])[-100:]
                    changed = True
            st.session_state.history_acknowledgements = acknowledgements
        applied = player.apply_browser_feedback(event)
        if event.get("kind") == "history":
            # Background confirmations must not close editors elsewhere in the app.
            if changed and st.session_state.get("navigation_menu") == "📊 Histórico":
                st.rerun()
        elif applied or changed:
            st.rerun()
