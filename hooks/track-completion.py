#!/usr/bin/env python3
# Track Completion Hook (stop)
# Cross-platform replacement for track-completion.sh.
# Logs task outcome when the agent loop ends, enabling accuracy analysis
# by correlating with the model recommendation from beforeSubmitPrompt.

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    print("{}")
    sys.exit(0)

status = data.get("status", "unknown")
loop_count = data.get("loop_count", 0)
conversation_id = data.get("conversation_id", "")
generation_id = data.get("generation_id", "")
model = data.get("model", "").lower()

try:
    hook_dir = Path.home() / ".cursor" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    log_path = hook_dir / "model-matchmaker.ndjson"
    entry = {
        "event": "completion",
        "ts": datetime.now().isoformat(),
        "conversation_id": conversation_id,
        "generation_id": generation_id,
        "model": model,
        "status": status,
        "loop_count": loop_count,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
except Exception:
    pass

print("{}")
