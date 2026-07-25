# Pokopia Habitat Planner

A single-page tool for planning shared habitats in *Pokémon Pokopia*. Pick up to four Pokémon, and the app shows every item they all care about — ranked by how many of the residents share each favourite — so you can decorate the habitat to make the whole roster happy.

[Open the live app](https://jd-andradex.github.io/projects/pokopia/) · [Read the case study](https://jd-andradex.github.io/projects/pokopia-habitat.html)

## What's in this folder

| File / dir | Purpose |
| --- | --- |
| `index.html` | The app. Single file: HTML + inline CSS + vanilla JS. No build step. |
| `data.js` | Runtime data — wraps a JSON blob as `window.POKOPIA_DATA`. Loaded by `index.html`. |
| `icons/` | Local copy of Pokémon sprites and item icons referenced by `data.js`. |
| `scrape_pokopia.py` | Python scraper that produces `data.js` + `icons/` from serebii.net. |

## Running the app locally

It's static — open `index.html` in a browser, or serve the folder:

```bash
cd projects/pokopia
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Regenerating the data

The data comes from [serebii.net/pokemonpokopia](https://www.serebii.net/pokemonpokopia/). To refresh it:

```bash
cd projects/pokopia
pip3 install --user requests beautifulsoup4
python3 scrape_pokopia.py
```

The scraper writes `data.json`, `data.js`, and `icons/` next to itself, plus a `.cache/` directory of raw HTML / image responses. Re-runs are idempotent — cached pages aren't re-fetched. Delete `.cache/` to force a fresh crawl. Expect ~5–10 minutes on a first run; subsequent runs finish in seconds.

`.cache/`, `__pycache__/`, and `data.json` are gitignored. Only `data.js` is committed (it's what the app actually loads).

## Data model

`window.POKOPIA_DATA` is `{ pokemon, categories, items }`:

- **pokemon** — 307 entries with `slug`, `name`, `number` (Pokopia Dex, sequential), `sprite` (relative path), and `favorites` (array of category slugs).
- **categories** — 43 favourite-category groups, e.g. *Pillow*, *Ball*, *Wagon*.
- **items** — 607 items with `slug`, `name`, `icon` (relative path), `categories` (which categories they belong to), and an optional `type` (*Decoration*, *Toy*, *Relaxation*, *Road*, or untagged).

## How the suggestion logic works

The app cross-references each item's category list against the union of every roster member's favourites, then ranks items by how many roster members share that favourite. A four-Pokémon roster typically surfaces a few "everyone likes this" items, a wider band of three-out-of-four matches, and a long tail of single-resident picks — so you can prioritise high-overlap items when planning the habitat.

## Stack

HTML / vanilla JS / CSS, no frameworks · Python 3 (`requests` + `BeautifulSoup`) for scraping · serebii.net as the upstream data source.
