# PicoBlog - Installation & Deployment Guide

This guide covers setting up PicoBlog for both local development and production environments.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for building CSS)
- **Git**
- **Docker & Docker Compose** (optional, recommended for production)

---

## 1. Quick Start (Development)

Follow these steps to get PicoBlog running locally in minutes.

### 1.1 Install Dependencies

```bash
# Set up Python virtual environment
uv venv
source .venv/bin/activate
uv sync

# Install Node dependencies
npm install
```

### 1.2 Configuration

```bash
cp .env.example .env
# Generate a secure secret key
sed -i "s/^SECRET_KEY=.*/SECRET_KEY='$(python3 -c 'import secrets; print(secrets.token_hex(32))')'/" .env
```

### 1.3 Build & Run

```bash
# Build CSS
npm run build:css

# Initialize Database
export FLASK_APP=app
flask db upgrade

# Run development server
python run.py
```

The app will be available at `http://127.0.0.1:5000`.

---

## 2. Production Deployment (Docker)

This is the **recommended** way to deploy PicoBlog. It handles all dependencies, including CSS building and the WSGI server.

### 2.1 Configuration

```bash
cp .env.example .env
# Set FLASK_ENV to production
sed -i "s/FLASK_ENV=development/FLASK_ENV=production/" .env
# Generate secret key
sed -i "s/^SECRET_KEY=.*/SECRET_KEY='$(python3 -c 'import secrets; print(secrets.token_hex(32))')'/" .env
```

### 2.2 Run with Docker Compose

```bash
docker-compose up -d --build
```

The application will be running on `http://127.0.0.1:8000`. You can now point your Nginx reverse proxy to this port.

---

## 3. Production Deployment (Manual)

If you prefer not to use Docker, follow these steps for a traditional Linux deployment.

### 3.1 System Setup

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx nodejs npm
```

### 3.2 Application Setup

```bash
# Clone and setup env
git clone https://github.com/Lowara1243/PicoBlog
cd PicoBlog
python3 -m venv .venv
source .venv/bin/activate
pip install uv
uv sync
npm install
npm run build:css
```

### 3.3 Configure Service (systemd)

Create `/etc/systemd/system/PicoBlog.service`:

```ini
[Unit]
Description=PicoBlog Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/PicoBlog
Environment="PATH=/var/www/PicoBlog/.venv/bin"
ExecStart=/var/www/PicoBlog/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 "run:app"

Restart=always
[Install]
WantedBy=multi-user.target
```

---

## 4. Nginx Configuration

Choose the method that matches your infrastructure.

### Option A: Standalone Nginx (Managing SSL)
Use this if PicoBlog is the primary application on this server.

1. **Copy configuration:**
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/PicoBlog
   sudo ln -s /etc/nginx/sites-available/PicoBlog /etc/nginx/sites-enabled/
   ```
2. **Setup SSL:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

### Option B: Behind an Existing Reverse Proxy
If you already have a proxy (like Nginx Proxy Manager or another Nginx instance) that handles SSL, just point it to the PicoBlog container/address:

**Proxy Target:** `http://127.0.0.1:8000`

**Nginx Snippet:**
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## 5. Configuration Reference

| Variable | Description |
| :--- | :--- |
| `SECRET_KEY` | **Required.** Random string for session security. |
| `FLASK_ENV` | Set to `production` for automatic security features. |
| `DATABASE_URL` | Database URL (Default: `sqlite:///data/app.db`). |
| `REQUIRE_LOGIN` | `True` (default) for private mode. |

---

## Troubleshooting

- **CSS not loading?** Run `npm run build:css`.
- **502 Bad Gateway?** Check if Gunicorn/Docker is running on port 8000.
- **Permission issues?** Ensure `www-data` owns the directory in manual setup.
