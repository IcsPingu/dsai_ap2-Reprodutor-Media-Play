from core.user_storage import atomic_json
from core.user_storage import scoped_path, accessible_path, serialized, user_directory
import os
import json
import hashlib
from io import BytesIO
from typing import List, Dict, Any, Optional
from PIL import Image
from core.audio_formats import supported_audio, audio_mime_type, read_audio, write_audio_tags

STORAGE_DIR = "storage"
COVERS_DIR = os.path.join(STORAGE_DIR, "covers")
MEDIA_DIR = os.path.join(STORAGE_DIR, "media")
LIBRARY_JSON = os.path.join(STORAGE_DIR, "library.json")
DEFAULT_COVER = os.path.join(COVERS_DIR, "default_cover.png")


def ensure_storage_dirs():
    """Garante que as pastas de armazenamento existam."""
    os.makedirs(scoped_path(COVERS_DIR, "covers"), exist_ok=True)
    os.makedirs(scoped_path(MEDIA_DIR, "media"), exist_ok=True)
    if not os.path.exists(scoped_path(LIBRARY_JSON, "library.json")):
        with open(scoped_path(LIBRARY_JSON, "library.json"), "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def generate_track_id(filepath: str) -> str:
    """Gera um ID hash unico com base no caminho do arquivo."""
    return hashlib.md5(filepath.encode("utf-8")).hexdigest()[:12]


def extract_cover_art(filepath: str, track_id: str) -> str:
    """
    Extrai a capa do album da tag ID3 APIC se existir.
    Salva em storage/covers/<track_id>.png e retorna o caminho.
    Se nao houver capa, retorna scoped_path(DEFAULT_COVER, "covers/default_cover.png").
    """
    ensure_storage_dirs()
    cover_filename = f"cover_{track_id}.png"
    cover_filepath = os.path.join(scoped_path(COVERS_DIR, "covers"), cover_filename)

    if os.path.exists(cover_filepath):
        return cover_filepath

    try:
        audio = read_audio(filepath)
        if audio is not None and hasattr(audio, "tags") and audio.tags:
            for key in audio.tags.keys():
                if key.startswith("APIC"):
                    apic = audio.tags[key]
                    image_data = apic.data
                    img = Image.open(BytesIO(image_data))
                    img.thumbnail((400, 400))
                    img.save(cover_filepath, format="PNG")
                    return cover_filepath
        if getattr(audio, "pictures", None):
            picture = next((p for p in audio.pictures if p.type == 3), audio.pictures[0])
            with Image.open(BytesIO(picture.data)) as img:
                img.thumbnail((400, 400))
                img.save(cover_filepath, format="PNG")
                return cover_filepath
    except Exception as e:
        print(f"Erro ao extrair capa de {filepath}: {e}")

    return scoped_path(DEFAULT_COVER, "covers/default_cover.png") if os.path.exists(scoped_path(DEFAULT_COVER, "covers/default_cover.png")) else ""


def parse_audio_metadata(filepath: str) -> Dict[str, Any]:
    """
    Extrai duração, tags nativas e capa de arquivos MP3, WAV ou FLAC.
    """
    if not accessible_path(filepath):
        raise ValueError("Arquivo fora da biblioteca do usuário.")
    audio = read_audio(filepath)
    track_id = generate_track_id(filepath)
    filename = os.path.basename(filepath)
    title_default = os.path.splitext(filename)[0]

    metadata = {
        "format": os.path.splitext(filepath)[1][1:].lower(),
        "mime_type": audio_mime_type(filepath),
        "id": track_id,
        "filepath": filepath,
        "filename": filename,
        "title": title_default,
        "artist": "Artista Desconhecido",
        "album": "Album Desconhecido",
        "year": "N/A",
        "genre": "Genero Desconhecido",
        "duration": 0,
        "duration_str": "00:00",
        "cover_path": scoped_path(DEFAULT_COVER, "covers/default_cover.png"),
    }

    try:
        audio = read_audio(filepath)
        if audio is not None:
            if hasattr(audio.info, "length"):
                duration_sec = int(audio.info.length)
                metadata["duration"] = duration_sec
                mins = duration_sec // 60
                secs = duration_sec % 60
                metadata["duration_str"] = f"{mins:02d}:{secs:02d}"

            if hasattr(audio, "tags") and audio.tags:
                tags = audio.tags
                if "TIT2" in tags and str(tags["TIT2"]).strip():
                    metadata["title"] = str(tags["TIT2"]).strip()
                if "TPE1" in tags and str(tags["TPE1"]).strip():
                    metadata["artist"] = str(tags["TPE1"]).strip()
                if "TALB" in tags and str(tags["TALB"]).strip():
                    metadata["album"] = str(tags["TALB"]).strip()
                if "TDRC" in tags and str(tags["TDRC"]).strip():
                    metadata["year"] = str(tags["TDRC"]).strip()
                elif "TYER" in tags and str(tags["TYER"]).strip():
                    metadata["year"] = str(tags["TYER"]).strip()
                if "TCON" in tags and str(tags["TCON"]).strip():
                    metadata["genre"] = str(tags["TCON"]).strip()

        if metadata["format"] == "flac" and audio.tags:
            fields = {"title": "title", "artist": "artist", "album": "album", "year": "date", "genre": "genre"}
            for field, tag in fields.items():
                values = audio.tags.get(tag, [])
                if values and str(values[0]).strip():
                    metadata[field] = str(values[0]).strip()
        metadata["cover_path"] = extract_cover_art(filepath, track_id)

    except Exception as e:
        print(f"Erro ao ler metadados de {filepath}: {e}")

    return metadata


def parse_mp3_metadata(filepath: str) -> Dict[str, Any]:
    """Compatibilidade para consumidores antigos; aceita os três formatos."""
    return parse_audio_metadata(filepath)


def resolve_filepath(filepath: str) -> str:
    """Resolve o caminho do arquivo de audio de forma portavel entre OS e Streamlit Cloud."""
    if not filepath:
        return ""
    if not accessible_path(filepath):
        return ""
    if os.path.exists(filepath):
        return filepath
    filename = os.path.basename(filepath.replace("\\", "/"))
    media_path = os.path.join(scoped_path(MEDIA_DIR, "media"), filename)
    if os.path.exists(media_path):
        return media_path
    return filepath


def resolve_coverpath(cover_path: str) -> str:
    """Resolve o caminho da capa de forma portavel."""
    if cover_path and not accessible_path(cover_path):
        return ""
    if not cover_path:
        return scoped_path(DEFAULT_COVER, "covers/default_cover.png") if os.path.exists(scoped_path(DEFAULT_COVER, "covers/default_cover.png")) else ""
    if os.path.exists(cover_path):
        return cover_path
    filename = os.path.basename(cover_path.replace("\\", "/"))
    rel_cover = os.path.join(scoped_path(COVERS_DIR, "covers"), filename)
    if os.path.exists(rel_cover):
        return rel_cover
    return scoped_path(DEFAULT_COVER, "covers/default_cover.png") if os.path.exists(scoped_path(DEFAULT_COVER, "covers/default_cover.png")) else ""


@serialized
def load_library() -> List[Dict[str, Any]]:
    """Carrega a lista de faixas do arquivo JSON local com caminhos resolvidos."""
    ensure_storage_dirs()
    if not os.path.exists(scoped_path(LIBRARY_JSON, "library.json")):
        return []
    try:
        with open(scoped_path(LIBRARY_JSON, "library.json"), "r", encoding="utf-8") as f:
            items = json.load(f)
            for item in items:
                item["filepath"] = resolve_filepath(item.get("filepath", ""))
                item["cover_path"] = resolve_coverpath(item.get("cover_path", ""))
            return items
    except Exception as e:
        print(f"Erro ao ler {scoped_path(LIBRARY_JSON, "library.json")}: {e}")
        return []


@serialized
def save_library(library: List[Dict[str, Any]]):
    """Salva a lista de faixas no arquivo JSON local."""
    ensure_storage_dirs()
    atomic_json(scoped_path(LIBRARY_JSON, "library.json"), library)


@serialized
def scan_directory(folder_path: str) -> List[Dict[str, Any]]:
    """
    Varre um diretorio local em busca de arquivos MP3, WAV e FLAC,
    extrai metadados de cada arquivo e atualiza a biblioteca.
    """
    if user_directory() is not None:
        raise ValueError("Use o upload para importar arquivos na conta web.")
    if not os.path.isdir(folder_path):
        return load_library()

    current_library = {t["filepath"]: t for t in load_library()}

    for root, _, files in os.walk(folder_path):
        for file in files:
            if supported_audio(file):
                full_path = os.path.abspath(os.path.join(root, file))
                if full_path not in current_library:
                    try:
                        metadata = parse_audio_metadata(full_path)
                    except ValueError as error:
                        raise ValueError(f"{file}: {error}") from error
                    current_library[full_path] = metadata

    updated_library_list = list(current_library.values())
    save_library(updated_library_list)
    return updated_library_list


@serialized
def import_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """Importa uma lista de caminhos de arquivos MP3, WAV e FLAC fisicos."""
    current_library = {t["filepath"]: t for t in load_library()}
    for filepath in file_paths:
        if supported_audio(filepath) and os.path.isfile(filepath):
            if not accessible_path(filepath):
                raise ValueError("Arquivo fora da biblioteca do usuário.")
            abs_path = os.path.abspath(filepath)
            if abs_path not in current_library:
                metadata = parse_audio_metadata(abs_path)
                current_library[abs_path] = metadata

    updated_list = list(current_library.values())
    save_library(updated_list)
    return updated_list


@serialized
def import_uploaded_files(uploaded_files) -> List[Dict[str, Any]]:
    """Salva arquivos enviados via Streamlit file_uploader no disco e os adiciona a biblioteca."""
    ensure_storage_dirs()
    imported_paths = []
    original_names = {}
    for file_obj in uploaded_files:
        filename = os.path.basename(file_obj.name.replace("\\", "/"))
        if not supported_audio(filename):
            raise ValueError(f"Formato não suportado: {filename}")
        content = bytes(file_obj.getbuffer())
        read_audio(BytesIO(content), filename)
        stem, extension = os.path.splitext(filename)
        digest = hashlib.sha256(content).hexdigest()
        save_path = os.path.join(scoped_path(MEDIA_DIR, "media"), f"{stem}_{digest}{extension.lower()}")
        with open(save_path, "wb") as f:
            f.write(content)
        absolute_path = os.path.abspath(save_path)
        imported_paths.append(absolute_path)
        original_names[absolute_path] = filename
    tracks = import_files(imported_paths)
    for track in tracks:
        original_name = original_names.get(track["filepath"])
        if original_name:
            generated_title = os.path.splitext(os.path.basename(track["filepath"]))[0]
            if track["title"] == generated_title:
                track["title"] = os.path.splitext(original_name)[0]
            track["filename"] = original_name
    save_library(tracks)
    return tracks


def open_folder_picker_dialog() -> str:
    """Abre uma janela nativa do Explorador de Arquivos do Windows para selecionar uma pasta."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        folder_selected = filedialog.askdirectory(master=root, title="Selecione a pasta com arquivos MP3, WAV e FLAC")
        root.destroy()
        return folder_selected if folder_selected else ""
    except Exception as e:
        print(f"Erro ao abrir seletor de pasta nativo: {e}")
        return ""


@serialized
def save_custom_cover(track_id: str, uploaded_file) -> Optional[str]:
    """Salva a imagem enviada pelo usuario (PNG, JPG, WEBP) como capa da musica."""
    if not uploaded_file:
        return None
    ensure_storage_dirs()
    cover_filename = f"cover_{track_id}.png"
    cover_filepath = os.path.join(scoped_path(COVERS_DIR, "covers"), cover_filename)

    try:
        image_bytes = uploaded_file.getvalue()
        img = Image.open(BytesIO(image_bytes))
        img = img.convert("RGB")
        img.thumbnail((500, 500))
        img.save(cover_filepath, format="PNG")

        library = load_library()
        for track in library:
            if track["id"] == track_id:
                track["cover_path"] = cover_filepath
                break
        save_library(library)
        return cover_filepath
    except Exception as e:
        print(f"Erro ao salvar capa personalizada: {e}")
        return None


@serialized
def update_track_metadata(track_id: str, new_data: Dict[str, str]) -> bool:
    """
    Atualiza os metadados de uma faixa na biblioteca e opcionalmente na tag ID3 do arquivo.
    """
    library = load_library()
    updated = False
    for track in library:
        if track["id"] == track_id:
            for field in ["title", "artist", "album", "year", "genre"]:
                if field in new_data:
                    track[field] = new_data[field]
            updated = True

            try:
                write_audio_tags(track["filepath"], new_data)
            except Exception as e:
                print(f"Aviso ao salvar tag ID3 no arquivo: {e}")

            break

    if updated:
        save_library(library)
    return updated


@serialized
def set_favorite(track_id: str, favorite: bool) -> bool:
    library = load_library()
    for track in library:
        if track["id"] == track_id:
            track["favorite"] = bool(favorite)
            save_library(library)
            return True
    return False
