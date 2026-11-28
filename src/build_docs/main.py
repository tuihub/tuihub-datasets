import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR / "vndb_id_connector"))
sys.path.insert(0, str(SRC_DIR / "game_detection_rules"))

from modules.manual import ManualLists  # noqa: E402
from rules import build_rules  # noqa: E402

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
    # game_detection_rules
    game_detection_rules = build_rules("../../data/game_detection_rules")
    with open("../../docs/game_detection_rules.json", "w", encoding="utf8") as f3:
        f3.writelines(
            json.dumps(
                game_detection_rules,
                ensure_ascii=False,
                indent=None,
                separators=(",", ":"),
            )
        )
