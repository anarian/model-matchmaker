# Feature Request: Add Mode and Model Metadata to Hook Payloads

**Category:** Hooks API Enhancement  
**Use Case:** Mode-aware tooling (Model Matchmaker, cost optimization, workflow automation)

## Summary

Add `mode` and `model_display_name` fields to hook payloads (especially `beforeSubmitPrompt`) to enable mode-aware recommendations without UI scraping workarounds.

---

## The Problem

I built [Model Matchmaker](https://github.com/coyvalyss1/model-matchmaker), a hook that helps avoid overpaying for simple tasks (git commits on Opus) and underpowering complex work (architecture on Haiku). It classifies prompts and recommends the right model.

**Current blocker:** Cursor modes (Agent/Plan/Debug/Ask) have different model availability:
- Plan mode: Haiku unavailable (grayed out)
- Other modes: All models available

The hook receives `model: "claude-4.6-opus-high"` but NOT:
- Which **mode** the user is in
- Which models are **available** in that mode

This forces workarounds:
- ❌ Manual mode logging (`~/.cursor/hooks/log-cursor-mode.sh plan`)
- ❌ UI scraping via AppleScript to detect mode
- ❌ Hardcoded dropdown positions per mode

---

## Proposed Solution

Add to `beforeSubmitPrompt` payload:

```json
{
  "prompt": "git commit these changes",
  "model": "claude-4.6-opus-high",
  "mode": "plan",  // NEW: "agent" | "plan" | "debug" | "ask"
  "model_display_name": "Opus",  // NEW: Human-readable name
  "available_models": ["opus", "sonnet"],  // NEW: What's selectable
  "conversation_id": "...",
  "generation_id": "..."
}
```

### Why This Matters

**With mode metadata, hooks can:**
1. Give actionable recommendations ("Switch to Agent mode for Haiku" vs "Switch to Haiku" which fails in Plan)
2. Auto-switch modes when appropriate (e.g., Plan→Agent for simple tasks)
3. Adapt routing logic per mode (Plan is designed for planning, so architectural questions should stay)

**Example:**
```
User in Plan mode: "git commit these changes"
Hook sees: mode="plan", model="opus", haiku not available
Hook recommends: "Switch to Agent mode for Haiku (90% cheaper)"
OR auto-switches if enabled: Plan→Agent, Opus→Haiku
```

---

## Real-World Impact

Model Matchmaker has proven demand:
- ✅ 50-70% reduction in cloud API costs
- ✅ 3-5x faster responses for simple tasks
- ✅ Used by teams for cost-aware model selection

But it currently requires 3 workaround scripts and fragile UI automation.

Adding `mode` to hooks would make it **just work**.

---

## Minimal Implementation

Just the `mode` field would be sufficient:
```json
{ "mode": "plan" | "agent" | "debug" | "ask" }
```

Hooks can infer model availability from mode.

Optional nice-to-haves:
- `model_display_name`: "Opus" (better for user messages)
- `available_models`: Explicit list of what's selectable

---

## Backward Compatibility

✅ Adding optional fields to hook payloads is backward compatible. Existing hooks ignore unknown fields.

---

## Alternatives Considered

1. **UI scraping** — Fragile, breaks on UI changes, requires Accessibility permissions
2. **Manual logging** — Users forget, breaks the flow
3. **Heuristics** — Can't reliably distinguish modes

None are as robust as first-class metadata.

---

## Related

- Model Matchmaker repo: https://github.com/coyvalyss1/model-matchmaker
- Auto-switch implementation: Uses keyboard automation (current workaround)
- Investigation: https://github.com/coyvalyss1/model-matchmaker/issues/7

Would love to see this in the hooks API! Happy to provide more details or help with implementation if useful.
