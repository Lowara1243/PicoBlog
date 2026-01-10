# PicoBlog - Setup Instructions

## Prerequisites

Before you begin, make sure you have:
- **Python 3.10+** installed
- **Node.js 16+** and npm installed (required for Tailwind CSS compilation)
- **uv** Python package installer: `pip install uv`

## Quick Start Guide

### 1. Install Dependencies

#### Python Dependencies
```bash
# Make sure you have Python 3.10+ installed
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

#### Node Dependencies (for Tailwind CSS)
```bash
npm install  # Installs @tailwindcss/cli, autoprefixer, postcss, and tailwindcss
```

**Note:** PicoBlog uses Tailwind CSS 4.x which requires the separate `@tailwindcss/cli` package. This is automatically installed via `npm install`.

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Edit .env and replace SECRET_KEY with the generated key
```

### 3. Build Tailwind CSS

```bash
# Build the CSS (one-time)
npm run build:css

# OR watch for changes during development
npm run watch:css
```

### 4. Initialize Database

```bash
export FLASK_APP=app
flask db upgrade
```

### 5. Create Admin User

```bash
flask shell
```

Then in the Flask shell:
```python
from app import db
from app.models import User

admin = User(username='admin', email='admin@example.com', is_admin=True)
admin.set_password(r'change_this_password')  # CHANGE THIS!
db.session.add(admin)
db.session.commit()
exit()
```

### 6. Run the Application

Choose one of the following methods:

#### Option A: Using run.py
```bash
python run.py
```

#### Option B: Using Flask CLI
```bash
export FLASK_APP=app
flask run
```

The application will be available at http://127.0.0.1:5000/

### 7. Access Admin Panel

1. Navigate to http://127.0.0.1:5000/login
2. Login with the admin credentials you created
3. Click "Admin" in the navigation bar

## Features Implemented

### ✅ Security
- Tag-based access control for posts
- HTML sanitization (XSS protection)
- Rate limiting on authentication endpoints
- Secure cookie configuration
- Admin-only user registration

### ✅ Core Functionality
- User management (create, edit, delete)
- Tag management (create, edit, delete)
- Post management with Markdown support
- Comment system with Markdown support
- Image upload functionality

### ✅ UI/UX
- Tailwind CSS (compiled, not CDN)
- Responsive design
- Clean, minimalist interface
- No JavaScript on blog pages (as per requirements)

## Production Deployment

### Important Security Checklist

1. **Environment Variables**
   - [ ] Generate and set a strong `SECRET_KEY`
   - [ ] Set `FLASK_ENV=production` in `.env`

2. **Configuration (config.py)**
   - [ ] Uncomment `SESSION_COOKIE_SECURE = True`
   - [ ] Uncomment `REMEMBER_COOKIE_SECURE = True`

3. **Web Server**
   - [ ] Use a production WSGI server (Gunicorn, uWSGI)
   - [ ] Set up Nginx as reverse proxy
   - [ ] Configure HTTPS/SSL certificates

4. **Dependencies**
   - [ ] Run `npm run build:css` to generate production CSS
   - [ ] Install all Python dependencies: `uv pip install -e .`
   - [ ] Install Flask-Limiter dependency is included

### Example Production Setup with Gunicorn

```bash
# Install gunicorn
uv pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 "app:app"
```

Then configure Nginx to proxy to port 8000.

## Troubleshooting

### "tailwindcss: command not found" error?
This happens if Node dependencies aren't installed. Run:
```bash
npm install
```
This will install the required `@tailwindcss/cli` package along with other dependencies.

### CSS not loading?
Make sure you've run `npm run build:css` to compile Tailwind CSS.

### Database errors?
Run `flask db upgrade` to apply migrations.

### Rate limit errors during testing?
The rate limits are:
- Login: 5 attempts per minute
- Register: 3 attempts per hour
- Comments: 10 per minute

Wait for the time window to reset, or adjust limits in `app/__init__.py`.

## Additional Notes

- Uploaded images are stored in `app/static/uploads/`
- Database is SQLite by default (stored in `data/app.db`)
- Markdown is supported in posts and comments
- All Markdown output is sanitized to prevent XSS attacks
- Anonymous users can only view posts without tags
- Authenticated users can only view posts with tags they have access to
- Admins can see all posts

## Need Help?

Check the following files for more information:
- `README.md` - Project overview
- `requirements.md` - Original project requirements (in Russian)
- `security_considerations.md` - Security documentation (in Russian)
