# The Core AI Autonomous Agent

A **Super App** that combines a Gemini-style chat interface with vision, persistent memory (GitHub RAG), autonomous browser control, and safe computer control — all powered by Groq and following the logic in `Gemini_Expertise_Transfer.md`.

## Features

### 1. Visual Interface (Gemini-Style UI)
- **Streamlit** app with a deep dark theme (background: `#0e1117`).
- Fixed, rounded bottom chat bar for input.
- **(+)** button in the bar for **uploads**: images (Vision), documents (PDF, DOC/DOCX), and videos (MP4, WebM).
- **Word-by-word streaming** responses.

### 2. Cognitive Engine & Vision (Groq)
- **Groq API** with model `llama-3.2-11b-vision-preview` for fast text and image/screen analysis.
- Agent responds in **natural Jordanian/Arabic dialect** and strictly follows the rules in `Gemini_Expertise_Transfer.md`.

### 3. Persistent Memory & GitHub RAG
- Connected to your **private GitHub repository** via `GITHUB_TOKEN` and `GITHUB_REPO`.
- Before answering, the agent **searches the repo** (e.g. `memory/` and `memory/tasks/`) for past experiences.
- After successful tasks, it **pushes short task summaries** to the repo for future RAG.

### 4. Autonomous Execution & System Control
- **Playwright** (and optional **browser-use**) for autonomous web navigation: search products, compare prices, interact with sites.
- **Computer Control** module: list directories, read files, and **monitor system resources** (e.g. i7-7700HQ, 16GB RAM).
- **Safety:** Financial transactions and OS-level changes require a mandatory **Approve/Run** confirmation before execution.

### 5. Environment
- **`.env`** for `GROQ_API_KEY` and `GITHUB_TOKEN` (and `GITHUB_REPO`).
- **`requirements.txt`** lists all dependencies.
- **`Gemini_Expertise_Transfer.md`** defines agent behavior and safety rules.

---

## Setup

1. **Clone or create the project** (e.g. on Desktop in folder `Core AI`).

2. **Create virtual environment and install dependencies:**
   ```bash
   cd "Core AI"
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure environment:**
   - Copy `.env.example` to `.env`.
   - Set `GROQ_API_KEY` (from [Groq Console](https://console.groq.com)).
   - Set `GITHUB_TOKEN` (Personal Access Token with `repo` scope).
   - Set `GITHUB_REPO` to `your_username/your_private_repo`.

4. **Optional — GitHub memory layout:**  
   In your repo you can add a `memory/` or `memory/tasks/` folder. The agent will read markdown/text files there for RAG and push new task summaries into that repo.

5. **Run the app:**
   ```bash
   streamlit run app.py
   ```

---

## Project Structure

```
Core AI/
├── app.py                    # Streamlit UI (chat bar, uploads, streaming)
├── core/
│   ├── config.py             # GROQ, GitHub, theme, safety keywords
│   └── cognitive_engine.py   # Groq vision + chat (streaming)
├── memory/
│   └── github_rag.py         # Search repo + push task summaries
├── modules/
│   ├── browser_agent.py      # Playwright autonomous browsing
│   └── computer_control.py   # Files + system resources (CPU/RAM)
├── static/                   # Uploaded files (images, docs, video)
├── Gemini_Expertise_Transfer.md
├── .env.example
├── requirements.txt
└── README.md
```

---

## Safety (Approve/Run)

Actions that involve **financial** or **OS-level** keywords (e.g. دفع، شراء، حذف، نظام) trigger a mandatory **Approve/Run** step. The agent will not execute such actions until you confirm in the UI.

---

## Super App Capabilities Summary

| Capability           | Description                                      |
|----------------------|--------------------------------------------------|
| **Chat + streaming** | Jordanian Arabic, word-by-word output            |
| **Vision**           | Image/screenshot analysis via Groq vision model  |
| **Uploads**          | Images, documents, videos in the chat bar        |
| **GitHub RAG**       | Search past experiences; push new summaries      |
| **Browser**          | Playwright (and optional browser-use) automation |
| **System**           | List files, read files, CPU/RAM monitoring       |
| **Safety**           | Approve/Run for money and OS-changing actions    |

---

*Built for autonomous assistance with a focus on safety and persistent learning.*
