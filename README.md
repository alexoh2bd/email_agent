# Email agent

LLM-based agent that researches context (semantic memory + grounding docs), plans a strategy, then drafts and refines an email with tool use—implemented with a **custom** planning and tool-calling loop (no LangChain-style frameworks).

---

## Course assignment requirements

For this individual assignment, you will design and build your own LLM-based agent. Your agent can be designed for any purpose you would like, but it must meet the following requirements:

1. **Custom agent loop** — You must write the code for the agent loop (planning, tool-calling) yourself; you **cannot** use a framework (e.g. no LangChain, CrewAI, etc.).
2. **LLM** — You **may** use an LLM via API if you wish, or run your own model.
3. **Tools** — Your agent must be able to use **at least 3 tools** (which you can build, or use via API or MCP).
4. **User interface** — You must develop a **user interface** for interacting with your agent.
5. **Evaluation** — You must build and execute an approach to **evaluating your agent’s performance**, and demonstrate **quantitatively** how it performs.

### How this project maps to those requirements

| Requirement | In this repo |
|-------------|----------------|
| Custom loop | `run_tool_loop` in `src/agent.py` drives research and drafting phases with explicit tool dispatch (no orchestration framework). |
| LLM via API | Google GenAI (`google-genai`) with `GEMINI_API_KEY`. |
| ≥ 3 tools | Multiple tools (e.g. semantic memory query, grounding fetch, working memory, strategy submit, draft patch, persona critic, finalize)—see `src/tools.py`. |
| UI | **Streamlit** app ([`app.py`](app.py)): chat tab + **human-in-the-loop** labeler (**Minimal revisions** / **Lots of revisions**; writes `email_revised` + `label` in `results.csv`). CLI still works (`--task` or stdin). |
| Evaluation | Quantitative batch metrics on `results.csv` (below) + human judgment on revision load (8 / 11 drafts minimally revisable). |

### Evaluation

Batch evaluation uses `test_agent_loop.py`, which runs the agent once per row in `profiles.csv` and records `email_draft` in `results.csv`. Counts are from the current `results.csv` in this repo (parsed with Python’s `csv` module; a run counts as successful if `email_draft` is non-empty after stripping whitespace).

| Metric | Value |
|--------|------:|
| Profiles / batch runs | **24** |
| Runs that produced an email (non-empty `email_draft`) | **11** |
| Runs with empty draft (no email, error, or no output) | **13** |
| Of successful drafts, **minimally revisable** (human judgment) | **8 / 11** |

Human review: use the **Label results** tab in [`app.py`](app.py) to choose **Minimal revisions** vs **Lots of revisions** and save **`email_revised`**. CSV `label` values are `minimal` or `lots` (older rows may still show `p` / `r`, which mean the same).

---

## Prerequisites

- **Python** 3.12 or newer  
- **[uv](https://docs.astral.sh/uv/)** for environments and dependencies

---

## Setup

### 1. Install dependencies

```bash
cd email_agent
uv sync
```

### 2. Configure environment

Create a `.env` in the project root (same folder as `pyproject.toml`). Minimum variables used by `src/agent.py` / `src/config.py`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | Yes | API key for Google GenAI |
| `PROJECT_ID` | No | Optional; only needed if you use Vertex / GCP resources beyond the API key client |

Optional overrides (see `src/config.py`):

- `MODEL_NAME` — default `gemini-2.5-flash`
- `REGION` — default `us-central1`
- `MEMORY_DIR`, `GROUNDING_DIR`, `SEMANTIC_INDEX_PATH`, `PERSONA_PATH`
- `MAX_ARCHITECT_TURNS`, `MAX_DRAFT_TURNS`, `MAX_GROUNDING_CHARS`

Example `.env` skeleton (replace with your values):

```env
GEMINI_API_KEY=your_key_here
# PROJECT_ID=your-gcp-project-id   # optional for API-key-only runs
# MODEL_NAME=gemini-2.5-flash
```

### 3. Memory files (optional but useful)

- `memory/persona.md` — recipient persona for the critic tool  
- `memory/semantic_index.json` — semantic memory index  
- `memory/grounding/*.md` — facts the agent can pull in

---

## Run the agent

From the project root, using the project virtual environment:

```bash
uv run python src/agent.py --task "Your email task in natural language"
```

Or pipe a task on stdin:

```bash
echo "Schedule a meeting with my advisor about the capstone" | uv run python src/agent.py
```

If you omit `--task` and stdin is a TTY, the program prompts for a task interactively.

The agent prints tool calls and ends with a **final draft** section.

**Web UI (Streamlit)** — chat with the agent and label rows in `results.csv`:

```bash
uv run streamlit run app.py
```

### Human-in-the-loop: revise and label

After the model produces drafts, you review how much editing the draft needs. The workflow is:

1. **Generate drafts at scale** — `test_agent_loop.py` walks `profiles.csv`, runs the agent per contact, and writes `results.csv` with one row per person (`Name`, `Role`, `Email`, `email_draft`, `email_revised`, `label`, `sent`). Initial runs leave `email_revised` and `label` empty until you label.

2. **Open the Label results tab** in [`app.py`](app.py) (`uv run streamlit run app.py`). Pick a row (name, email, and current label). You see the **original draft** (`email_draft`) for reference and an editable **working copy** for the text you are willing to send (pre-filled from `email_revised` if you already saved one, otherwise from `email_draft`).

3. **Edit** the email in the text area if you want changes (tone, facts, sign-off, length). You are the final editor; the agent does not send mail.

4. **Choose a label** — **Minimal revisions** means the model’s draft needed only light edits (or none) to be sendable. **Lots of revisions** means the draft needed substantial editing or a rewrite. Either button saves the current textarea to **`email_revised`** and sets **`label`** to `minimal` or `lots` (legacy rows may use `p` / `r` for the same meaning).

5. **`sent`** stays unchanged in the labeler (defaults to `false` in batch output); you can track “actually sent” separately or extend the app later.

Do **not** run `test_agent_loop.py` at the same time as the Streamlit labeler while both are writing `results.csv`, or you risk overwriting each other’s changes.

---

## Project layout (high level)

| Path | Role |
|------|------|
| `app.py` | Streamlit UI (chat + CSV labeler) |
| `src/agent.py` | Entry point, `run_tool_loop`, research + draft nodes |
| `src/tools.py` | Tool implementations and registration |
| `src/config.py` | Paths, model name, limits |
| `src/prompts.py` | System / research / draft prompts |
| `memory/` | Persona, grounding, semantic index |

---

## License

Add your license or course policy if you use this repo.
