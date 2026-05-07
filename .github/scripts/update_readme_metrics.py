#!/usr/bin/env python3
"""Update README plugin metrics from Deckbrew and GitHub releases."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
DECKBREW_PLUGINS_URL = "https://plugins.deckbrew.xyz/plugins"
GITHUB_RELEASES_URL = "https://api.github.com/repos/{owner}/{repo}/releases?per_page=100"

USER_AGENT = "xXJSONDeruloXx-profile-readme-metrics"

DECKY_PLUGINS = {
    97: {"name": "Decky-Framegen", "label": "Decky--Framegen", "color": "6366f1"},
    113: {"name": "Decky LSFG-VK", "label": "Decky%20LSFG--VK", "color": "0ea5e9"},
    98: {"name": "Decky-Lookup", "label": "Decky--Lookup", "color": "f59e0b"},
    92: {"name": "Crosshair", "label": "Crosshair", "color": "ef4444"},
}

GITHUB_REPOS = {
    "Decky-Framegen": {"owner": "xXJSONDeruloXx", "repo": "Decky-Framegen", "label": "Decky--Framegen", "color": "6366f1"},
    "Decky LSFG-VK": {"owner": "xXJSONDeruloXx", "repo": "decky-lsfg-vk", "label": "Decky%20LSFG--VK", "color": "0ea5e9"},
}


def request_json(url: str) -> object:
    headers = {"User-Agent": USER_AGENT}
    if "api.github.com" in url and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_deckbrew_metrics() -> dict[int, dict[str, int]]:
    plugins = request_json(DECKBREW_PLUGINS_URL)
    by_id = {int(plugin["id"]): plugin for plugin in plugins}
    return {
        plugin_id: {
            "downloads": int(by_id[plugin_id].get("downloads", 0)),
            "updates": int(by_id[plugin_id].get("updates", 0)),
        }
        for plugin_id in DECKY_PLUGINS
    }


def fetch_github_downloads(owner: str, repo: str) -> int:
    total = 0
    page = 1
    while True:
        url = GITHUB_RELEASES_URL.format(owner=owner, repo=repo) + f"&page={page}"
        releases = request_json(url)
        if not releases:
            break
        total += sum(
            int(asset.get("download_count", 0))
            for release in releases
            for asset in release.get("assets", [])
        )
        if len(releases) < 100:
            break
        page += 1
    return total


def badge_count(value: int) -> str:
    return urllib.parse.quote(f"{value:,}", safe="")


def replace_metric_badge(markdown: str, label: str, metric: str, color: str, value: int, style: str = "flat-square") -> str:
    encoded = badge_count(value)
    pattern = rf"({re.escape(label)}%20{re.escape(metric)}-)[0-9%2C]+(-{re.escape(color)}\?style={re.escape(style)}(?:&[^)]+)?)"
    return re.sub(pattern, rf"\g<1>{encoded}\2", markdown)


def replace_total_badge(markdown: str, metric: str, color: str, value: int) -> str:
    encoded = badge_count(value)
    pattern = rf"(total%20{re.escape(metric)}-)[0-9%2C]+(-{re.escape(color)}\?style=for-the-badge(?:&[^)]+)?)"
    return re.sub(pattern, rf"\g<1>{encoded}\2", markdown)


def main() -> None:
    deckbrew = fetch_deckbrew_metrics()
    github = {
        name: fetch_github_downloads(meta["owner"], meta["repo"])
        for name, meta in GITHUB_REPOS.items()
    }

    markdown = README.read_text()

    for plugin_id, meta in DECKY_PLUGINS.items():
        metrics = deckbrew[plugin_id]
        markdown = replace_metric_badge(markdown, meta["label"], "downloads", meta["color"], metrics["downloads"])
        markdown = replace_metric_badge(markdown, meta["label"], "updates", meta["color"], metrics["updates"])

    for name, meta in GITHUB_REPOS.items():
        markdown = replace_metric_badge(markdown, meta["label"], "GitHub%20downloads", meta["color"], github[name])

    markdown = replace_total_badge(markdown, "Decky%20Store%20downloads", "22c55e", sum(m["downloads"] for m in deckbrew.values()))
    markdown = replace_total_badge(markdown, "Decky%20Store%20updates", "14b8a6", sum(m["updates"] for m in deckbrew.values()))
    markdown = replace_total_badge(markdown, "GitHub%20release%20downloads", "181717", sum(github.values()))

    README.write_text(markdown)


if __name__ == "__main__":
    main()
