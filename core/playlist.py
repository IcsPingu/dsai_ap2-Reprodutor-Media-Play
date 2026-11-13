from core.user_storage import atomic_json
from core.user_storage import scoped_path, serialized
import os
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional
from core.library import STORAGE_DIR

PLAYLISTS_JSON = os.path.join(STORAGE_DIR, "playlists.json")


def ensure_playlists_file():
    """Garante que a pasta storage e o arquivo playlists.json existam."""
    os.makedirs(scoped_path(STORAGE_DIR, ""), exist_ok=True)
    if not os.path.exists(scoped_path(PLAYLISTS_JSON, "playlists.json")):
        with open(scoped_path(PLAYLISTS_JSON, "playlists.json"), "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


@serialized
def load_playlists() -> List[Dict[str, Any]]:
    """Carrega as playlists do arquivo JSON local."""
    ensure_playlists_file()
    try:
        with open(scoped_path(PLAYLISTS_JSON, "playlists.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar {scoped_path(PLAYLISTS_JSON, "playlists.json")}: {e}")
        return []


@serialized
def save_playlists(playlists: List[Dict[str, Any]]):
    """Salva a lista de playlists no arquivo JSON local."""
    ensure_playlists_file()
    atomic_json(scoped_path(PLAYLISTS_JSON, "playlists.json"), playlists)


@serialized
def create_playlist(name: str) -> Dict[str, Any]:
    """Cria uma nova playlist personalizada."""
    playlists = load_playlists()
    playlist_id = str(uuid.uuid4())[:8]

    new_playlist = {
        "id": playlist_id,
        "name": name.strip() if name.strip() else "Nova Playlist",
        "track_ids": [],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    playlists.append(new_playlist)
    save_playlists(playlists)
    return new_playlist


@serialized
def delete_playlist(playlist_id: str) -> bool:
    """Exclui uma playlist pelo ID."""
    playlists = load_playlists()
    initial_count = len(playlists)
    playlists = [p for p in playlists if p["id"] != playlist_id]
    if len(playlists) < initial_count:
        save_playlists(playlists)
        return True
    return False


@serialized
def rename_playlist(playlist_id: str, new_name: str) -> bool:
    """Renomeia uma playlist existente."""
    playlists = load_playlists()
    updated = False
    for p in playlists:
        if p["id"] == playlist_id:
            p["name"] = new_name.strip()
            updated = True
            break
    if updated:
        save_playlists(playlists)
    return updated


@serialized
def add_track_to_playlist(playlist_id: str, track_id: str) -> bool:
    """Adiciona o ID de uma faixa ao final de uma playlist."""
    playlists = load_playlists()
    updated = False
    for p in playlists:
        if p["id"] == playlist_id:
            if track_id not in p["track_ids"]:
                p["track_ids"].append(track_id)
                updated = True
            break
    if updated:
        save_playlists(playlists)
    return updated


@serialized
def remove_track_from_playlist(playlist_id: str, track_id: str) -> bool:
    """Remove uma faixa de uma playlist específica."""
    playlists = load_playlists()
    updated = False
    for p in playlists:
        if p["id"] == playlist_id:
            if track_id in p["track_ids"]:
                p["track_ids"].remove(track_id)
                updated = True
            break
    if updated:
        save_playlists(playlists)
    return updated


@serialized
def reorder_playlist_tracks(playlist_id: str, new_track_ids: List[str]) -> bool:
    """Reordena a lista de IDs de faixas de uma playlist."""
    playlists = load_playlists()
    updated = False
    for p in playlists:
        if p["id"] == playlist_id:
            p["track_ids"] = new_track_ids
            updated = True
            break
    if updated:
        save_playlists(playlists)
    return updated


@serialized
def get_playlist_by_id(playlist_id: str) -> Optional[Dict[str, Any]]:
    """Busca uma playlist pelo ID."""
    playlists = load_playlists()
    for p in playlists:
        if p["id"] == playlist_id:
            return p
    return None
