from __future__ import annotations

from pathlib import Path
import tomllib

from .models import SourceConfig


class ConfigError(ValueError):
    pass


def load_toml(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Configuration file not found: {p}")
    with p.open("rb") as handle:
        return tomllib.load(handle)


def load_profile(path: str | Path) -> dict:
    data = load_toml(path)
    for section in ("identity", "preferences", "personas"):
        if section not in data:
            raise ConfigError(f"Missing [{section}] in {path}")
    if not data["personas"]:
        raise ConfigError("At least one persona is required")
    return data


def load_sources(path: str | Path) -> list[SourceConfig]:
    data = load_toml(path)
    raw_sources = data.get("sources", [])
    if not isinstance(raw_sources, list):
        raise ConfigError("sources.toml must contain [[sources]] entries")
    sources: list[SourceConfig] = []
    names: set[str] = set()
    for item in raw_sources:
        for field in ("name", "type", "company", "board"):
            if not str(item.get(field, "")).strip():
                raise ConfigError(f"Source missing required field {field}: {item}")
        name = str(item["name"])
        if name in names:
            raise ConfigError(f"Duplicate source name: {name}")
        names.add(name)
        source_type = str(item["type"]).lower()
        if source_type not in {"greenhouse", "lever", "ashby"}:
            raise ConfigError(f"Unsupported source type: {source_type}")
        instance = str(item.get("instance", "global")).lower()
        if source_type == "lever" and instance not in {"global", "eu"}:
            raise ConfigError(f"Invalid Lever instance for {name}: {instance}")
        sources.append(SourceConfig(
            name=name,
            type=source_type,
            company=str(item["company"]),
            board=str(item["board"]),
            enabled=bool(item.get("enabled", True)),
            instance=instance,
        ))
    return sources
