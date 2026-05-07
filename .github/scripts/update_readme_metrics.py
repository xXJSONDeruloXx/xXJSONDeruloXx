#!/usr/bin/env python3
"""Update README Decky plugin install metrics from the Decky plugin index."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
DECKY_PLUGINS_URL = "https://plugins.deckbrew.xyz/plugins"

PLUGINS = {
    97: {"label": "Decky--Framegen", "color": "6366f1"},
    113: {"label": "Decky%20LSFG--VK", "color": "0ea5e9"},
    98: {"label": "Decky--Lookup", "color": "f59e0b"},
    92: {"label": "Crosshair", "color": "ef4444"},
}

PROJECT_INSTALL_BADGES = {
    97: "6366f1",
    113: "0ea5e9",
}


def fetch_downloads() -> dict[int, int]:
    request = urllib.request.Request(
        DECKY_PLUGINS_URL,
        headers={"User-Agent": "xXJSONDeruloXx-profile-readme-metrics"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        plugins = json.load(response)

    by_id = {int(plugin["id"]): int(plugin.get("downloads", 0)) for plugin in plugins}
    return {plugin_id: by_id[plugin_id] for plugin_id in PLUGINS}


def badge_count(value: int) -> str:
    return urllib.parse.quote(f"{value:,}", safe="")


def replace_badge_count(markdown: str, label: str, color: str, value: int) -> str:
    encoded = badge_count(value)
    return re.sub(
        rf"({re.escape(label)}-)[0-9%2C]+(-{re.escape(color)}\?style=flat-square)",
        rf"\g<1>{encoded}\2",
        markdown,
    )


def main() -> None:
    downloads = fetch_downloads()
    markdown = README.read_text()

    for plugin_id, meta in PLUGINS.items():
        markdown = replace_badge_count(
            markdown,
            label=meta["label"],
            color=meta["color"],
            value=downloads[plugin_id],
        )

    for plugin_id, color in PROJECT_INSTALL_BADGES.items():
        encoded = badge_count(downloads[plugin_id])
        markdown = re.sub(
            rf"(Decky%20installs-)[0-9%2C]+(-{re.escape(color)}\?style=flat-square&logo=steam&logoColor=white)",
            rf"\g<1>{encoded}\2",
            markdown,
            count=1,
        )

    total = sum(downloads.values())
    markdown = re.sub(
        r"(total%20Decky%20installs-)[0-9%2C]+(-22c55e\?style=for-the-badge&logo=steam&logoColor=white)",
        rf"\g<1>{badge_count(total)}\2",
        markdown,
    )

    README.write_text(markdown)


if __name__ == "__main__":
    main()
