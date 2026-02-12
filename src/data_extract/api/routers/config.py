"""Configuration API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data_extract.api.database import SessionLocal
from data_extract.api.models import AppSetting
from data_extract.cli.config import (
    PresetManager,
    load_merged_config,
)
from data_extract.cli.config import (
    list_presets as list_config_presets,
)

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class ApplyPresetResponse(BaseModel):
    """Preset apply response payload."""

    preset: str
    effective_config: dict


class PresetSummary(BaseModel):
    """Summary metadata for a preset entry."""

    name: str
    category: str
    description: str | None = None
    is_builtin: bool


class PresetPreviewResponse(BaseModel):
    """Preset preview payload."""

    preset: str
    effective_config: dict


def _preset_to_effective_config(name: str) -> dict:
    manager = PresetManager()
    try:
        preset = manager.load(name)
        return {
            "format": preset.output_format,
            "chunk": {"size": preset.chunk_size},
            "quality": {"min_score": preset.quality_threshold},
            "semantic": {
                "similarity": {
                    "duplicate_threshold": preset.dedup_threshold,
                }
            },
            "metadata": {"include": preset.include_metadata},
            "validation": {"level": preset.validation_level.value},
        }
    except KeyError:
        pass

    config_presets = list_config_presets() if callable(list_config_presets) else []
    names = {entry.get("name") for entry in config_presets if isinstance(entry, dict)}
    if name in names:
        return load_merged_config(preset_name=name).to_dict()

    raise HTTPException(status_code=404, detail=f"Preset not found: {name}")


@router.get("/effective")
def get_effective_config() -> dict:
    """Return effective merged configuration."""
    return load_merged_config().to_dict()


@router.post("/presets/{name}/apply", response_model=ApplyPresetResponse)
def apply_preset(name: str) -> ApplyPresetResponse:
    """Apply a preset and persist latest choice in app settings."""
    config = _preset_to_effective_config(name)

    with SessionLocal() as db:
        setting = db.get(AppSetting, "last_preset")
        if setting is None:
            setting = AppSetting(key="last_preset", value=name, updated_at=datetime.utcnow())
            db.add(setting)
        else:
            setting.value = name
            setting.updated_at = datetime.utcnow()
        db.commit()

    return ApplyPresetResponse(preset=name, effective_config=config)


@router.get("/presets", response_model=list[PresetSummary])
def list_presets() -> list[PresetSummary]:
    """List available presets for UI selection."""
    manager = PresetManager()
    output: dict[str, PresetSummary] = {}

    for preset in manager.list_builtin().values():
        output[preset.name] = PresetSummary(
            name=preset.name,
            category="preset_manager",
            description=preset.description,
            is_builtin=True,
        )

    for preset in manager.list_custom():
        output[preset.name] = PresetSummary(
            name=preset.name,
            category="preset_manager",
            description=preset.description,
            is_builtin=False,
        )

    config_presets = list_config_presets() if callable(list_config_presets) else []
    for entry in config_presets:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name or name in output:
            continue
        output[name] = PresetSummary(
            name=name,
            category="config",
            description=None,
            is_builtin=bool(entry.get("is_builtin")),
        )

    return sorted(output.values(), key=lambda preset: preset.name)


@router.get("/presets/{name}/preview", response_model=PresetPreviewResponse)
def preview_preset(name: str) -> PresetPreviewResponse:
    """Preview resolved configuration for a preset."""
    return PresetPreviewResponse(
        preset=name,
        effective_config=_preset_to_effective_config(name),
    )
