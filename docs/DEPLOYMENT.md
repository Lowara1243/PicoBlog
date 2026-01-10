# PicoBlog - Production Deployment Guide

This guide covers deploying PicoBlog to a production server with Nginx, Gunicorn, and SSL certificates.

## Prerequisites

- Ubuntu/Debian server with root access
- Domain name pointing to your server's IP
- Git
- Python 3.11+
- Node.js 18+ (for building CSS)

## 1. Server Setup

### Install system dependencies:

```bash
sudo apt update
sudo apt install -y git python3.11 python3-pip python3-venv nginx certbot python3-certbot-nginx nodejs npm
```

### Create application directory and clone repository:

```bash
# Create parent directory
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
cd /var/www

# Clone the repository
git clone <YOUR_REPOSITORY_URL> picoblog
cd picoblog
```
> **Note:** Replace `<YOUR_REPOSITORY_URL>` with the actual URL of your Git repository.

## 2. Application Setup

### Create Python virtual environment:

```bash
cd /var/www/picoblog
python3 -m venv .venv
source .venv/bin/activate
```

### Install Python dependencies:

```bash
# If using uv (recommended):
pip install uv
uv sync

# Or with regular pip:
pip install -e .
```

### Install Node dependencies and build CSS:

```bash
npm install
npm run build:css
```

### Create .env file:

Create a `.env` file by copying the example:
```bash
cp .env.example .env
```

Now, edit the `.env` file and set your `SECRET_KEY`.
```bash
nano .env
```

**IMPORTANT:** Generate a strong `SECRET_KEY` using this command and add it to the `.env` file:
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Your `.env` should look something like this:
```ini
# Generate with: python -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY=your-generated-secret-key-here

# Database (SQLite for small deployments, PostgreSQL recommended for production)
DATABASE_URL=sqlite:////var/www/picoblog/data/app.db

# Environment
FLASK_ENV=production
```

### Create data and upload directories:

```bash
mkdir -p /var/www/picoblog/data
mkdir -p /var/www/picoblog/app/static/uploads
chmod 755 /var/www/picoblog/data /var/www/picoblog/app/static/uploads
```

### Initialize database:

```bash
export FLASK_APP=app
.venv/bin/flask db upgrade

# Create admin user
.venv/bin/flask shell
```
Inside the Flask shell, run the following Python code:
```python
from app.models import User
from app import db
# Replace with your desired admin username, email, and a strong password
admin = User(username='admin', email='admin@example.com', is_admin=True)
admin.set_password(r'your-strong-password-here')
db.session.add(admin)
db.session.commit()
exit()
```

## 3. Gunicorn Setup

### Install Gunicorn:

```bash
.venv/bin/pip install gunicorn
```

### Create systemd service file:

```bash
sudo nano /etc/systemd/system/picoblog.service
```

Add the following content:

```ini
[Unit]
Description=PicoBlog Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/picoblog
Environment="PATH=/var/www/picoblog/.venv/bin"
ExecStart=/var/www/picoblog/.venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/picoblog/access.log \
    --error-logfile /var/log/picoblog/error.log \
    --log-level info \
    "run:app"

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
> **Note**: We use `run:app` to ensure the application is started correctly via the `run.py` file.

### Create log directory:

```bash
sudo mkdir -p /var/log/picoblog
sudo chown www-data:www-data /var/log/picoblog
```

### Set proper permissions:

```bash
sudo chown -R www-data:www-data /var/www/picoblog
sudo chmod -R 755 /var/www/picoblog
```

### Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable picoblog
sudo systemctl start picoblog
sudo systemctl status picoblog
```

## 4. Nginx Configuration

### Copy nginx configuration:

```bash
sudo cp /var/www/picoblog/nginx.conf /etc/nginx/sites-available/picoblog
```

### Edit configuration with your domain:

```bash
sudo nano /etc/nginx/sites-available/picoblog
```

Replace `your-domain.com` with your actual domain name.

