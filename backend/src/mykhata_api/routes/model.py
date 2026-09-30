import json
from typing import Any

from fastapi import APIRouter, HTTPException, status

from mykhata_api.deps import CurrentUser
from mykhata_ml.config import load_config, path

router = APIRouter(prefix="/api/model", tags=["model"])


@router.get("/results")
def results(_: CurrentUser) -> dict[str, Any]:
    file = path(load_config()["output"]["reports"]) / "results.json"
    if not file.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No training results yet. Run scripts/train.py first.")
    return json.loads(file.read_text(encoding="utf-8"))
