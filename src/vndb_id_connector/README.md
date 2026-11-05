# VNDB ID Connector

## Usage

```bash
# Deploy containers
docker compose up -d
# Run script

```

## Matching

A VNDB VN and a Bangumi subject are linked only when the evidence agrees
(`modules/evidence.py`):

- **IDs**: the Bangumi infobox links to the VN on vndb.org, or both sides link the same
  Steam / ErogameScape / DLsite / Getchu / novelgame / freem page. VNDB links from
  releases shared by several VNs (bundles) are ignored.
- **Names** (`modules/matching.py`): a name counts only if exactly one VN and exactly one
  subject carry it, first compared with `normalize_string`, then ignoring punctuation.

A pair is published when nothing contradicts it and either two of the above agree, or it
has an exact match on a VN title with first release years at most one year apart and no
disagreeing developer/publisher. All other candidates are written to
`data/vndb_id_connector/review_queue.jsonl` (not committed) with the reason, so they can be
checked and moved to the manual lists below.

Steam apps are taken from VNDB (the VN and its releases) and are always published. Each
entry holds one VN with at most one Bangumi subject and one Steam app (`modules/output.py`):
a subject and an app share an entry when the subject links the app, or when it is the VN's
only subject and no other Bangumi subject links the app.

## Manual corrections

`data/vndb_id_connector/1_manually.json` is applied when the data is generated (`main.py`,
so blacklisted associations never end up in `2_automated.json` and the review queue only
contains undecided pairs) and again when the published dataset is built (`src/build_docs`,
so edits take effect without regenerating the data).

```json
{
  "whitelist": [
    {"vndb": "v210", "bangumi": "5916", "steam": "", "names": ["ひまわり"], "note": "issue #7"}
  ],
  "blacklist": [
    {"vndb": "v18840", "bangumi": "94278", "note": "same title, different game"}
  ]
}
```

- **whitelist**: at least two IDs plus a non-empty `names` list. The IDs are published as one
  entry; existing entries whose IDs are a subset of it are merged into it.
- **blacklist**: one ID removes that ID from the dataset; two or three IDs forbid every
  pairwise association between them. Entries containing a forbidden association are dropped.
- The blacklist has priority over the whitelist. `note` is optional and free-form.
