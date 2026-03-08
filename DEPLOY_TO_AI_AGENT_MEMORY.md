# Push to AI-Agent-Memory (STRICT)

Run these commands **in order** from the project folder. Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

## 1. Open terminal in project folder

```bash
cd "c:\Users\user\Desktop\Core AI"
```

## 2. Initialize and commit (if not already)

```bash
git init
git branch -M main
git add .
git commit -m "Final deployment build - CORE AI (app.py, index.html, requirements.txt, CoreAI.ico)"
```

## 3. Link to AI-Agent-Memory and push

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/AI-Agent-Memory.git
git push -u origin main
```

## 4. Repository link (after successful push)

**https://github.com/YOUR_GITHUB_USERNAME/AI-Agent-Memory**

---

**Required for Streamlit:** The push includes `app.py`, `index.html`, `requirements.txt`, and `CoreAI.ico` so the repo is ready for Streamlit Cloud deployment.
