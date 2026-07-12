# Lenovo ASP Ticket Tracker

A Flask web application for managing Lenovo After-Sales Partner (ASP) work orders, backed by Excel data.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Deploy to Render.com](#deploy-to-rendercom)
- [Environment Variables](#environment-variables)

---

## Project Structure

```
.
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── routes/
│   │   ├── ticket.py        # Work-order ticket routes
│   │   └── excel_upload.py  # Excel upload routes
│   ├── services/
│   │   ├── excel_service.py # Reads work-order data from Excel
│   │   └── wo_onsite/       # On-site WO pipeline
│   └── templates/           # Jinja2 HTML templates
├── config/
│   └── settings.py          # Flask config (paths, secret key)
├── excels/                  # Output Excel reports (auto-created)
├── uploads/                 # Uploaded Excel source files (auto-created)
├── files/                   # Evidence file uploads (auto-created)
├── render.yaml              # Render.com deployment config
├── requirements.txt
└── run.py                   # App entry point
```

---

## Prerequisites

### Python (macOS via Homebrew)

If you are on macOS and install Python via Homebrew, it will block system-wide `pip install` by default (PEP 668). The correct approach is to always use a virtual environment per project (covered in [Local Development](#local-development) below).

To install Python via Homebrew and make the `python`, `python3`, and `py` commands all available:

```zsh
brew install python
```

Then add Homebrew's unversioned symlinks to your PATH (add to `~/.zshrc`):

```zsh
echo 'export PATH="/usr/local/opt/python@3.14/libexec/bin:$PATH"' >> ~/.zshrc
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
echo "alias py='python3'" >> ~/.zshrc
source ~/.zshrc
```

Verify all three shortcuts work:

```zsh
python --version   # Python 3.14.x
python3 --version  # Python 3.14.x
py --version       # Python 3.14.x
```

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

> **macOS/Homebrew note:** Running `pip install` outside a virtual environment will fail with an `externally-managed-environment` error. Always activate `.venv` first — do **not** use `--break-system-packages` as it can corrupt your Homebrew Python installation.

Every time you return to work on this project, re-activate the environment:

```zsh
source .venv/bin/activate   # activate
deactivate                  # when done
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The `.venv/` folder is excluded from version control via `.gitignore`. Never commit it.

### 4. Run the development server

```bash
python run.py
```

The app will be available at **http://127.0.0.1:5000**.

---

## Deploy to Render.com

### Prerequisites

- A [Render.com](https://render.com) account (free tier is sufficient)
- The repository pushed to GitHub or GitLab

### Step 1 — Push to GitHub

Make sure all changes (including `render.yaml`) are committed and pushed:

```bash
git add .
git commit -m "Add render.yaml and gunicorn"
git push origin main
```

### Step 2 — Create a new Web Service on Render

1. Log in to [render.com](https://render.com) and click **New → Web Service**.
2. Connect your GitHub/GitLab account and select this repository.
3. Render will auto-detect `render.yaml` and pre-fill the settings:

   | Setting | Value |
   |---|---|
   | **Runtime** | Python |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

4. Click **Create Web Service**.

### Step 3 — Set environment variables (if needed)

In the Render dashboard go to your service → **Environment** tab and add any required variables (see [Environment Variables](#environment-variables) below).

### Step 4 — Deploy

Render will automatically build and deploy on every push to `main`. You can also trigger a manual deploy from the dashboard via **Manual Deploy → Deploy latest commit**.

### Subsequent deploys

Every `git push origin main` triggers an automatic redeploy — no further action needed.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Recommended | Flask secret key for session security. Defaults to a hardcoded dev value — **always override in production**. |
| `PORT` | Auto-set | Injected by Render at runtime. Do not set this manually. |

To set `SECRET_KEY` on Render:

1. Go to your service → **Environment** tab.
2. Click **Add Environment Variable**.
3. Key: `SECRET_KEY`, Value: a long random string (e.g. output of `python -c "import secrets; print(secrets.token_hex(32))"`).

> **Note on file persistence:** Render's free tier uses an ephemeral filesystem — uploaded Excel files and generated reports in `uploads/` and `excels/` will be lost on each redeploy. For persistent storage, attach a [Render Disk](https://render.com/docs/disks) or store files in an external service (e.g. AWS S3).
