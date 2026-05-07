#!/usr/bin/env python3
"""Update README plugin download metrics from Deckbrew."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
DECKBREW_PLUGINS_URL = "https://plugins.deckbrew.xyz/plugins"
USER_AGENT = "xXJSONDeruloXx-profile-readme-metrics"

DECKY_PLUGINS = {
    97: {"label": "Decky--Framegen", "color": "6366f1"},
    113: {"label": "Decky%20LSFG--VK", "color": "0ea5e9"},
    98: {"label": "Decky--Lookup", "color": "f59e0b"},
    92: {"label": "Crosshair", "color": "ef4444"},
}


def fetch_deckbrew_downloads() -> dict[int, int]:
    request = urllib.request.Request(
        DECKBREW_PLUGINS_URL,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        plugins = json.load(response)

    by_id = {int(plugin["id"]): plugin for plugin in plugins}
    return {plugin_id: int(by_id[plugin_id].get("downloads", 0)) for plugin_id in DECKY_PLUGINS}


def badge_count(value: int) -> str:
    return urllib.parse.quote(f"{value:,}", safe="")


def replace_badge(markdown: str, label: str, color: str, value: int) -> str:
    encoded = badge_count(value)
    pattern = rf"({re.escape(label)}%20Decky%20Store%20downloads-)[0-9%2C]+(-{re.escape(color)}\?style=flat-square(?:&[^)]+)?)"
    return re.sub(pattern, rf"\g<1>{encoded}\2", markdown)


def main() -> None:
    downloads = fetch_deckbrew_downloads()
    markdown = README.read_text()

    for plugin_id, meta in DECKY_PLUGINS.items():
        markdown = replace_badge(markdown, meta["label"], meta["color"], downloads[plugin_id])

    README.write_text(markdown)


if __name__ == "__main__":
    main()
