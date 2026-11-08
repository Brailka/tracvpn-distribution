#!/usr/bin/env python3
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SERVERS = ROOT / "Tracservis" / "servis.txt"
CATALOG = ROOT / "catalog.json"
APK_PATTERN = re.compile(r"^tracVPN-(\d+)-([0-9A-Za-z._-]+)\.apk$")


def load_servers():
    links = []
    for raw in SERVERS.read_text(encoding="utf-8").splitlines():
        link = raw.strip()
        if not link or link.startswith("#"):
            continue
        parsed = urlsplit(link)
        if parsed.scheme != "vless" or not parsed.hostname or not parsed.port:
            raise SystemExit(f"Invalid VLESS link: {link[:40]}")
        uuid.UUID(parsed.username)
        links.append(link)
    if not 1 <= len(links) <= 200:
        raise SystemExit("servis.txt must contain 1 to 200 VLESS links")
    return links


def latest_update():
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not repository:
        return None
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "tracVPN-catalog"},
    )
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            release = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    candidates = []
    for asset in release.get("assets", []):
        match = APK_PATTERN.match(asset.get("name", ""))
        if match:
            candidates.append((int(match.group(1)), match.group(2), asset["browser_download_url"]))
    if not candidates:
        return None
    code, version, url = max(candidates)
    return {"versionCode": code, "versionName": version, "apkUrl": url}


catalog = {"servers": load_servers()}
update = latest_update()
if update:
    catalog["update"] = update
CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {CATALOG} with {len(catalog['servers'])} servers")
