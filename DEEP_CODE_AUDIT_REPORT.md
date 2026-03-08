# Deep Code Audit Report — Core AI (2026 Standards)

**Role:** Senior AI Solutions Architect  
**Scope:** Full workspace audit and upgrade to professional 2026 standards  
**Target hardware:** i7-7700HQ, 16GB RAM

---

## 1. Logic & Efficiency

### app.py (main entry)
- **Web-fetching:** `web_search_tool` and `price_radar_search` use a single DDGS context per call; no redundant loops. `get_live_price` returns on first successful query and does not over-fetch.
- **Refactor applied:** None removed (no duplicate fetch blocks). Optional future: extract price/vision/code branches into `tools/` or `services/` for smaller app.py.
- **Recommendation:** For i7-7700HQ, keep `max_results` at 6 for web and 10 for price radar; already reasonable. ChromaDB and sentence-transformers are the main memory users; consider lazy-loading RAG on first code-path only if needed.

### autonomous_agent.py
- **Refactor applied:**
  - **Memory cache with TTL (60s):** `_refresh_memory()` now skips GitHub when cache is fresh. Reduces API calls when `is_data_new()` is invoked multiple times in the same request or in quick succession.
  - **Single return path:** `auto_check_and_update` now returns `new_info` in both “new” and “unchanged” cases, and only calls `push_to_github` when data is new (no redundant push).
- **Result:** Fewer GitHub reads and clearer control flow; better for 16GB RAM and CPU-bound i7.

---

## 2. Security & Environment

### Findings
- **No hardcoded secrets.** All API keys and tokens are read via `os.getenv()` or `core.config` (which uses `load_dotenv(.env)`). Checked: `app.py`, `core/config.py`, `core/research.py`, `core/github_projects.py`, `autonomous_scan.py`.
- **.env:** Loaded from `ROOT / ".env"` in app and in `core/config`. No keys in repo.

### Changes applied
- **.gitignore:** Expanded to include:
  - `.env.local`, `.env.*.local`, `*.pem`
  - `data/`, `chroma/`, `*.log`
  - `.streamlit/secrets.toml`
  - Common IDE/OS entries (`.idea/`, `.vscode/`, `Thumbs.db`, `.DS_Store`)
- **.env.example:** Updated with required vs optional vars and a short note: copy to `.env`, never commit.

### Recommendation
- Keep using `.env` for all secrets; do not add `GROQ_API_KEY` or `GITHUB_TOKEN` to `secrets.toml` unless you explicitly want Streamlit to override.

---

## 3. Professional Refactoring (Clean Code)

### Modularity
- **Current layout:** UI and flow in `app.py`; logic in `core/` (config, advanced_search, autonomous_agent, research, stack_overflow, github_projects); memory in `memory/` (github_rag, vector_rag). Tools (web search, price radar, SO, GitHub projects) are either in `app.py` or in `core/`.
- **Naming:** `action_picker`, `needs_live_price_prompt`, `build_reasoning_agent_system`, `sync_knowledge`, `update_agent_knowledge` are clear and consistent.
- **Docstrings:** Added or clarified for:
  - `web_search_tool`: returns (raw_text, rows) and purpose.
  - `price_radar_search`: returns (raw_text, rows), timelimit=d.
  - `AutonomousAgent`: class purpose, `_refresh_memory` (TTL cache), `auto_check_and_update` (single DDGS context, minimal results).

### Optional next steps
- Move `web_search_tool`, `price_radar_search`, and `get_live_price` into e.g. `core/web_tools.py` and import in `app.py` to shorten app.py and separate UI from tools.
- Add one-line docstrings to any remaining public functions in `app.py` that lack them.

---

## 4. RAG & Sync Validation

### GitHub push/pull
- **Pull:** `sync_knowledge()` → `sync_github_memory()` reads `knowledge_base.md` and parses latest date. Used at start of each query in `app.py` (e.g. `sync_knowledge()` before building the system prompt).
- **Push:** `update_agent_knowledge()`, `append_to_knowledge_base()`, `push_proposed_update()`, `update_github_repo()` all use `_get_repo()` and the same token/repo from config. No conflicting code paths found.

### Data priority (knowledge_base + web over training)
- **Explicit instruction added** in `build_reasoning_agent_system()`:
  - *"Data priority (RAG & Sync): knowledge_base.md and the latest web search results ALWAYS override your internal training memory. For prices and time-sensitive facts, use only the provided snippets and knowledge_base; never rely on model weights alone."*
- Existing blocks already enforce: (1) stale KB for price → use only fresh web data, (2) Zero-Inference, (3) Data grounding (prices from snippets only). The new line makes the priority ordering explicit.

---

## 5. UI/UX Consistency

### 18px and no large headers
- **Single source of truth:** `UI_FONT_SIZE_PX = 18` in `app.py`. All relevant CSS rules use this variable via f-string (`.stApp`, `.stMarkdown`, `.block-container`, chat message content, all h1–h6, `.stExpander`).
- **Headers:** All `.stMarkdown h1`–`h6` are forced to `18px` and `font-weight: 600`, so no large titles; minimal, consistent layout.
- **Result:** One constant drives font size; changing it in one place updates the whole UI.

---

## 6. Performance Report & System Health (16GB RAM)

### Improvements made (summary)
| Area | Change | Benefit |
|------|--------|--------|
| **autonomous_agent** | 60s TTL cache on `_refresh_memory()` | Fewer GitHub API calls per request/session |
| **autonomous_agent** | Single return path in `auto_check_and_update` | Clearer logic, no redundant push |
| **Security** | .gitignore and .env.example tightened | Reduced risk of committing secrets or logs |
| **RAG/Sync** | Explicit data-priority line in system prompt | Agent consistently prefers KB + web over training |
| **UI** | `UI_FONT_SIZE_PX` centralised, all CSS use it | Consistent 18px, easy to tune later |

### System health (16GB RAM, i7-7700HQ)

- **Streamlit:** Typically 200–500 MB for the app process; acceptable.
- **ChromaDB + sentence-transformers:** Largest consumers. Embedding model loads once; Chroma persists under `data/chroma` (or `CHROMA_PERSIST_DIR`). On 16GB, if you see pressure:
  - Ensure only one Streamlit process runs.
  - RAG is already loaded lazily (on first use); optional: delay `ensure_rag_context_loaded()` until the first code-path query.
- **DDGS / requests:** Short-lived; no long-lived connection pools. Fine for i7.
- **Background thread (autonomous_scan):** Runs every 3600s; one scan per hour. Memory impact is small (one extra run of web_scout + fetch_live_gold + optional Groq call).
- **Recommendation:** Monitor with Task Manager or `psutil` (already in sidebar). If RAM usage grows over time, consider restarting the Streamlit process periodically or lazy-loading the embedding model only when the first “code” or RAG query is made.

### Memory usage (indicative)
- **Idle (after load):** ~800 MB – 1.5 GB (Streamlit + Chroma + embeddings).
- **Under load (search + Groq):** +100–300 MB transient.
- **16GB system:** Leaves ample headroom for OS and other apps.

---

**Audit completed.** All critical items addressed; optional refactors (e.g. moving web tools to a dedicated module) can be done in a follow-up pass.
