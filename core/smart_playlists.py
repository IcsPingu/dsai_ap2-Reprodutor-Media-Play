"""Validated, declarative rules evaluated against the current user's library."""

import math
from core.library_filters import normalized, track_format, missing_metadata
from core.sources import is_local_track, track_platform, PLATFORMS

TEXT_FIELDS = ("title", "artist", "album", "genre")
TEXT_OPERATORS = ("contains", "equals", "not_contains")
SORT_FIELDS = ("title", "artist", "album", "duration", "format")
MAX_RULES = 20


def validate_rule(rule):
    if not isinstance(rule, dict):
        raise ValueError("Cada regra deve ser um objeto.")
    field = rule.get("field")
    operator = rule.get("operator")
    value = rule.get("value")
    if field in TEXT_FIELDS:
        if operator not in TEXT_OPERATORS:
            raise ValueError("Operador de texto inválido.")
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise ValueError("Informe um texto de 1 a 200 caracteres.")
        value = value.strip()
    elif field == "format":
        if operator not in ("equals", "not_equals"):
            raise ValueError("Operador de formato inválido.")
        if value not in ("mp3", "wav", "flac"):
            raise ValueError("Selecione MP3, WAV ou FLAC.")
    elif field in ("source_type", "platform"):
        if operator not in ("equals", "not_equals"):
            raise ValueError("Operador de origem inválido.")
        choices = ("local", "external") if field == "source_type" else PLATFORMS
        if value not in choices:
            raise ValueError("Selecione uma origem ou plataforma válida.")
    elif field == "duration":
        if operator not in ("gte", "lte"):
            raise ValueError("Operador de duração inválido.")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("A duração deve ser um número em segundos.")
        if not math.isfinite(value) or value < 0:
            raise ValueError("A duração deve ser finita e não negativa.")
        value = float(value)
    elif field in ("favorite", "missing_metadata"):
        if operator != "equals" or not isinstance(value, bool):
            raise ValueError("A regra deve comparar Sim ou Não.")
    else:
        raise ValueError("Campo de regra inválido.")
    return {"field": field, "operator": operator, "value": value}


def validate_definition(definition):
    if not isinstance(definition, dict):
        raise ValueError("Definição de playlist inválida.")
    rules = definition.get("rules")
    if not isinstance(rules, list) or not 1 <= len(rules) <= MAX_RULES:
        raise ValueError(f"Use entre 1 e {MAX_RULES} regras.")
    match = definition.get("match", "all")
    if match not in ("all", "any"):
        raise ValueError("Escolha combinar todas ou qualquer regra.")
    sort = definition.get("sort", "title")
    if sort not in SORT_FIELDS:
        raise ValueError("Ordenação inválida.")
    descending = definition.get("descending", False)
    if not isinstance(descending, bool):
        raise ValueError("Direção de ordenação inválida.")
    limit = definition.get("limit", 0)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 0 <= limit <= 10000:
        raise ValueError("O limite deve estar entre 0 e 10000 faixas.")
    return {
        "rules": [validate_rule(rule) for rule in rules],
        "match": match,
        "sort": sort,
        "descending": descending,
        "limit": limit,
    }


def rule_matches(track, rule):
    field, operator, expected = rule["field"], rule["operator"], rule["value"]
    if field in ("source_type", "platform"):
        actual = ("local" if is_local_track(track) else "external") \
            if field == "source_type" else track_platform(track)
        equal = actual == expected
        return equal if operator == "equals" else not equal
    if field in TEXT_FIELDS:
        actual = normalized(track.get(field) or "")
        expected = normalized(expected)
        if operator == "contains":
            return expected in actual
        if operator == "not_contains":
            return expected not in actual
        return actual == expected
    if field == "format":
        equal = track_format(track).lower() == expected
        return equal if operator == "equals" else not equal
    if field == "favorite":
        return bool(track.get("favorite", False)) == expected
    if field == "missing_metadata":
        return missing_metadata(track) == expected
    if not is_local_track(track):
        return False
    try:
        duration = float(track.get("duration", 0))
    except (TypeError, ValueError):
        return False
    if not math.isfinite(duration) or duration < 0:
        return False
    return duration >= expected if operator == "gte" else duration <= expected


def _duration(track):
    try:
        value = float(track.get("duration", 0))
        return value if math.isfinite(value) and value >= 0 else 0
    except (ValueError, TypeError):
        return 0


def evaluate(definition, library):
    definition = validate_definition(definition)
    combine = all if definition["match"] == "all" else any
    tracks = []
    seen = set()
    for track in library:
        identity = track.get("id")
        if not identity or identity in seen:
            continue
        if combine(rule_matches(track, rule) for rule in definition["rules"]):
            tracks.append(track)
            seen.add(identity)
    field = definition["sort"]
    def key(track):
        if field == "duration":
            value = _duration(track)
        elif field == "format":
            value = normalized(track_format(track))
        else:
            value = normalized(track.get(field) or "")
        return value, normalized(track.get("title") or ""), str(track["id"])
    tracks.sort(key=key, reverse=definition["descending"])
    return tracks[:definition["limit"]] if definition["limit"] else tracks
