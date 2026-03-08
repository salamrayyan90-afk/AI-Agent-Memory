# Git & GitHub Setup — CORE AI

Run these steps **after installing Git** (and optionally GitHub CLI) from https://git-scm.com and https://cli.github.com.

## 1. Initialize repository (if not already)

```bash
cd "c:\Users\user\Desktop\Core AI"
git init
```

## 2. Create the repository on GitHub

**Option A — GitHub CLI (recommended):**
```bash
gh auth login
gh repo create "Core-AI" --public --source=. --remote=origin --description "CORE AI v1.0 - Professional Build"
```

**Option B — Manual:** Create a new public repo at https://github.com/new named **Core-AI**, then:
```bash
git remote add origin https://github.com/YOUR_USERNAME/Core-AI.git
```

## 3. Stage, commit, and push

```bash
git add .
git commit -m "Initial Professional Build - CORE AI v1.0"
git branch -M main
git push -u origin main
```

(If you used **Option A**, the push is included in `gh repo create` with `--push`; otherwise run the last two lines.)

## 4. Repository link

After a successful push, your repo will be at:
**https://github.com/YOUR_USERNAME/Core-AI**

Replace `YOUR_USERNAME` with your GitHub username.
