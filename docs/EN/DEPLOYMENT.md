# PicoBlog - Production Deployment Guide

This guide covers deploying PicoBlog to a production server with Nginx, Gunicorn, and SSL certificates.

## Prerequisites

- Ubuntu/Debian server with root access
- Domain name pointing to your server's IP
- Git
- Python 3.10+
- Node.js 18+ (for building CSS)

## 1. Server Setup

### Install system dependencies:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx nodejs npm
```

### Create application directory and clone repository:

```bash
# Create parent directory
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
cd /var/www

# Clone the repository
git clone https://github.com/Lowara1243/PicoBlog.git
cd PicoBlog
```
> **Note:** Replace `<YOUR_REPOSITORY_URL>` with the actual URL of your Git repository.

## 2. Application Setup

### Create Python virtual environment:

```bash
cd /var/www/PicoBlog
python3 -m venv .venv
source .venv/bin/activate
```

### Install Python dependencies:

```bash
# If using uv (recommended):
pip install uv
uv sync


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
DATABASE_URL=sqlite:////var/www/PicoBlog/data/app.db

# Environment
FLASK_ENV=production
```

### Create data and upload directories:

```bash
mkdir -p /var/www/PicoBlog/data
mkdir -p /var/www/PicoBlog/app/static/uploads
chmod 755 /var/www/PicoBlog/data /var/www/PicoBlog/app/static/uploads
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
sudo nano /etc/systemd/system/PicoBlog.service
```

Add the following content:

```ini
[Unit]
Description=PicoBlog Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/PicoBlog
Environment="PATH=/var/www/PicoBlog/.venv/bin"
ExecStart=/var/www/PicoBlog/.venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/PicoBlog/access.log \
    --error-logfile /var/log/PicoBlog/error.log \
    --log-level info \
    "app:app"

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

### Create log directory:

```bash
sudo mkdir -p /var/log/PicoBlog
sudo chown www-data:www-data /var/log/PicoBlog
```

### Set proper permissions:

```bash
sudo chown -R www-data:www-data /var/www/PicoBlog
sudo chmod -R 755 /var/www/PicoBlog
```

### Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable PicoBlog
sudo systemctl start PicoBlog
sudo systemctl status PicoBlog
```

## 4. Nginx Configuration

### Copy nginx configuration:

```bash
sudo cp /var/www/PicoBlog/nginx.conf /etc/nginx/sites-available/PicoBlog
```

### Edit configuration with your domain:

```bash
sudo nano /etc/nginx/sites-available/PicoBlog
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
sudo ln -s /etc/nginx/sites-available/PicoBlog /etc/nginx/sites-enabled/
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

Edit `/var/www/PicoBlog/config.py` and uncomment:

```python
SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
REMEMBER_COOKIE_SECURE = True
```

### Restart application:

```bash
sudo systemctl restart PicoBlog
```

## 7. Verify Deployment

### Check services:

```bash
sudo systemctl status PicoBlog
sudo systemctl status nginx
```

### Check logs:

```bash
# Application logs
sudo tail -f /var/log/PicoBlog/error.log

# Nginx logs
sudo tail -f /var/log/nginx/PicoBlog_error.log
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
cd /var/www/PicoBlog
git pull origin main
source .venv/bin/activate

# Update dependencies
uv sync

# Rebuild CSS
npm run build:css

# Apply database migrations
.venv/bin/flask db upgrade

# Set correct permissions and restart
sudo chown -R www-data:www-data /var/www/PicoBlog
sudo systemctl restart PicoBlog
```

### Backup database:

```bash
# For SQLite
sudo cp /var/www/PicoBlog/data/app.db /var/backups/PicoBlog-$(date +%Y%m%d).db

# For PostgreSQL
pg_dump PicoBlog > /var/backups/PicoBlog-$(date +%Y%m%d).sql
```

### View logs:

```bash
# Application logs
sudo journalctl -u PicoBlog -f

# Nginx access logs
sudo tail -f /var/log/nginx/PicoBlog_access.log
```

## 9. Troubleshooting

### Application won't start:

```bash
sudo journalctl -u PicoBlog -n 50
```

Check for:
- Missing `SECRET_KEY` in `.env`
- Database connection errors
- Permission issues

### 502 Bad Gateway:

- Check Gunicorn is running: `sudo systemctl status PicoBlog`
- Check port 8000 is listening: `sudo netstat -tlnp | grep 8000`
- Check nginx error log: `sudo tail /var/log/nginx/PicoBlog_error.log`

### Static files not loading:

- Verify path in `nginx.conf` matches actual location
- Check permissions: `ls -la /var/www/PicoBlog/app/static/`
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
CREATE DATABASE PicoBlog;
CREATE USER PicoBlog_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE PicoBlog TO PicoBlog_user;
\q

# Update .env
DATABASE_URL=postgresql://PicoBlog_user:secure-password@localhost/PicoBlog

# Install PostgreSQL adapter
.venv/bin/pip install psycopg2-binary

# Initialize database
.venv/bin/flask db upgrade
```

## Support

For issues, check:
- Application logs: `/var/log/PicoBlog/`
- Nginx logs: `/var/log/nginx/`
- Systemd journal: `sudo journalctl -u PicoBlog`

---

**Deployment complete!** Your PicoBlog instance should now be running securely at `https://your-domain.com`.
