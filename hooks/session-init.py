#!/usr/bin/env python3
# Session Init Hook (sessionStart)
# Cross-platform replacement for session-init.sh.
# Injects model-awareness context into every conversation.

import json
import sys

sys.stdin.read()  # consume and discard stdin

print(json.dumps({
    "additional_context": (
        "Model guidance: Haiku is ideal for git ops, renames, formatting, and simple edits. "
        "Sonnet is the default for feature work, debugging, and planning. "
        "Opus is for architecture decisions, deep analysis, and multi-system reasoning. "
        "If you notice the current task is simpler than the model being used, briefly mention it."
    )
}))
