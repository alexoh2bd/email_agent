"""Streamlit UI: chat with the email agent + label rows in results.csv."""

from __future__ import annotations

import csv
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agent import run_agent_pipeline  # noqa: E402

load_dotenv()

RESULTS_CSV = _ROOT / "results.csv"

RESULT_FIELDS = [
    "Name",
    "Role",
    "Email",
    "email_draft",
    "email_revised",
    "label",
    "sent",
]

# Stored in CSV; legacy rows may still use p / r
LABEL_MINIMAL = "minimal"
LABEL_LOTS = "lots"


def label_display(raw: str) -> str:
    """Human-readable label for UI and row picker."""
    t = (raw or "").strip().lower()
    if t == "":
        return "(unlabeled)"
    if t in ("p", LABEL_MINIMAL):
        return "Minimal revisions"
    if t in ("r", LABEL_LOTS):
        return "Lots of revisions"
    return raw or "(unlabeled)"


def load_results_rows() -> list[dict[str, str]]:
    if not RESULTS_CSV.is_file():
        return []
    with RESULTS_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_results_rows(rows: list[dict[str, str]]) -> None:
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            out = {k: row.get(k, "") for k in RESULT_FIELDS}
            w.writerow(out)


def initial_revised_body(row: dict[str, str]) -> str:
    rev = (row.get("email_revised") or "").strip()
    if rev:
        return rev
    return row.get("email_draft", "") or ""


def _format_chat_assistant_content(text: str) -> str:
    """Show errors as-is; wrap successful drafts for readability and copy-paste."""
    if text.startswith("**Configuration error:**") or text.startswith("**Error:**"):
        return text
    if not (text or "").strip() or text == "(empty draft)":
        return "**Email draft**\n\n_(empty — agent returned no body)_"
    # Fenced block preserves newlines and makes the email easy to copy
    return f"**Email draft**\n\n```text\n{text}\n```"


def tab_chat() -> None:
    st.subheader("Email agent")
    st.caption(
        "Same pipeline as the CLI: research → strategy → draft with tools. "
        "Your message is the task; the assistant reply is the **final email draft** (copy from the block below)."
    )

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Describe the email task…"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        draft_text = ""
        try:
            with st.spinner("Running agent (research + draft)…"):
                state = run_agent_pipeline(prompt)
                draft_text = (state.get("draft") or "").strip() or "(empty draft)"
        except ValueError as e:
            draft_text = f"**Configuration error:** {e}"
        except Exception:
            draft_text = f"**Error:**\n```\n{traceback.format_exc()}\n```"

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": _format_chat_assistant_content(draft_text)}
        )
        # Without rerun, Streamlit has already drawn the message list for this run *before*
        # the new messages were appended, so the user sees no reply until another interaction.
        st.rerun()


def tab_labeler() -> None:
    st.subheader("Label results")
    st.caption(
        "Edits `results.csv`. **Minimal revisions** = light edits (or none) to send; "
        "**Lots of revisions** = heavy edit or rewrite. "
        "Do not run `test_agent_loop.py` at the same time—avoid concurrent writers."
    )

    rows = load_results_rows()
    if not rows:
        st.warning(f"No rows found. Add `{RESULTS_CSV.name}` or run the batch script first.")
        return

    if "label_prev_idx" not in st.session_state:
        st.session_state.label_prev_idx = 0
        st.session_state.revise_body = initial_revised_body(rows[0])

    def row_label(i: int) -> str:
        r = rows[i]
        lab = label_display(r.get("label", ""))
        return f"{r.get('Name', '')} — {r.get('Email', '')} — {lab}"

    idx = st.selectbox(
        "Select row",
        range(len(rows)),
        format_func=row_label,
        key="label_row_select",
    )

    if idx != st.session_state.label_prev_idx:
        st.session_state.label_prev_idx = idx
        st.session_state.revise_body = initial_revised_body(rows[idx])

    r = rows[idx]
    c1, c2, c3 = st.columns(3)
    c1.text_input("Name", value=r.get("Name", ""), disabled=True)
    c2.text_input("Role", value=r.get("Role", ""), disabled=True)
    c3.text_input("Email", value=r.get("Email", ""), disabled=True)

    with st.expander("Original draft (read-only)", expanded=False):
        st.text_area(
            "email_draft",
            value=r.get("email_draft", ""),
            height=200,
            disabled=True,
        )

    # Form batches widgets so text_area value is committed with the submit button
    # (plain st.button + keyed text_area often reads stale session state).
    with st.form("label_row_form", clear_on_submit=False):
        st.text_area(
            "Revise email (saved to **email_revised**)",
            key="revise_body",
            height=320,
        )
        b1, b2 = st.columns(2)
        minimal_clicked = b1.form_submit_button(
            "Minimal revisions", type="primary", use_container_width=True
        )
        lots_clicked = b2.form_submit_button(
            "Lots of revisions", use_container_width=True
        )

    if minimal_clicked:
        body = (st.session_state.get("revise_body") or "").strip()
        rows[idx]["email_revised"] = body
        rows[idx]["label"] = LABEL_MINIMAL
        write_results_rows(rows)
        st.success("Saved: **Minimal revisions**, **email_revised** updated.")
        st.rerun()

    if lots_clicked:
        body = (st.session_state.get("revise_body") or "").strip()
        rows[idx]["email_revised"] = body
        rows[idx]["label"] = LABEL_LOTS
        write_results_rows(rows)
        st.success("Saved: **Lots of revisions**, **email_revised** updated.")
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Email agent", layout="wide")
    st.title("Email agent")

    tab1, tab2 = st.tabs(["Chat", "Label results"])

    with tab1:
        tab_chat()

    with tab2:
        tab_labeler()


if __name__ == "__main__":
    main()
