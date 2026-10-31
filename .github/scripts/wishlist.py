import csv
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

INPUT_PATH = Path('input/wishlist.csv')
OUTPUT_PATH = Path('data/wishlist.json')

REQUEST_DELAY = 1.5   # Steam's appdetails endpoint rate-limits aggressively
MAX_ATTEMPTS = 3

# A game only counts as released once its release date is at least this many days old
MIN_DAYS_SINCE_RELEASE = 1

EXCLUDED_GENRES = ["Early Access"]

DATE_FORMATS = ["%d %b, %Y", "%b %d, %Y", "%d %B, %Y", "%B %d, %Y", "%d %b %Y", "%b %d %Y"]


def make_keywords(game_name: str) -> str:
    words = re.findall(r"[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)*", game_name.lower())
    return "+".join(words)


def parse_release_date(text):
    """Parses a full release date. Returns None for 'Coming soon', 'Q4 2026', '2026', etc."""
    if not text:
        return None
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def fetch_app_details(appid):
    """
    Returns (status, data):
      ("ok", game_data)  - Steam answered with usable data
      ("error", None)    - transient or unknown failure; caller should fall back to previous data
    """
    url = "https://store.steampowered.com/api/appdetails"
    params = {"appids": appid, "l": "english"}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 429:
                raise requests.HTTPError("rate limited (429)")
            response.raise_for_status()
            payload = response.json().get(str(appid), {})
            if not payload.get("success"):
                # Region-locked, delisted, or bad ID. Treat as unknown rather than "unreleased".
                return "error", None
            return "ok", payload.get("data", {})
        except Exception as e:
            print(f"    ⚠️  Attempt {attempt}/{MAX_ATTEMPTS} failed for {appid}: {e}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(5 * attempt)

    return "error", None


def header_url_for(appid, game_data):
    header = game_data.get("header_image")
    if header:
        return header.split("?")[0]  # drop the cache-busting query string
    return f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg"


def load_previous():
    """Previous output, keyed by appid, used as a fallback when Steam hiccups."""
    try:
        with open(OUTPUT_PATH, encoding='utf-8') as f:
            return {entry["appid"]: entry for entry in json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return {}


def load_wishlist():
    rows = []
    try:
        with open(INPUT_PATH, newline='', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                appid = (row.get('appid') or '').strip()
                name = (row.get('name') or '').strip()
                if not appid or not name:
                    continue
                rows.append((appid, name))
    except FileNotFoundError:
        print(f"Error: {INPUT_PATH} not found.")
        raise SystemExit(1)
    return rows


def main():
    wishlist = load_wishlist()
    previous = load_previous()
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=MIN_DAYS_SINCE_RELEASE)

    results = []  # (release_date, entry)

    for appid, name in wishlist:
        print(f"Checking {name} ({appid})...")
        status, data = fetch_app_details(appid)

        if status == "error":
            if appid in previous:
                print("    ↩️  Steam lookup failed; keeping previous entry")
                prev = previous[appid]
                prev_date = parse_release_date(prev.get("released")) or cutoff
                results.append((prev_date, prev))
            else:
                print("    ❌ Steam lookup failed and no previous entry; skipping")
            time.sleep(REQUEST_DELAY)
            continue

        release_info = data.get("release_date", {})

        if release_info.get("coming_soon"):
            print("    ⏳ Coming soon")
        elif any(g.get("description") in EXCLUDED_GENRES for g in data.get("genres", [])):
            print("    ⏳ Early Access (ignored)")
        else:
            release_date = parse_release_date(release_info.get("date"))
            if release_date is None:
                print(f"    ⏳ No full release date ({release_info.get('date')!r})")
            elif release_date > cutoff:
                print(f"    ⏳ Released {release_date}, not yet a full day old")
            else:
                print(f"    ✅ Released {release_date}")
                keywords = make_keywords(name)
                results.append((release_date, {
                    "appid": appid,
                    "name": name,
                    "steamheader": header_url_for(appid, data),
                    "steamdburl": f"https://steamdb.info/app/{appid}/",
                    "rinurl": f"https://cs.rin.ru/forum/search.php?st=0&sk=t&sd=d&sr=topics&keywords={keywords}&terms=all&fid[]=10&sf=titleonly",
                    "released": release_date.isoformat(),
                }))

        time.sleep(REQUEST_DELAY)

    # Newest release first. Output is a list (not a dict keyed by appid) so the
    # browser can't reorder it: JS sorts integer-like object keys numerically.
    results.sort(key=lambda r: r[0], reverse=True)
    output = [entry for _, entry in results]

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Done! {len(output)} released game(s) from {len(wishlist)} on the wishlist.")


if __name__ == "__main__":
    main()
