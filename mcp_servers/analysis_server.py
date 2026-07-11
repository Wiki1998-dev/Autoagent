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
import config

mcp = FastMCP("analysis-server")

DATA_DIR = config.DATA_DIR / "scenarios"


@mcp.tool()
def get_scenario_metadata(scenario_id: str) -> dict:
    """Load the full scenario JSON by ID."""
    path = DATA_DIR / f"{scenario_id}.json"
    if not path.exists():
        return {"error": f"Scenario {scenario_id} not found"}
    return json.loads(path.read_text(encoding="utf-8"))


@mcp.tool()
def compare_sensor_predictions(scenario_id: str) -> dict:
    """Compare camera vs radar predictions for a scenario."""
    data = get_scenario_metadata(scenario_id)
    if "error" in data:
        return data
    preds = data["predictions"]
    return {
        "camera": preds["camera_model"],
        "radar": preds["radar_model"],
        "disagreement": preds["camera_model"]["class"] != preds["radar_model"]["class"],
    }


@mcp.tool()
def get_xai_summary(scenario_id: str) -> dict:
    """Get the explainability (XAI) summary for a scenario."""
    data = get_scenario_metadata(scenario_id)
    if "error" in data:
        return data
    return data.get("xai_summary", {})
