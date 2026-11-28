# Game Detection Rules

## Usage

```bash
# Validate source files, schema and conformance cases
make check-game-detection

# Scan a directory with the stdlib-only reference interpreter
python3 src/game_detection_rules/scanner.py /path/to/games
```

`scanner.py --rules` accepts either `data/game_detection_rules` (default) or a compiled `game_detection_rules.json`. `python3 src/game_detection_rules/rules.py` prints the assembled JSON.

## Evaluation

`scanner.py` is the reference implementation of the rule language:

- **Traversal**: Visit the root directory first, list entries in UTF-16 code unit order while preserving original spelling, and skip symlinks and Windows reparse points. An identified directory claims its subtree; otherwise descend into subdirectories not matching `traversal.skipDirectories`. Unreadable subdirectories are recorded in `unreadable`.
- **Store manifests** (`storeManifests`): Tried in order across two modes. Directory-local `gog-galaxy-info` matches a directory containing a single valid `goggame-<id>.info` whose numeric `gameId` equals `rootGameId` and whose primary `FileTask` paths exist inside that directory. Library-level `steam-acf` matches `appmanifest_<id>.acf` VDF `"AppState"` files at a library directory (skipping its `skipDirectories` and `ignore` AppIDs) and binds each single-segment `installdir` under `appsDir` when that target directory yields entries (from a matching engine layout, or else the manifest's `entries` tiers filtered by `ignoreEntries` and `traversal.skipDirectories`); ambiguous manifests targeting the same directory supply no store identity, and `titleFile` / `signals` are relative to the game `root`.
- **Engines** (`engines`): Engines and their `layouts` are tried in order; the first matching layout wins. Every probe in `anchors` must match. Entry tiers in `entries` are evaluated in order: filter out `defaults.ignoreEntries` and `engine.ignoreEntries`, bind `{stem}` (entry basename without its final extension) and any `{project}` directory segment, and keep entries for which all `companions` match. The first tier with survivors supplies `entries`. When both a store manifest and an engine layout match, the store supplies identity and title (plus `entries` when the manifest defines explicit tasks), while the layout supplies `engine`, `rule` (`<engine>/<layout>`), and `signals`.
- **Probes**: `/`-separated relative paths with case-insensitive `*` and `?` segment globs; a trailing `/` matches directories, otherwise files. Bound `{stem}` and `{project}` segments match literally (case-insensitive). `extension: "none"` matches basenames with no dot, `magic` checks hex bytes at `offset` (default `0`), and `any` records its first matching branch. `signals` lists the first matched path per probe (anchors before companions), deduplicated in order.
- **Titles and hints**: `layout.titles` are tried in order (`line` 1-based, `json` RFC 6901 string pointer, `ini` case-insensitive section and key, `html-title` `<title>` within the first 64 KiB of UTF-8 HTML); `{stem}` in title paths requires all surviving entries to share one case-insensitive stem. Otherwise use that stem (stripping the first matching `stripStemSuffixes`) unless listed in `genericStems`, falling back to the directory name. `hints` run after detection (`uint-line` reads a positive uint32 from line 1, strips leading zeros, and skips `ignore`), keeping the first value per `provider` other than a confirmed `store`. Unknown `kind`s in manifests, titles, or hints are skipped locally.

## Source files

`data/game_detection_rules/` splits rules by concern and is assembled by `rules.py` when `src/build_docs` builds `docs/game_detection_rules.json` (validated against `docs/schemas/game_detection_rules_schema.json` by `check.py`):

- **base.json**: shared `traversal` and `defaults`.
- **stores/*.json**: per-store `storeManifests` and `hints` (e.g. `gog.json`, `steam.json`), plus optional store-scoped `traversal` and `defaults`.
- **engines/*.json**: one `engine` definition per file (`id`, `name`, `layouts`, and optional engine-scoped filters).
- **extensions/*.json**: non-store, non-engine `hints` and supplementary `traversal` or `defaults` filters.

Files within each directory are merged in UTF-8 filename order, deduplicating global filter lists while preserving order. `cases.json` holds portable conformance fixtures (virtual file trees mapped to UTF-8 strings or `hex:` bytes, with optional per-case `rules` overrides); add a positive case and a counterexample when introducing a layout.
