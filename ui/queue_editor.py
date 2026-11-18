"""Transport-independent edits to the upcoming section of the queue."""

import streamlit as st
from core.playback_queue import format_duration


def render_enqueue_actions(player, track):
    with st.popover("Adicionar à fila", use_container_width=True):
        st.caption("Adicionar mantém a música atual. Repetições são permitidas.")
        if st.button("Tocar depois", key=f"enqueue_next_{track['id']}"):
            player.enqueue(track, next_up=True)
            st.rerun()
        if st.button("Adicionar ao final", key=f"enqueue_end_{track['id']}"):
            player.enqueue(track)
            st.rerun()


def render_queue_editor(player):
    st.subheader("📋 Fila de Reprodução Atual")
    if not player.queue:
        st.info("A fila está vazia. Use Adicionar à fila na biblioteca.")
        return
    st.caption("A faixa atual e as anteriores ficam protegidas. Você pode editar as próximas sem interromper o áudio.")
    upcoming = len(player.queue) - player.current_index - 1
    st.caption(f"{upcoming} próxima(s) · duração estimada: {format_duration(player.upcoming_duration())}")
    if st.button("Limpar próximas", disabled=upcoming == 0, key="queue_clear_upcoming"):
        player.clear_upcoming()
        st.rerun()
    for index, track in enumerate(player.queue):
        active = index == player.current_index
        editable = index > player.current_index
        identity = track["_queue_id"]
        with st.container(border=True):
            state = "Atual" if active else "Anterior" if index < player.current_index else "Próxima"
            st.write(f"{index + 1}. {track.get('title', 'Sem título')} — {state}")
            st.caption(f"{track.get('artist', '')} · {track.get('duration_str', '00:00')}")
            if st.button("Tocar esta ocorrência", key=f"queue_play_{identity}"):
                player.play(track)
                st.rerun()
            first, second, third = st.columns(3)
            with first:
                if st.button("Subir", key=f"queue_up_{identity}", disabled=not editable or index <= player.current_index + 1):
                    player.move_queue_entry(index, index - 1)
                    st.rerun()
            with second:
                if st.button("Descer", key=f"queue_down_{identity}", disabled=not editable or index == len(player.queue) - 1):
                    player.move_queue_entry(index, index + 1)
                    st.rerun()
            with third:
                if st.button("Remover da fila", key=f"queue_remove_{identity}", disabled=not editable):
                    player.remove_queue_entry(index)
                    st.rerun()
