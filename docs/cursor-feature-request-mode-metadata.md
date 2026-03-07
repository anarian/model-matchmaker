# Feature Request: Add Mode and Model Metadata to Hook Payloads

## Summary

Add `mode` and `current_model_display_name` fields to hook payloads (especially `beforeSubmitPrompt`) to enable mode-aware tooling without UI scraping workarounds.

## Problem

Model Matchmaker is a local hook that helps users avoid overpaying for simple tasks (git commits on Opus) and underpowering complex tasks (architecture questions on Haiku). It works by classifying prompts and recommending the right model.

**Current limitation:** Cursor has different modes (Agent, Plan, Debug, Ask) with different model availability:
- **Plan mode**: Haiku is unavailable (grayed out)
- **Agent/Debug/Ask modes**: All models available

The hook receives `model` (e.g., `"claude-4.6-opus-high"`) but not:
1. Which **mode** the user is in
2. Which models are **available** in that mode

This forces workarounds:
- Manual mode logging: `~/.cursor/hooks/log-cursor-mode.sh plan`
- UI scraping via AppleScript to detect mode
- Hardcoded dropdown positions per mode for keyboard automation

## Proposed Solution

### Add to `beforeSubmitPrompt` payload:

```json
{
  "prompt": "...",
  "model": "claude-4.6-opus-high",
  "mode": "plan",  // NEW: "agent" | "plan" | "debug" | "ask"
  "model_display_name": "Opus",  // NEW: Human-readable name
  "available_models": ["opus", "sonnet"],  // NEW: Models available in current mode
  "conversation_id": "...",
  "generation_id": "..."
}
```

### Benefits

1. **Mode-aware recommendations** — Hook can say "Switch to Agent mode for Haiku" instead of "Switch to Haiku" (which fails in Plan mode)
2. **No UI scraping** — No need for AppleScript hacks to detect mode
3. **No manual logging** — Mode is known automatically
4. **Better user experience** — Recommendations are always actionable
5. **Enables auto-mode switching** — Hook could auto-switch mode when needed (with user permission)

### Use Cases

**Example 1: Haiku in Plan Mode**
```
User in Plan mode asks: "git commit these changes"
Hook sees: mode="plan", model="opus", available_models=["opus","sonnet"]
Hook recommends: "Switch to Agent mode for cheaper Haiku, or use Sonnet"
```

**Example 2: Mode-Aware Routing**
```
User in Plan mode asks architectural question
Hook sees: mode="plan" (designed for planning)
Hook says: "Plan mode is perfect for this, continue with current model"
```

**Example 3: Auto-Mode Switching**
```
User in Plan mode asks simple git commit question
Hook sees: mode="plan", optimal_model="haiku", available=false
Hook could: Auto-switch to Agent mode, then to Haiku
```

## Implementation Details

### Minimal Addition

Just the `mode` field would be sufficient:
```json
{
  "mode": "plan" | "agent" | "debug" | "ask"
}
```

Hooks can infer availability from mode (Plan=no Haiku, others=all models).

### Optional Enhancements

- `model_display_name`: "Opus" instead of "claude-4.6-opus-high" (easier for user messages)
- `available_models`: Explicit list of what's selectable in current mode
- `mode_display_name`: "Plan Mode" for user-facing messages

## Why This Matters

Model Matchmaker has proven demand:
- Saves 50-70% on cloud API costs (retroactive analysis)
- 3-5x speed improvement for simple tasks
- Used by teams to enforce cost-aware model selection

But the current implementation requires:
- 3 workaround scripts (`log-cursor-mode.sh`, `auto-switch-model.sh`, UI detection)
- Manual mode tracking by users
- Fragile keyboard automation that breaks on UI changes

Adding `mode` to hooks would make these tools **just work** without hacks.

## Related Work

- Model Matchmaker: https://github.com/coyvalyss1/model-matchmaker
- Auto-switch implementation: Uses keyboard automation via AppleScript
- GitHub Issue #7: Auto-mode switching investigation

## Alternatives Considered

1. **UI scraping** (current workaround) — Fragile, requires Accessibility permissions, breaks on UI changes
2. **Manual logging** (current workaround) — Requires user to remember to log mode changes
3. **Mode detection heuristics** — Unreliable, can't distinguish modes with same model availability

None are as clean as first-class metadata in the hook payload.

## Backward Compatibility

Adding optional fields to hook payloads is backward compatible. Existing hooks ignore unknown fields.

## Request

Please add `mode` (and optionally `model_display_name` and `available_models`) to hook payloads, especially `beforeSubmitPrompt`. This would enable robust mode-aware tooling without fragile workarounds.

---

**Contact:** @coybyron (GitHub), Model Matchmaker maintainer
