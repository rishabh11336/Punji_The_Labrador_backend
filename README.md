# Punji Admin Backend

Flask-based admin panel for managing Punji's dog product affiliate site.

## Features

- 🔐 Secure admin authentication
- 📸 Image upload and optimization
- 🐙 GitHub API integration
- ✨ Clean, responsive UI
- 🚀 Ready for deployment

## Setup

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your credentials.

### 3. Run Locally

```bash
python app.py
```

Visit `http://localhost:5000`

## Deployment

See `execution_plan.md` for detailed deployment instructions to Render, Railway, or other platforms.

### Keep-Alive Workflow

This repository includes a GitHub Actions workflow (`.github/workflows/keep_alive.yml`) that automatically pings the deployed Render app every 14 minutes to prevent it from spinning down due to inactivity on Render's free tier.

**Important Notes:**
- The workflow runs on a schedule every 14 minutes to comply with GitHub Actions rate limits
- GitHub Actions doesn't guarantee exact timing for scheduled workflows
- Scheduled workflows only run on the default branch (`main`)
- The minimum recommended interval is 15 minutes to avoid GitHub rate limiting
- You can manually trigger the workflow from the Actions tab if needed

## Structure

```
Punji_The_Labrador_backend/
├── app.py               # Main Flask app
├── requirements.txt     # Dependencies
├── Procfile            # For deployment
├── services/
│   ├── github_service.py
│   └── image_service.py
├── utils/
│   └── auth.py
├── templates/
│   ├── login.html
│   ├── admin.html
│   └── success.html
└── static/
    ├── admin.css
    └── admin.js
```

## Environment Variables

- `GITHUB_TOKEN`: Personal access token with repo scope
- `GITHUB_REPO_OWNER`: Your GitHub username
- `DATA_REPO_NAME`: Name of data repository (Punji_The_Labrador_Images-JSON)
- `ADMIN_USERNAME`: Admin login username
- `ADMIN_PASSWORD`: Admin login password
- `SECRET_KEY`: Flask secret key

## License

MIT
