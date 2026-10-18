import json
import sys
import os
from datetime import datetime, timezone

def load(path):
    try:
        with open(path) as f:
            content = f.read().strip()
        if not content or content == "null":
            return None
        return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"WARN: JSON invalid a {path}: {e}", file=sys.stderr)
        return None

start = sys.argv[1] if len(sys.argv) > 1 else ""
end   = sys.argv[2] if len(sys.argv) > 2 else ""

data = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "period": {"start": start, "end": end},
    "hits_data":  load("/tmp/hits.json"),
    "browsers":   load("/tmp/browsers.json"),
    "systems":    load("/tmp/systems.json"),
    "sizes":      load("/tmp/sizes.json"),
    "locations":  load("/tmp/locations.json"),
}

with open("/tmp/raw_all.json", "w") as f:
    json.dump(data, f, indent=2)

print("JSON generat correctament")