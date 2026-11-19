"""History browsing and statistics without changing the active queue implicitly."""

from datetime import datetime
import streamlit as st
from core.library import load_library
from core.listening_history import (
    LOCAL_ZONE, available_track, clear_history, filter_history,
    history_state, history_statistics,
)


def render_listening_history(player):
    st.subheader("Histórico e estatísticas")
    st.caption("Uma reprodução conta após 5 segundos efetivos, ou metade de uma faixa mais curta. Pausas e saltos de posição não contam como tempo ouvido.")
    st.caption("Horários de São Paulo. Dados temporários neste deploy; abrir links externos não registra reprodução.")
    try:
        state = history_state()
    except ValueError as error:
        st.error(str(error))
        return
    periods = {"Hoje": "today", "Últimos 7 dias": "week", "Todo o histórico": "all"}
    period = st.selectbox("Período do histórico", list(periods), index=2)
    events = filter_history(state["events"], periods[period])
    stats = history_statistics(events)
    first, second = st.columns(2)
    first.metric("Reproduções confirmadas", stats["plays"])
    second.metric("Músicas diferentes", stats["unique_tracks"])
    st.markdown("#### Mais ouvidas no período")
    if stats["ranking"]:
        st.dataframe([
            {"Música": row["title"], "Artista": row["artist"], "Reproduções": row["plays"]}
            for row in stats["ranking"]
        ], hide_index=True, use_container_width=True)
    else:
        st.info("Nenhuma reprodução confirmada neste período.")
    library = load_library()
    st.markdown("#### Ouvidas recentemente")
    pages = max(1, (len(events) + 19) // 20)
    page = st.selectbox("Página do histórico", list(range(1, pages + 1)))
    for event in events[(page - 1) * 20:page * 20]:
        timestamp = datetime.fromisoformat(event["played_at"]).astimezone(LOCAL_ZONE)
        with st.container(border=True):
            st.text(f"{event.get('title', '')} — {event.get('artist', '')}")
            st.caption(timestamp.strftime("%d/%m/%Y %H:%M:%S"))
            track = available_track(event, library)
            if track is None:
                st.caption("Arquivo indisponível na biblioteca atual.")
            first, second = st.columns(2)
            with first:
                if st.button("Tocar novamente", key=f"history_play_{event['attempt_id']}", disabled=track is None):
                    if player.play(track):
                        st.rerun()
                    else:
                        st.error("Não foi possível abrir o arquivo.")
            with second:
                if st.button("Adicionar ao final da fila", key=f"history_enqueue_{event['attempt_id']}", disabled=track is None):
                    player.enqueue(track)
                    st.toast("Música adicionada ao final da fila.")
                    st.rerun()
    with st.expander("Limpar meu histórico"):
        st.caption("Remove todo o histórico desta conta, inclusive registros fora do período selecionado. Biblioteca, playlists e áudio atual são preservados.")
        confirm = st.checkbox("Confirmo a limpeza de todo o meu histórico", key=f"history_clear_confirm_{state['generation']}")
        if st.button("Limpar histórico", disabled=not confirm or not state["events"]):
            clear_history()
            st.toast("Histórico da conta limpo.")
            st.rerun()
