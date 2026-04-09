"""Batch-run the email agent for each row in profiles.csv and write results.csv."""

from __future__ import annotations

import csv
import sys
import traceback
from pathlib import Path

# Repo root must be on path for `src.agent`
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agent import run_agent_pipeline  # noqa: E402

PROFILES_CSV = _ROOT / "profiles.csv"
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


def compose_task(row: dict[str, str]) -> str:
    """Build the user_task string for the agent from a profile row."""
    name = (row.get("Name") or "").strip()
    role = (row.get("Role") or "").strip()
    desc = (row.get("description") or "").strip()
    papers = (row.get("papers") or "").strip()
    recipient = f"{name}" + (f" ({role})" if role else "")
    parts = [
        f"Write a concise cold-outreach email to {recipient}.",
        "Goal: express research alignment and politely ask for a short meeting or reply.",
        f"Context about them:\n{desc}" if desc else "",
        f"Relevant papers / links:\n{papers}" if papers else "",
        f"The recipient's email address is: {row.get('email', '').strip()} (use only for the signature / To line if needed; keep tone professional).",
    ]
    return "\n\n".join(p for p in parts if p)


def main() -> None:
    if not PROFILES_CSV.is_file():
        print(f"Error: missing {PROFILES_CSV}", file=sys.stderr)
        sys.exit(1)

    with PROFILES_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Truncate results and stream one row at a time so each completion is persisted immediately.
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(RESULT_FIELDS)
        out_f.flush()

        n = 0
        for row in rows:
            name = (row.get("Name") or "").strip()
            role = (row.get("Role") or "").strip()
            email = (row.get("email") or "").strip()

            draft_text = ""
            if not email:
                # Skip API call when there is no recipient email; still record the row.
                print(f"[skip agent] No email for profile: {name or '(unnamed)'}", file=sys.stderr)
            else:
                task = compose_task(row)
                try:
                    state = run_agent_pipeline(task)
                    draft_text = (state.get("draft") or "").strip()
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    draft_text = ""

            writer.writerow(
                [
                    name,
                    role,
                    email,
                    draft_text,
                    draft_text,
                    "",
                    "False",
                ]
            )
            out_f.flush()
            n += 1

    print(f"Wrote {n} rows to {RESULTS_CSV}")


if __name__ == "__main__":
    main()
