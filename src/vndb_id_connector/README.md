# VNDB ID Connector

## Usage

```bash
# Deploy containers
docker compose up -d
# Run script

```

## Manual corrections

`data/vndb_id_connector/1_manually.json` is applied on top of the generated data when the
published dataset is built (`src/build_docs`).

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
