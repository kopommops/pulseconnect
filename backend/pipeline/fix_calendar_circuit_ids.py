"""One-off repair: backfills circuit_id into an already-generated
race_calendar.json without touching FastF1 — circuit_id is derived
locally from event_name, which is already saved. Safe to run any time,
only ever fills in a missing field."""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import GENERATED_DIR, circuit_id_for_event

path = os.path.join(GENERATED_DIR, "race_calendar.json")
with open(path) as f:
    calendar = json.load(f)

fixed, missing = 0, []
for season, events in calendar.items():
    if season == "source":
        continue
    for ev in events:
        if not ev.get("circuit_id"):
            cid = circuit_id_for_event(ev["event_name"])
            if cid:
                ev["circuit_id"] = cid
                fixed += 1
            else:
                missing.append(f"{season} round {ev.get('round')}: {ev.get('event_name')}")

with open(path, "w") as f:
    json.dump(calendar, f, indent=2)

print(f"Fixed {fixed} calendar entries.")
if missing:
    print("Unresolved (no match in EVENT_NAME_TO_CIRCUIT) — check config.py:")
    for m in missing:
        print(" ", m)