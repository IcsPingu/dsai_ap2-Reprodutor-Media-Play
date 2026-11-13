"""Format recognition and native tag handling shared by import and playback."""

import os

import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.id3 import TIT2, TPE1, TALB, TDRC, TCON


AUDIO_TYPES = {
    ".mp3": (MP3, "audio/mpeg"),
    ".wav": (WAVE, "audio/wav"),
    ".flac": (FLAC, "audio/flac"),
}


def supported_audio(filename):
    """Extensions are case insensitive; content is checked separately."""
    extension = os.path.splitext(os.fspath(filename))[1].lower()
    return extension in AUDIO_TYPES


def audio_mime_type(filename):
    extension = os.path.splitext(os.fspath(filename))[1].lower()
    if extension not in AUDIO_TYPES:
        raise ValueError(f"Formato de áudio não suportado: {extension}")
    return AUDIO_TYPES[extension][1]


def read_audio(source, filename=None):
    """Reject corrupt files and extensions that disagree with actual content."""
    name = filename if filename is not None else os.fspath(source)
    extension = os.path.splitext(name)[1].lower()
    if extension not in AUDIO_TYPES:
        raise ValueError(f"Formato de áudio não suportado: {extension}")
    expected_class = AUDIO_TYPES[extension][0]
    try:
        audio = mutagen.File(source)
    except (mutagen.MutagenError, OSError, ValueError, EOFError) as error:
        raise ValueError(f"Arquivo inválido ou ilegível: {name}") from error
    if not isinstance(audio, expected_class):
        raise ValueError(f"Conteúdo incompatível com a extensão: {name}")
    return audio


def write_audio_tags(filepath, values):
    """Write Vorbis comments for FLAC and native ID3 chunks for WAV/MP3."""
    audio = read_audio(filepath)
    if audio.tags is None:
        audio.add_tags()
    if isinstance(audio, FLAC):
        fields = {"title": "title", "artist": "artist", "album": "album", "year": "date", "genre": "genre"}
        for field, tag in fields.items():
            if field in values:
                audio[tag] = [str(values[field])]
    else:
        fields = {"title": TIT2, "artist": TPE1, "album": TALB, "year": TDRC, "genre": TCON}
        for field, frame in fields.items():
            if field in values:
                audio.tags.add(frame(encoding=3, text=str(values[field])))
    audio.save()
