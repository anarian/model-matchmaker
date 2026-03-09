#!/usr/bin/env python3
# Model Advisor Hook (beforeSubmitPrompt)
# Cross-platform replacement for model-advisor.sh.
# Step-down: block + recommend Haiku/Sonnet when overpaying.
# Step-up: block + recommend Opus when on Sonnet/Haiku for complex tasks.
# Override: prefix prompt with "!" to bypass entirely.

import json
import sys
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"continue": True}))
        return

    prompt = data.get("prompt", "")
    model = data.get("model", "").lower()
    conversation_id = data.get("conversation_id", "")
    generation_id = data.get("generation_id", "")

    is_override = prompt.lstrip().startswith("!")

    if is_override:
        clean_prompt = prompt.lstrip()[1:].lstrip()
    else:
        clean_prompt = prompt

    prompt_lower = clean_prompt.lower()
    word_count = len(clean_prompt.split())

    is_opus = "opus" in model
    is_sonnet = "sonnet" in model
    is_haiku = "haiku" in model

    if not (is_opus or is_sonnet or is_haiku):
        print(json.dumps({"continue": True}))
        return

    opus_keywords = [
        "architect", "architecture", "evaluate", "tradeoff", "trade-off",
        "strategy", "strategic", "compare approaches", "why does", "deep dive",
        "redesign", "across the codebase", "investor", "multi-system",
        "complex refactor", "analyze", "analysis", "plan mode", "rethink",
        "high-stakes", "critical decision"
    ]

    has_opus_signal = any(kw in prompt_lower for kw in opus_keywords)
    is_long_analytical = word_count > 100 and "?" in clean_prompt
    is_multi_paragraph = word_count > 200

    if has_opus_signal or is_long_analytical or is_multi_paragraph:
        recommendation = "opus"
    else:
        haiku_patterns = [
            r"\bgit\s+(commit|push|pull|status|log|diff|add|stash|branch|merge|rebase|checkout)\b",
            r"\bcommit\b.*\b(change|push|all)\b", r"\bpush\s+(to|the|remote|origin)\b",
            r"\brename\b", r"\bre-?order\b", r"\bmove\s+file\b", r"\bdelete\s+file\b",
            r"\badd\s+(import|route|link)\b", r"\bformat\b", r"\blint\b",
            r"\bprettier\b", r"\beslint\b", r"\bremove\s+(unused|dead)\b",
            r"\bupdate\s+(version|package)\b"
        ]
        is_haiku_task = word_count < 60 and any(re.search(p, prompt_lower) for p in haiku_patterns)

        sonnet_patterns = [
            r"\bbuild\b", r"\bimplement\b", r"\bcreate\b", r"\bfix\b", r"\bdebug\b",
            r"\badd\s+feature\b", r"\bwrite\b", r"\bcomponent\b", r"\bservice\b",
            r"\bpage\b", r"\bdeploy\b", r"\btest\b", r"\bupdate\b", r"\brefactor\b",
            r"\bstyle\b", r"\bcss\b", r"\broute\b", r"\bapi\b", r"\bfunction\b"
        ]
        is_sonnet_task = any(re.search(p, prompt_lower) for p in sonnet_patterns)

        if is_haiku_task:
            recommendation = "haiku"
        elif is_sonnet_task:
            recommendation = "sonnet"
        else:
            recommendation = None

    block = False
    message = ""

    if not is_override:
        if recommendation == "haiku" and (is_opus or is_sonnet):
            block = True
            if is_opus:
                message = "This looks like a simple mechanical task (git, rename, format). Haiku handles these identically at ~90% less cost than Opus. Switch to Haiku and re-send. (Prefix with ! to override.)"
            else:
                message = "This looks like a simple mechanical task. Haiku handles these identically at ~80% less cost than Sonnet. Switch to Haiku and re-send. (Prefix with ! to override.)"
        elif recommendation == "sonnet" and is_opus:
            block = True
            message = "Standard implementation work. Sonnet handles this at ~80% less cost with the same quality. Switch to Sonnet and re-send. (Prefix with ! to override.)"
        elif recommendation == "opus" and (is_sonnet or is_haiku):
            block = True
            message = "This looks like architecture, deep analysis, or multi-system work. Switch to Opus for better results, then re-send. (Prefix with ! to override.)"

    rec = recommendation if recommendation else "uncertain"
    action = "OVERRIDE" if is_override else ("BLOCK" if block else "ALLOW")

    try:
        hook_dir = Path.home() / ".cursor" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        log_path = hook_dir / "model-matchmaker.ndjson"
        snippet = clean_prompt[:40].replace(chr(10), " ").replace(chr(34), chr(39))
        entry = {
            "event": "recommendation",
            "ts": datetime.now().isoformat(),
            "conversation_id": conversation_id,
            "generation_id": generation_id,
            "model": model,
            "recommendation": rec,
            "action": action,
            "word_count": word_count,
            "prompt_snippet": snippet,
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        if block:
            state_path = hook_dir / ".last-block-state.json"
            block_state = {
                "conversation_id": conversation_id,
                "generation_id": generation_id,
                "blocked_model": model,
                "recommended_model": rec,
                "block_ts": datetime.now().isoformat(),
            }
            with open(state_path, "w") as f:
                json.dump(block_state, f)

            auto_switch_flag = hook_dir / ".auto-switch-enabled"
            if auto_switch_flag.exists():
                try:
                    if sys.platform == "win32":
                        switch_script = hook_dir / "auto-switch-model.ps1"
                        if switch_script.exists():
                            subprocess.Popen(
                                ["powershell", "-WindowStyle", "Hidden",
                                 "-NonInteractive", "-File", str(switch_script), rec],
                                start_new_session=True,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                    else:
                        switch_script = hook_dir / "auto-switch-model.sh"
                        if switch_script.exists():
                            subprocess.Popen(
                                ["bash", str(switch_script), rec],
                                start_new_session=True,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                except Exception:
                    pass
    except Exception:
        pass

    if is_override:
        print(json.dumps({"continue": True}))
    elif block:
        print(json.dumps({"continue": False, "user_message": message}))
    else:
        out = {"continue": True}
        if message:
            out["user_message"] = message
        print(json.dumps(out))


try:
    main()
except Exception:
    print(json.dumps({"continue": True}))
