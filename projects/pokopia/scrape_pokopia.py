#!/usr/bin/env python3
"""
Pokopia Habitat data scraper.

Scrapes https://www.serebii.net/pokemonpokopia/ to produce:
  - data.json     (pokemon, categories, items)
  - icons/*.png   (one icon per unique item)
  - .cache/       (raw HTML / image cache so re-runs are fast)

USAGE (in Terminal):
    cd "/Users/danielapatricio/Documents/Claude/Projects/GithubPage/projects/pokopia"
    pip3 install --user requests beautifulsoup4
    python3 scrape_pokopia.py

The script is idempotent: re-running uses cached fetches. Delete .cache/ to
force a fresh crawl. Expect ~5-10 minutes on first run.

If something fails, copy the terminal output and share it back — the logs
identify exactly which page didn't parse so we can adjust the rules.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write(
        "\nMissing dependencies. Install them first:\n"
        "    pip3 install --user requests beautifulsoup4\n\n"
    )
    sys.exit(1)


# ---------- configuration ----------
BASE = "https://www.serebii.net"
POKOPIA = f"{BASE}/pokemonpokopia"

# Verified index URL (João confirmed). Keeping fallbacks in case the site moves.
POKEDEX_INDEX_CANDIDATES = [
    f"{POKOPIA}/availablepokemon.shtml",
    f"{POKOPIA}/pokedex.shtml",
    f"{POKOPIA}/pokemon.shtml",
    f"{POKOPIA}/",
    f"{POKOPIA}/index.shtml",
    f"{POKOPIA}/pokedex/index.shtml",
]

OUT_DIR = Path(__file__).resolve().parent
CACHE_DIR = OUT_DIR / ".cache"
ICONS_DIR = OUT_DIR / "icons"
POKE_DIR = ICONS_DIR / "pokemon"
DATA_JSON = OUT_DIR / "data.json"
DATA_JS = OUT_DIR / "data.js"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,image/*;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DELAY_SECONDS = 0.35  # be polite between requests

session = requests.Session()
session.headers.update(HEADERS)


# ---------- helpers ----------
def log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}", flush=True)


def cache_path(url: str, kind: str = "html") -> Path:
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{h}.{kind}"


def fetch_text(url: str, *, use_cache: bool = True) -> str:
    path = cache_path(url, "html")
    if use_cache and path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    time.sleep(DELAY_SECONDS)
    log("fetch", url)
    r = session.get(url, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding or "utf-8"
    text = r.text
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


def fetch_bytes(url: str, *, use_cache: bool = True) -> bytes:
    ext = Path(urlparse(url).path).suffix.lstrip(".") or "bin"
    path = cache_path(url, ext)
    if use_cache and path.exists():
        return path.read_bytes()
    time.sleep(DELAY_SECONDS)
    log("fetch", url)
    r = session.get(url, timeout=30)
    r.raise_for_status()
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_bytes(r.content)
    return r.content


def try_fetch_any(urls: list[str]) -> tuple[str | None, str | None]:
    """Return (html, url) for the first URL that works."""
    for u in urls:
        try:
            return fetch_text(u), u
        except requests.HTTPError as e:
            log("warn", f"{u}: {e}")
        except Exception as e:
            log("warn", f"{u}: {e}")
    return None, None


POKEDEX_RE = re.compile(r"/pokemonpokopia/pokedex/([a-z0-9\-.]+)\.shtml", re.I)
FAV_RE = re.compile(r"/pokemonpokopia/favorites/([a-z0-9\-.]+)\.shtml", re.I)


# ---------- pokemon enumeration ----------
def collect_pokemon_slugs() -> tuple[list[str], dict[str, str]]:
    """
    Return (sorted_slugs, pokopia_dex_map).

    pokopia_dex_map: slug -> zero-padded Pokopia dex number (e.g. "011" for Pidgeotto).
    Serebii's availablepokemon.shtml index table is the authoritative source:
    rows are `<tr><td>#NNN</td><td><a href=".../<slug>.shtml">...`.
    """
    slugs: set[str] = set()
    pokopia_dex: dict[str, str] = {}

    index_html, used_url = try_fetch_any(POKEDEX_INDEX_CANDIDATES)
    if index_html:
        # Plain slug scan (keeps fallback discovery working)
        for m in POKEDEX_RE.finditer(index_html):
            slugs.add(m.group(1).lower())

        # Pull the Pokopia dex number from each row in the index table.
        soup = BeautifulSoup(index_html, "html.parser")
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            m_num = re.match(r"\s*#(\d+)\s*$", tds[0].get_text(" ", strip=True))
            if not m_num:
                continue
            a = tds[1].find("a", href=re.compile(r"/pokemonpokopia/pokedex/"))
            if not a:
                continue
            m_slug = re.search(r"/pokemonpokopia/pokedex/([a-z0-9\-.]+)\.shtml", a["href"], re.I)
            if not m_slug:
                continue
            slug = m_slug.group(1).lower()
            slugs.add(slug)
            # Zero-pad to 3 digits; game has 300 Pokemon so 3 is enough.
            pokopia_dex[slug] = f"{int(m_num.group(1)):03d}"

        log(
            "info",
            f"Found {len(slugs)} pokemon slugs via {used_url} "
            f"({len(pokopia_dex)} with Pokopia dex #)",
        )

    if slugs:
        return sorted(slugs), pokopia_dex

    log("error", "No pokedex index found. Tried:")
    for u in POKEDEX_INDEX_CANDIDATES:
        log("error", f"  {u}")
    log("error", "Share this output so we can add the correct index URL.")
    sys.exit(2)


# ---------- pokemon page parsing ----------
HABITAT_LABELS = ["ideal habitat", "ideal home", "preferred habitat", "habitat"]


def parse_pokemon_page(slug: str) -> dict:
    url = f"{POKOPIA}/pokedex/{slug}.shtml"
    html = fetch_text(url)
    soup = BeautifulSoup(html, "html.parser")

    # ---- name + number ----
    name = None
    number = None
    title = soup.find("title")
    if title:
        t = title.get_text(" ", strip=True)
        # Format A: "Serebii.net Pokemon Pokopia - #004 Charmander"
        m = re.search(r"-\s*#(\d+)\s+([A-Za-z][A-Za-z0-9 '\-\.]+?)\s*$", t)
        if m:
            number = m.group(1)
            name = m.group(2).strip()
        else:
            # Format B: "Paldean Wooper - Poké Dex - Pokémon Pokopia"
            # Take the first " - "-separated segment as the display name.
            parts = re.split(r"\s+-\s+", t)
            if parts:
                candidate = parts[0].strip()
                if candidate and candidate.lower() not in ("pokémon pokopia", "pokemon pokopia", "poké dex", "poke dex"):
                    name = candidate
    if not name:
        name = slug.replace("-", " ").title()

    # ---- habitat ----
    # Strategy 1 (primary): the page has an <a href="/pokemonpokopia/pokedex/idealhabitat/<slug>.shtml">
    habitat = None
    habitat_link = soup.find("a", href=re.compile(r"/pokemonpokopia/pokedex/idealhabitat/", re.I))
    if habitat_link:
        habitat = habitat_link.get_text(" ", strip=True) or None
        if not habitat:
            m = re.search(r"/idealhabitat/([a-z0-9\-]+)\.shtml", habitat_link["href"], re.I)
            if m:
                habitat = m.group(1).replace("-", " ").title()

    # Strategy 2 (fallback): regex over whole text.
    if not habitat:
        text = soup.get_text(" ", strip=True)
        m = re.search(
            r"Ideal\s+Habitat[^A-Za-z]{0,20}([A-Za-z][A-Za-z ]{0,30})",
            text,
        )
        if m:
            cand = m.group(1).strip()
            # Avoid the common pitfall where "Favorites" sits adjacent.
            if cand.lower() not in ("favorites", "favorite", "specialty"):
                habitat = cand

    # ---- favorites ----
    fav_pairs: list[tuple[str, str]] = []
    for a in soup.find_all("a", href=True):
        m = FAV_RE.search(a["href"])
        if not m:
            continue
        fav_slug = m.group(1).lower()
        fav_name = a.get_text(" ", strip=True)
        if not fav_name:
            img = a.find("img")
            if img and img.get("alt"):
                fav_name = img["alt"].strip()
        if not fav_name:
            fav_name = fav_slug
        if not any(fs == fav_slug for fs, _ in fav_pairs):
            fav_pairs.append((fav_slug, fav_name))

    # ---- sprite ----
    # Match either "/pokemonpokopia/pokemon/<digits>.png" or
    # "/pokemonpokopia/pokemon/<digits>-<suffix>.png" (forms like "025-peakychu.png").
    sprite_url = None
    sprite_re = re.compile(r"/pokemonpokopia/pokemon/(\d+)(?:-[a-z0-9]+)?\.png$", re.I)
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        m = sprite_re.search(src)
        if m:
            sprite_url = urljoin(url, src)
            # Fallback: if the title didn't carry a number, use the one from the sprite filename.
            if not number:
                number = m.group(1)
            break

    return {
        "slug": slug,
        "name": name,
        "number": number,
        "habitat": habitat,
        "favorites": [fs for fs, _ in fav_pairs],
        "favorite_names": {fs: fn for fs, fn in fav_pairs},
        "sprite_url": sprite_url,
        "url": url,
    }


# ---------- favorites/category page parsing ----------
def parse_category_page(slug: str) -> dict:
    url = f"{POKOPIA}/favorites/{slug}.shtml"
    html = fetch_text(url)
    soup = BeautifulSoup(html, "html.parser")

    # ---- display name ----
    name = slug
    title = soup.find("title")
    if title:
        t = title.get_text(" ", strip=True)
        m = re.search(r"-\s*([A-Za-z0-9 '\-&]+)\s*$", t)
        if m:
            name = m.group(1).strip()

    # ---- items ----
    # Heuristic: find the table with the most item-like rows. The canonical
    # layout on serebii is a 4-column table: Picture | Name | Description | Category.
    # The "Category" column (Decoration / Toy / Relaxation / Road / blank) is
    # the item TYPE — distinct from the favourite-category page we're on.
    def header_index(table, label: str) -> int | None:
        rows = table.find_all("tr")
        if not rows:
            return None
        headers = [c.get_text(" ", strip=True).lower() for c in rows[0].find_all(["td", "th"])]
        if label.lower() in headers:
            return headers.index(label.lower())
        return None

    def extract_items_from_table(table) -> list[dict]:
        out: list[dict] = []
        seen_local: set[str] = set()
        type_idx = header_index(table, "Category")
        for row in table.find_all("tr"):
            img = row.find("img")
            if not img or not img.get("src"):
                continue
            src = img["src"].lower()
            if "pokopia" not in src:
                continue
            # skip pokemon sprites — items are not under /pokemon/
            if "/pokemon/" in src or "/pokedex/" in src:
                continue
            img_url = urljoin(url, img["src"])
            item_slug = Path(urlparse(img_url).path).stem.lower()
            item_slug = re.sub(r"[^a-z0-9\-_]", "", item_slug) or item_slug

            cells = row.find_all(["td", "th"])
            item_name = None
            for c in cells:
                if c.find("img"):
                    continue
                t = c.get_text(" ", strip=True)
                if t and 1 < len(t) < 80:
                    item_name = t
                    break
            if not item_name:
                for c in cells:
                    t = c.get_text(" ", strip=True)
                    if t and len(t) > 1:
                        item_name = t
                        break
            if not item_name:
                item_name = (img.get("alt") or "").strip() or item_slug

            # Item TYPE (column "Category"), if present
            item_type = None
            if type_idx is not None and type_idx < len(cells):
                item_type = cells[type_idx].get_text(" ", strip=True) or None

            if item_slug in seen_local:
                continue
            seen_local.add(item_slug)
            out.append(
                {
                    "slug": item_slug,
                    "name": item_name,
                    "icon_url": img_url,
                    "type": item_type,
                }
            )
        return out

    best_items: list[dict] = []
    for table in soup.find_all("table"):
        got = extract_items_from_table(table)
        if len(got) > len(best_items):
            best_items = got

    return {"slug": slug, "name": name, "items": best_items, "url": url}


# ---------- icon download ----------
def download_icon(item: dict) -> str | None:
    url = item["icon_url"]
    ext = Path(urlparse(url).path).suffix.lower() or ".png"
    if not ext.startswith("."):
        ext = "." + ext
    safe = re.sub(r"[^a-z0-9\-_\.]", "_", item["slug"].lower())
    dest = ICONS_DIR / f"{safe}{ext}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest.name
    try:
        data = fetch_bytes(url)
    except Exception as e:
        log("warn", f"icon fail {url}: {e}")
        return None
    ICONS_DIR.mkdir(exist_ok=True)
    dest.write_bytes(data)
    return dest.name


# ---------- main ----------
def main() -> None:
    log("info", f"Output directory: {OUT_DIR}")
    CACHE_DIR.mkdir(exist_ok=True)
    ICONS_DIR.mkdir(exist_ok=True)
    POKE_DIR.mkdir(exist_ok=True)

    # 1. Enumerate pokemon
    slugs, pokopia_dex = collect_pokemon_slugs()
    log("info", f"Pokemon to fetch: {len(slugs)}")

    pokemon: list[dict] = []
    sprite_queue: list[tuple[str, str]] = []  # (slug, url)
    fav_slugs: set[str] = set()
    fav_name_hints: dict[str, str] = {}
    missing_habitat: list[str] = []
    missing_favorites: list[str] = []
    missing_sprite: list[str] = []

    for i, s in enumerate(slugs, 1):
        try:
            info = parse_pokemon_page(s)
        except Exception as e:
            log("warn", f"pokemon {s}: {e}")
            continue
        # Prefer the Pokopia dex number from the index table; fall back to whatever
        # we could parse from the detail page (title prefix or sprite filename).
        pokopia_number = pokopia_dex.get(info["slug"]) or info["number"]
        pokemon.append(
            {
                "slug": info["slug"],
                "name": info["name"],
                "number": pokopia_number,
                "habitat": info["habitat"],
                "favorites": info["favorites"],
                "sprite": None,  # will be filled after download
                "url": info["url"],
            }
        )
        if not info["habitat"]:
            missing_habitat.append(s)
        if not info["favorites"]:
            missing_favorites.append(s)
        if info["sprite_url"]:
            sprite_queue.append((info["slug"], info["sprite_url"]))
        else:
            missing_sprite.append(s)
        for fs, fn in info["favorite_names"].items():
            fav_slugs.add(fs)
            fav_name_hints.setdefault(fs, fn)
        if i % 25 == 0 or i == len(slugs):
            log("progress", f"pokemon {i}/{len(slugs)}")

    # 1b. Download sprites
    log("info", f"Downloading {len(sprite_queue)} Pokemon sprites")
    sprite_by_slug: dict[str, str] = {}
    for i, (s, url) in enumerate(sprite_queue, 1):
        ext = Path(urlparse(url).path).suffix.lower() or ".png"
        safe = re.sub(r"[^a-z0-9\-_.]", "_", s.lower())
        dest = POKE_DIR / f"{safe}{ext}"
        rel = f"icons/pokemon/{safe}{ext}"
        if dest.exists() and dest.stat().st_size > 0:
            sprite_by_slug[s] = rel
        else:
            try:
                data = fetch_bytes(url)
            except Exception as e:
                log("warn", f"sprite fail {s}: {e}")
                missing_sprite.append(s)
                continue
            dest.write_bytes(data)
            sprite_by_slug[s] = rel
        if i % 50 == 0 or i == len(sprite_queue):
            log("progress", f"sprites {i}/{len(sprite_queue)}")

    for p in pokemon:
        p["sprite"] = sprite_by_slug.get(p["slug"])

    if missing_habitat:
        log("warn", f"No habitat detected for {len(missing_habitat)} pokemon (showing up to 10): {missing_habitat[:10]}")
    if missing_favorites:
        log("warn", f"No favorites detected for {len(missing_favorites)} pokemon (showing up to 10): {missing_favorites[:10]}")

    log("info", f"Unique favorite categories: {len(fav_slugs)}")

    # 2. Fetch each category
    categories: list[dict] = []
    all_items: dict[str, dict] = {}
    for i, s in enumerate(sorted(fav_slugs), 1):
        try:
            cat = parse_category_page(s)
        except Exception as e:
            log("warn", f"category {s}: {e}")
            continue
        cat_name = cat["name"]
        if (not cat_name) or cat_name.strip().lower() == s:
            cat_name = fav_name_hints.get(s, cat_name or s)
        categories.append(
            {
                "slug": cat["slug"],
                "name": cat_name,
                "items": [it["slug"] for it in cat["items"]],
                "url": cat["url"],
            }
        )
        for it in cat["items"]:
            existing = all_items.get(it["slug"])
            if existing:
                if s not in existing["categories"]:
                    existing["categories"].append(s)
                # Keep the first non-empty type we encounter across pages
                if not existing.get("type") and it.get("type"):
                    existing["type"] = it["type"]
            else:
                all_items[it["slug"]] = {
                    "slug": it["slug"],
                    "name": it["name"],
                    "icon_url": it["icon_url"],
                    "type": it.get("type"),
                    "categories": [s],
                }
        if i % 10 == 0 or i == len(fav_slugs):
            log("progress", f"categories {i}/{len(fav_slugs)}")

    # 3. Download icons
    log("info", f"Downloading {len(all_items)} icons")
    for i, it in enumerate(all_items.values(), 1):
        local = download_icon(it)
        it["icon"] = f"icons/{local}" if local else None
        if i % 50 == 0 or i == len(all_items):
            log("progress", f"icons {i}/{len(all_items)}")

    # 4. Finalize items
    items_out = []
    for it in all_items.values():
        items_out.append(
            {
                "slug": it["slug"],
                "name": it["name"],
                "icon": it["icon"],
                "type": it.get("type"),
                "categories": sorted(set(it["categories"])),
            }
        )
    items_out.sort(key=lambda x: (x["name"].lower(), x["slug"]))

    # 5. Write data.json
    data = {
        "source": "https://www.serebii.net/pokemonpokopia/",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pokemon": sorted(pokemon, key=lambda x: x["name"].lower()),
        "categories": sorted(categories, key=lambda x: x["name"].lower()),
        "items": items_out,
    }
    DATA_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    # Also write data.js so the HTML app can read it via <script> (file:// blocks fetch).
    DATA_JS.write_text(
        "window.POKOPIA_DATA = " + json.dumps(data, ensure_ascii=False) + ";",
        encoding="utf-8",
    )
    log("done", f"Wrote {DATA_JSON}")
    log("done", f"Wrote {DATA_JS}")
    log("done", f"Pokemon: {len(pokemon)}   Categories: {len(categories)}   Items: {len(items_out)}")
    log("done", "Next step: tell Claude the scraper finished so we can build the app.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("info", "Interrupted by user")
        sys.exit(130)
