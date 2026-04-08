from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import config

def _load_json(path: Any) -> Any:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _query_semantic_memory_impl(topic: str, index_path: Any) -> dict[str, Any]:
    data = _load_json(index_path)
    if not data or "entries" not in data:
        return {"hits": [], "message": "No semantic index found. Add memory/semantic_index.json."}
    q = topic.lower().strip()
    hits: list[str] = []
    for entry in data["entries"]:
        blob = json.dumps(entry).lower()
        if q in blob:
            hits.append(entry.get("snippet", str(entry)))
    if not hits:
        return {
            "hits": [],
            "message": f'No memory hits for "{topic}". Try another keyword or add entries to semantic_index.json.',
        }
    return {"hits": hits[:5], "message": "ok"}

def _fetch_grounding_facts_impl(query: str, grounding_dir: Any, max_chars: int) -> dict[str, Any]:
    if not grounding_dir.exists():
        return {"content": "", "message": f"Grounding directory missing: {grounding_dir}"}
    parts: list[str] = []
    qlow = query.lower()
    for path in sorted(grounding_dir.rglob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            parts.append(f"[{path.name}: read error {e}]")
            continue
        if not qlow or qlow in text.lower() or not parts:
            parts.append(f"--- {path.name} ---\n{text.strip()}")
        if sum(len(p) for p in parts) >= max_chars:
            break
    blob = "\n\n".join(parts) if parts else ""
    if not blob:
        blob = "\n\n".join(
            p.read_text(encoding="utf-8") for p in sorted(grounding_dir.rglob("*.md"))
        )
    if len(blob) > max_chars:
        blob = blob[:max_chars] + "\n...[truncated]"
    return {"content": blob, "message": "ok" if blob else "No markdown files in grounding dir."}


# --- Unified Tool Definition & Implementation ---

def build_tool_handlers(
    state: dict[str, Any],
    critic_model: Any, # Passed in from your main execution loop
) -> tuple[list[Callable], list[Callable]]:
    """Close over `state` and `critic_model`; returns lists of functions to pass to the SDK."""

    # ==========================================
    # ARCHITECT TOOLS
    # ==========================================

    def query_semantic_memory(topic: str) -> dict[str, Any]:
        """Search local memory for tone, sign-off, and style notes for a topic or recipient (e.g. lab colleague, advisor name)."""
        return _query_semantic_memory_impl(topic, config.SEMANTIC_INDEX_PATH)

    def fetch_grounding_facts(query: str) -> dict[str, Any]:
        """Read grounding markdown files (capstone status, schedule, facts) so the plan uses real details instead of guessing."""
        return _fetch_grounding_facts_impl(query, config.GROUNDING_DIR, config.MAX_GROUNDING_CHARS)

    def write_working_memory(key: str, value: str) -> dict[str, Any]:
        """Store a short key/value note in working memory (scratchpad for this run)."""
        state.setdefault("working_memory", {})
        state["working_memory"][key] = value
        return {"ok": True, "key": key}

    def submit_strategy_plan(plan: str) -> dict[str, Any]:
        """Submit the full bulleted strategic plan for the email. Call this when research is complete. This hands off to the drafting phase."""
        state["strategy_plan"] = plan
        state["node"] = "draft"
        return {"ok": True, "message": "Strategy plan recorded. Handing off to drafting."}

    architect_tools = [
        query_semantic_memory,
        fetch_grounding_facts,
        write_working_memory,
        submit_strategy_plan,
    ]

    # ==========================================
    # WORDSMITH (DRAFT) TOOLS
    # ==========================================

    def read_current_draft() -> dict[str, Any]:
        """Return the latest email draft text stored in working state."""
        return {"draft": state.get("draft", "")}

    def patch_draft(search_string: str, replace_string: str) -> dict[str, Any]:
        """Replace the first occurrence of search_string with replace_string. If the draft is empty, use search_string \"\" and put the full email in replace_string."""
        draft = state.get("draft", "")
        if not draft and search_string == "":
            state["draft"] = replace_string
            return {"ok": True, "draft": state["draft"]}
        if search_string not in draft:
            return {
                "ok": False,
                "error": "search_string not found in draft",
                "draft": draft,
            }
        state["draft"] = draft.replace(search_string, replace_string, 1)
        return {"ok": True, "draft": state["draft"]}

    def run_persona_critic(draft_text: str) -> dict[str, Any]:
        """Run a persona-based critic on the draft (uses recipient persona from memory). Call after substantive edits."""
        persona = ""
        if config.PERSONA_PATH.exists():
            persona = config.PERSONA_PATH.read_text(encoding="utf-8")
        user_msg = (
            f"Recipient persona (context):\n{persona}\n\n"
            f"Draft to critique:\n{draft_text}"
        )
        # Note: critic_model now needs to be a `genai.Client` call in your updated architecture
        response = critic_model.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_msg
        )
        text = response.text or "(no critique text returned)"
        return {"critique": text}

    def finalize_draft() -> dict[str, Any]:
        """Mark the draft as ready for human Pass/Reject review and end this phase."""
        state["node"] = "done"
        return {"status": "finalized", "message": "Draft marked ready for Pass/Reject review."}

    draft_tools = [
        read_current_draft,
        patch_draft,
        run_persona_critic,
        finalize_draft,
    ]

    return architect_tools, draft_tools