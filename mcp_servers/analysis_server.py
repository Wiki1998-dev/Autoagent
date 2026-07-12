"""
Analysis MCP Server.

Provides structured analysis tools:
  - get_scenario_metadata
  - compare_sensor_predictions
  - get_xai_summary
"""

import json
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel, Field
import config

mcp = FastMCP("analysis-server")

DATA_DIR = config.DATA_DIR / "scenarios"


# ── Response models ───────────────────────────────────────────

class SensorComparison(BaseModel):
    camera: dict
    radar: dict
    disagreement: bool

class XAISummary(BaseModel):
    data: dict


# ── Internal loader (not a tool — used by other tools) ────────

def _load_scenario(scenario_id: str) -> dict:
    """Load raw scenario JSON from disk. Raises FileNotFoundError if missing."""
    # Prevent path traversal by extracting only the filename
    safe_name = Path(scenario_id).name
    path = DATA_DIR / f"{safe_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenario '{scenario_id}' not found in {DATA_DIR}")
    return json.loads(path.read_text(encoding="utf-8"))


# ── Tools ─────────────────────────────────────────────────────

@mcp.tool()
def get_scenario_metadata(
    scenario_id: str = Field(description="Scenario identifier, e.g. 'SC-042'"),
) -> dict:
    """Load the full scenario JSON by ID. Returns the raw scenario data dict."""
    try:
        return _load_scenario(scenario_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def compare_sensor_predictions(
    scenario_id: str = Field(description="Scenario identifier, e.g. 'SC-042'"),
) -> SensorComparison | dict:
    """Compare camera vs radar predictions for a scenario."""
    try:
        data = _load_scenario(scenario_id)
        preds = data.get("predictions", {})
        camera = preds.get("camera_model", {})
        radar = preds.get("radar_model", {})
        return SensorComparison(
            camera=camera,
            radar=radar,
            disagreement=camera.get("class") != radar.get("class"),
        )
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_xai_summary(
    scenario_id: str = Field(description="Scenario identifier, e.g. 'SC-042'"),
) -> dict:
    """Get the explainability (XAI) summary for a scenario."""
    try:
        data = _load_scenario(scenario_id)
        return data.get("xai_summary", {})
    except Exception as e:
        return {"error": str(e)}
