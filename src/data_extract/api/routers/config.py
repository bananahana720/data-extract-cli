"""Configuration API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data_extract.api.database import SessionLocal
from data_extract.api.models import AppSetting
from data_extract.cli.config import load_merged_config

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class ApplyPresetResponse(BaseModel):
    """Preset apply response payload."""

    preset: str
    effective_config: dict


@router.get("/effective")
def get_effective_config() -> dict:
    """Return effective merged configuration."""
    return load_merged_config().to_dict()


@router.post("/presets/{name}/apply", response_model=ApplyPresetResponse)
def apply_preset(name: str) -> ApplyPresetResponse:
    """Apply a preset and persist latest choice in app settings."""
    config = load_merged_config(preset_name=name).to_dict()
    if not config:
        raise HTTPException(status_code=404, detail=f"Preset not found: {name}")

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