> [!TIP]
> The provided `nginx.conf` already includes Gzip compression settings. This significantly reduces the size of HTML, CSS, and JS files, improving performance on slow networks and mobile devices.

### Create certbot directory:

```bash
sudo mkdir -p /var/www/certbot
```

### Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/picoblog /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

## 5. SSL Certificate with Certbot

### Obtain certificate:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts. Certbot will:
- Verify domain ownership
- Obtain SSL certificate
- Automatically update nginx configuration

### Test auto-renewal:

```bash
sudo certbot renew --dry-run
```

Certbot automatically sets up a cron job for renewal.

## 6. Production Configuration

### Update config.py security settings:

Edit `/var/www/picoblog/config.py` and uncomment:

```python
SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
REMEMBER_COOKIE_SECURE = True
```

### Restart application:

```bash
sudo systemctl restart picoblog
```

## 7. Verify Deployment

### Check services:

```bash
sudo systemctl status picoblog
sudo systemctl status nginx
```

### Check logs:

```bash
# Application logs
sudo tail -f /var/log/picoblog/error.log

# Nginx logs
sudo tail -f /var/log/nginx/picoblog_error.log
```

### Test site:

Visit `https://your-domain.com` and verify:
- [ ] Site loads over HTTPS
- [ ] HTTP redirects to HTTPS
- [ ] Static files load correctly
- [ ] Login works
- [ ] Admin panel accessible
- [ ] Image upload works

## 8. Maintenance

### Update application:

```bash
cd /var/www/picoblog
git pull origin main # Or your default branch
source .venv/bin/activate

# Update dependencies
uv pip install -e .

# Rebuild CSS
npm run build:css

# Apply database migrations
.venv/bin/flask db upgrade

# Set correct permissions and restart
sudo chown -R www-data:www-data /var/www/picoblog
sudo systemctl restart picoblog
```

### Backup database:

```bash
# For SQLite
sudo cp /var/www/picoblog/data/app.db /var/backups/picoblog-$(date +%Y%m%d).db

# For PostgreSQL
pg_dump picoblog > /var/backups/picoblog-$(date +%Y%m%d).sql
```

### View logs:

```bash
# Application logs
sudo journalctl -u picoblog -f

# Nginx access logs
sudo tail -f /var/log/nginx/picoblog_access.log
```

## 9. Troubleshooting

### Application won't start:

```bash
sudo journalctl -u picoblog -n 50
```

Check for:
- Missing `SECRET_KEY` in `.env`
- Database connection errors
- Permission issues

### 502 Bad Gateway:

- Check Gunicorn is running: `sudo systemctl status picoblog`
- Check port 8000 is listening: `sudo netstat -tlnp | grep 8000`
- Check nginx error log: `sudo tail /var/log/nginx/picoblog_error.log`

### Static files not loading:

- Verify path in `nginx.conf` matches actual location
- Check permissions: `ls -la /var/www/picoblog/app/static/`
- Rebuild CSS: `npm run build:css`

### Upload errors:

- Check upload directory exists and is writable
- Verify `MAX_CONTENT_LENGTH` in `config.py` matches nginx `client_max_body_size`

## 10. Security

### Configure firewall:

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## 11. Optional: PostgreSQL Setup

For production with multiple users, PostgreSQL is recommended:

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE picoblog;
CREATE USER picoblog_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE picoblog TO picoblog_user;
\q

# Update .env
DATABASE_URL=postgresql://picoblog_user:secure-password@localhost/picoblog

# Install PostgreSQL adapter
.venv/bin/pip install psycopg2-binary

# Initialize database
.venv/bin/flask db upgrade
```

## Support

For issues, check:
- Application logs: `/var/log/picoblog/`
- Nginx logs: `/var/log/nginx/`
- Systemd journal: `sudo journalctl -u picoblog`

---

**Deployment complete!** Your PicoBlog instance should now be running securely at `https://your-domain.com`.
