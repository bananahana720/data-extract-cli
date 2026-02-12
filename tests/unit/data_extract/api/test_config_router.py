from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.routers import config as config_router_module
from data_extract.api.routers.config import apply_preset, get_current_preset


@pytest.mark.unit
def test_current_preset_reflects_applied_selection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "jobs.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(config_router_module, "SessionLocal", test_session_local)

    initial = get_current_preset()
    assert initial.preset is None

    apply_response = apply_preset("quality")
    assert apply_response.preset == "quality"

    after_apply = get_current_preset()
    assert after_apply.preset == "quality"
