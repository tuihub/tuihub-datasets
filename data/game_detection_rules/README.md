# Game detection rules

规则用于本地目录识别。对外发布的 `game_detection_rules.json` 供客户端加载或随应用分发。维护者同时更新 Schema 和共享样本，Python 参考解释器和下游原生实现使用相同的样本核对结果。集中式商店库清单由宿主提供。规则中的 `storeManifests` 只读取游戏目录中的商品安装信息，扫描可全程离线。

The runtime data is [game_detection_rules.json](game_detection_rules.json). The [authoring schema](game_detection_rules.schema.json), [conformance cases](game_detection_cases.json) and [Python reference scanner](../../src/game_detection/scanner.py) live in this repository. Pages copies only the runtime data to the site root. The reference scanner reads directories and byte ranges using the Python standard library.

## Execution

1. Visit the chosen root first. Enumerate children in ordinal UTF-16 name order, preserve original spelling in results and skip symbolic links. An identified directory claims its subtree. Otherwise descend into directories whose names do not match a traversal skip pattern. A host may also skip OS virtual filesystems. Report unreadable subtrees separately. A failed root scan cannot establish which prior installations disappeared.
2. Consult the host's registered store catalog, then the ordered directory-local `storeManifests`. The `gog-galaxy-info` reader checks that the numeric game ID, base game ID and filename identify one product and that a primary file task exists under the installation. A copied DLC receipt or ambiguous set of base receipts supplies no identity. Corrupt JSON invalidates that manifest. Steam's external ACF catalogs belong to the host. No store login is involved.
3. Evaluate engines and their layouts in declaration order. All fixed anchors must match. For each entry tier, discard ignored names and require every companion to match for that particular entry. The first tier with survivors supplies all its candidate files; the first successful layout wins. Engine filters extend the defaults. A store match takes precedence for title, identity and entry points, while a matching layout can add engine information and evidence.
4. Paths are relative, separated by `/`. Each segment supports case-insensitive `*` and `?` matching. A trailing slash denotes a directory; otherwise the probe requires a file. A probe's `any` tests alternatives in order and records its first hit. Hexadecimal `magic` matches bytes at `offset` (default zero). `extension: "none"` matches names with no dot. In companion paths, `{stem}` expands to the current entry's basename without its final extension. The optional whole entry segment `{project}` captures a directory name, so an Unreal resource pack and executable must belong to the same project. Bound segments are matched literally. Signals list the first matching path per probe, anchors before companions, with duplicates removed.
5. Try title readers in order. `json` uses a JSON Pointer to a string, `line` is one-based, `ini` uses case-insensitive section and key names, and `html-title` reads a complete title tag within the first 64 KiB of UTF-8 HTML. Malformed or empty titles fall through. Title paths may use `{stem}` when all surviving entries share a stem. Then try the distinct stem with its first matching build suffix removed; a generic or ambiguous stem falls back to the directory name.
6. After identifying a root, try hints in order. `uint-line` reads a positive decimal unsigned 32-bit ID from the first line, normalizes leading zeros and skips ignored IDs. The first usable value per provider wins. A hint supplies neither proof of ownership nor a confirmed store ID. Skip an unknown manifest, title or hint kind locally; the other extractors still apply.

Each conformance case names a root directory, maps relative filenames to UTF-8 contents (or `hex:` bytes), and declares ordered observations with relative paths. A case may supply a complete `rules` object to exercise the language independently of the shipping catalog. Rule IDs have the form `engine-id/layout-id`. The reference CLI prints the games and any unreadable subtrees as UTF-8 JSON.

## Maintenance

From the repository root:

```sh
python3 -m pip install -r requirements.txt
make check-game-detection
python3 src/game_detection/scanner.py /path/to/games
```

Edit the rules and add a positive case and a useful counterexample when introducing a layout. The test command validates the schema and runs the cases against an in-memory directory tree. Cross-language clients can materialize the same tree on disk. These fixtures measure agreement on specific inputs; estimating real-world coverage requires independently labeled releases and non-game directories.
