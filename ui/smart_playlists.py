"""Streamlit rule editor and live results for smart playlists."""

import streamlit as st
from core.library import load_library
from core.playlist import (
    create_smart_playlist, update_smart_playlist, delete_playlist,
    load_playlists, resolve_playlist_tracks,
)
from core.smart_playlists import evaluate

FIELDS = {
    "Título": "title", "Artista": "artist", "Álbum": "album",
    "Gênero": "genre", "Formato": "format", "Duração": "duration",
    "Favorita": "favorite", "Metadados incompletos": "missing_metadata",
}
SORTS = {"Título": "title", "Artista": "artist", "Álbum": "album", "Duração": "duration", "Formato": "format"}


def selected_label(mapping, value):
    return next((label for label, code in mapping.items() if code == value), next(iter(mapping)))


def rule_editor(prefix, index, initial):
    st.markdown(f"**Regra {index + 1}**")
    base = f"{prefix}_rule_{index}"
    options = list(FIELDS)
    label = st.selectbox(
        "Campo", options,
        index=options.index(selected_label(FIELDS, initial.get("field", "favorite"))),
        key=f"{base}_field",
    )
    field = FIELDS[label]
    key = f"{base}_{field}"
    original = initial if initial.get("field") == field else {}
    if field in ("favorite", "missing_metadata"):
        value = st.selectbox("Valor", ["Sim", "Não"], index=0 if original.get("value", True) else 1, key=f"{key}_value")
        return {"field": field, "operator": "equals", "value": value == "Sim"}
    if field == "duration":
        operators = {"No mínimo": "gte", "No máximo": "lte"}
        default = float(original.get("value", 300))
        value = st.number_input("Duração em segundos", min_value=0.0, value=default, step=1.0, key=f"{key}_value")
    elif field == "format":
        operators = {"É igual a": "equals", "É diferente de": "not_equals"}
        formats = ["mp3", "wav", "flac"]
        value = st.selectbox("Formato da regra", formats, index=formats.index(original.get("value", "mp3")), key=f"{key}_value")
    else:
        operators = {"Contém": "contains", "É igual a": "equals", "Não contém": "not_contains"}
        value = st.text_input("Texto da regra", value=original.get("value", ""), max_chars=200, key=f"{key}_value")
    labels = list(operators)
    operator = st.selectbox(
        "Comparação", labels,
        index=labels.index(selected_label(operators, original.get("operator"))),
        key=f"{key}_operator",
    )
    return {"field": field, "operator": operators[operator], "value": value}


def definition_editor(prefix, initial=None):
    initial = initial or {"rules": [{"field": "favorite", "operator": "equals", "value": True}]}
    rules = initial["rules"]
    count = st.number_input("Quantidade de regras", min_value=1, max_value=20, value=len(rules), step=1, key=f"{prefix}_count")
    st.caption("Textos ignoram maiúsculas e acentos. Duração é medida em segundos.")
    result = []
    for index in range(int(count)):
        default = rules[index] if index < len(rules) else {"field": "favorite", "operator": "equals", "value": True}
        result.append(rule_editor(prefix, index, default))
    match = st.selectbox("Combinar regras", ["Todas (E)", "Qualquer uma (OU)"], index=1 if initial.get("match") == "any" else 0, key=f"{prefix}_match")
    labels = list(SORTS)
    sort = st.selectbox("Ordenar resultados por", labels, index=labels.index(selected_label(SORTS, initial.get("sort", "title"))), key=f"{prefix}_sort")
    descending = st.checkbox("Resultados em ordem decrescente", value=initial.get("descending", False), key=f"{prefix}_descending")
    limit = st.number_input("Máximo de faixas (0 = sem limite)", min_value=0, max_value=10000, value=initial.get("limit", 0), step=1, key=f"{prefix}_limit")
    return {"rules": result, "match": "all" if match.startswith("Todas") else "any", "sort": SORTS[sort], "descending": descending, "limit": int(limit)}


def show_tracks(tracks):
    st.caption(f"{len(tracks)} faixa(s) correspondem às regras.")
    if not tracks:
        st.info("Nenhuma faixa corresponde. Importe músicas ou ajuste as regras.")
        return
    st.dataframe(
        [{"Título": t.get("title", ""), "Artista": t.get("artist", ""), "Álbum": t.get("album", ""), "Duração": t.get("duration_str", "")} for t in tracks],
        hide_index=True, use_container_width=True,
    )


def render_smart_playlists(player):
    st.subheader("Playlists inteligentes")
    st.caption("Salve regras para selecionar músicas automaticamente. Novas faixas compatíveis entram na próxima consulta; a fila já tocando permanece como foi iniciada.")
    library = load_library()
    with st.expander("Criar playlist inteligente"):
        name = st.text_input("Nome da playlist inteligente", max_chars=100, key="smart_new_name")
        definition = definition_editor("smart_new")
        if st.button("Pré-visualizar seleção", key="smart_new_preview"):
            try:
                show_tracks(evaluate(definition, library))
            except ValueError as error:
                st.error(str(error))
        if st.button("Salvar playlist inteligente", key="smart_new_save"):
            try:
                create_smart_playlist(name, definition)
                st.session_state.playlists = load_playlists()
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    playlists = [p for p in load_playlists() if p.get("type") == "smart"]
    if not playlists:
        st.info("Você ainda não criou playlists inteligentes.")
        return
    lookup = {p["id"]: p for p in playlists}
    identity = st.selectbox("Playlist inteligente", list(lookup), format_func=lambda value: lookup[value]["name"], key="smart_selected")
    playlist = lookup[identity]
    try:
        tracks = resolve_playlist_tracks(playlist, library)
    except ValueError as error:
        st.error(f"Regras inválidas: {error}. Edite a playlist para corrigir.")
        tracks = []
    show_tracks(tracks)
    if st.button("Reproduzir seleção inteligente", disabled=not tracks):
        player.set_queue(tracks)
        player.play(tracks[0])
        st.rerun()
    with st.expander("Editar regras e nome"):
        name = st.text_input("Nome", value=playlist["name"], max_chars=100, key=f"smart_edit_{identity}_name")
        definition = definition_editor(f"smart_edit_{identity}", playlist["definition"])
        if st.button("Salvar alterações da inteligente", key=f"smart_edit_{identity}_save"):
            try:
                update_smart_playlist(identity, name, definition)
                st.session_state.playlists = load_playlists()
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    if st.button("Excluir playlist inteligente", key=f"smart_delete_{identity}"):
        delete_playlist(identity)
        st.session_state.playlists = load_playlists()
        st.rerun()
