import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

CHANNELS = [
    "UClt01z1wHHT7c5lKcU8pxRQ",  # HBomb
    "UCj74rJ9Lgl3WTngq675wxKg",  # Noodle
    "UCMAJEIm9a_NGhD7BgWDMoXw",  # Jimmy McGee
    "UCyNtlmLB73-7gtlBz00XOQQ",  # Folding Ideas
    "UCSdma21fnJzgmPodhC9SJ3g",  # NakeyJakey
    "UCBtWQTdJwOwC1YJPyCeugIg",  # Comedy Without Errors
    "UCDJACu5LRKWE7sqagICB-ew",  # Spice8Rack
    "UCJ6o36XL0CpYb6U5dNBiXHQ",  # Shaun
    "UCCT8a7d6S6RJUivBgNRsiYg",  # Three Arrows
    "UCo8186mZYAY49flt6HkbqlQ",  # Leon Massey
    "UCeDKIj0G5XbultKOQnacu_w",  # Jose
    "UCrr7y8rEXb7_RiVniwvzk9w",  # Thought Slime
    "UC358urzyldvD78E9o2sR-Og",  # Leftist Cooks
]

OUT = Path("data/youtube.json")
PER_CHANNEL = 15   # videos kept per channel
FLAT_LIMIT = 40    # videos in the combined list
DELAY = 3          # seconds between channels

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def candidate_queries(ch):
    core = ch[2:]
    return [
        f"playlist_id=UULF{core}",  # uploads, no Shorts
        f"playlist_id=UU{core}",    # uploads, with Shorts
        f"channel_id={ch}",         # classic feed
    ]


def parse_feed(xml_bytes):
    root = ET.fromstring(xml_bytes)
    name = root.findtext("a:author/a:name", default="", namespaces=NS)
    videos = []
    for entry in root.findall("a:entry", NS):
        vid = entry.findtext("yt:videoId", namespaces=NS)
        if not vid:
            continue
        videos.append({
            "id": vid,
            "title": entry.findtext("a:title", default="", namespaces=NS),
            "published": entry.findtext("a:published", default="", namespaces=NS),
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        })
    return name, videos[:PER_CHANNEL]


def fetch_channel(ch):
    for query in candidate_queries(ch):
        url = f"https://www.youtube.com/feeds/videos.xml?{query}"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; glance-youtube-cache)"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                name, videos = parse_feed(resp.read())
            if videos:
                print(f"OK   {ch} via {query.split('=')[0]}={query.split('=')[1][:6]}…")
                return name, videos
        except Exception as e:
            print(f"FAIL {ch} ({query[:14]}…): {e}")
        time.sleep(1)
    return None


def main():
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8")).get("channels", {})
        except Exception as e:
            print(f"Could not read existing file: {e}")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    channels = {}

    for i, ch in enumerate(CHANNELS):
        if i:
            time.sleep(DELAY)
        result = fetch_channel(ch)
        if result:
            name, videos = result
            channels[ch] = {"name": name, "fetched_at": now, "videos": videos}
        elif ch in old:
            print(f"KEEP {ch}: reusing last good data")
            channels[ch] = old[ch]
        else:
            print(f"SKIP {ch}: no data and nothing cached")

    flat = []
    for ch, data in channels.items():
        for v in data["videos"]:
            flat.append({**v, "channel": data["name"], "channel_id": ch})
    flat.sort(key=lambda v: v["published"], reverse=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"updated": now, "channels": channels, "videos": flat[:FLAT_LIMIT]},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
