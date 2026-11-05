import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vndb_id_connector"))

from modules.manual import ManualLists  # noqa: E402

if __name__ == "__main__":
    # vndb_id_connector
    manual = ManualLists.load("../../data/vndb_id_connector/1_manually.json")
    with open("../../data/vndb_id_connector/2_automated.json", encoding="utf8") as f:
        vndb_data = json.load(f)
    merged_data = {
        "info": vndb_data["info"],
        "entries": manual.apply(vndb_data["entries"]),
    }
    with open("../../docs/vndb_id_connector.json", "w", encoding="utf8") as f3:
        f3.writelines(
            json.dumps(
                merged_data, ensure_ascii=False, indent=None, separators=(",", ":")
            )
        )
    # game_id_list
    f = open("../../data/game_id_list/1_automated.json", encoding="utf8")
    game_id_list_data = json.load(f)
    with open("../../docs/game_id_list.json", "w", encoding="utf8") as f3:
        f3.writelines(
            json.dumps(
                game_id_list_data,
                ensure_ascii=False,
                indent=None,
                separators=(",", ":"),
            )
        )
