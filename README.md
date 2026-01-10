# PicoBlog

**English** | [Русский](README.ru.md)

PicoBlog is a lightweight and performant blog platform, designed as an alternative to WriteFreely, with a focus on simplicity and efficiency, especially for deployment on devices like Raspberry Pi.

## Features

*   **User Management:** Admin-only user registration and role assignment.
*   **Access Control:** Administrators can assign tags to users to control which blog posts they can view.
*   **Tag Management:** Administrators can create, edit, and delete tags.
*   **Post Management:** Administrators can create, edit, and delete blog posts with Markdown support.
*   **Markdown Rendering:** Blog post content is written in Markdown and rendered to HTML for display.
*   **Minimalist Design:** Built with a focus on a clean and simple user interface, styled using Tailwind CSS (compiled, no CDN).
*   **Copy Button:** One-click copying for code blocks in posts.
*   **RSS Feed:** Standard RSS 2.0 feed for public posts.
*   **Dark Mode:** JavaScript-free dark mode support with cookie persistence.

## Tag-based Access Control

PicoBlog implements a refined tag-based access control system:

1.  **Public vs. Private Access:** Controlled by the `REQUIRE_LOGIN` environment variable.
    *   `REQUIRE_LOGIN=True` (default): Only logged-in (authenticated) users can view any posts.
    *   `REQUIRE_LOGIN=False`: Blog posts without any tags are visible to everyone (including anonymous guests).

2.  **Protected Posts (Tags Required):** Any post with at least one tag always requires authentication and specific permissions.

3.  **Posts with Regular Tags (OR Logic):**
    *   If a post has *only* regular tags (i.e., no master tags), an authenticated user can view it if they have been assigned *at least one* of the tags that are applied to that post.
    *   This works as an "OR" condition: possessing `Tag A` OR `Tag B` grants access if the post has `Tag A` and `Tag B`.

4.  **Posts with Master Tags (AND Logic):**
    *   Some tags can be designated as "Master Tags" (configured with `is_master=True` in the admin panel). These tags enforce stricter access.
    *   If a post has *any* Master Tags, an authenticated user must possess *all* of the Master Tags applied to that post to gain access.
    *   This works as an "AND" condition: possessing `Master Tag X` AND `Master Tag Y` grants access if the post has `Master Tag X` and `Master Tag Y`.

5.  **Posts with Mixed Tags (Master AND Regular OR Logic):**
    *   If a post has *both* Master Tags and regular tags, an authenticated user must satisfy *both* conditions:
        *   Possess *all* of the Master Tags applied to the post (AND logic).
        *   Possess *at least one* of the regular tags applied to the post (OR logic).
    *   Failure to meet either condition will deny access.

This system ensures granular control over content visibility, allowing for both broad access to general topics and restricted access to sensitive material.

## Setup (Linux)

Follow these instructions to set up and run PicoBlog on a Linux system.

### Prerequisites

*   **Python 3.10+:** Ensure you have Python 3.10 or a newer version installed.
*   **uv:** A fast Python package installer and resolver. If you don't have it, you can install it with `pip install uv`.
*   **Node.js 16+:** Required for building Tailwind CSS. Install from [nodejs.org](https://nodejs.org).

### 1. Clone the Repository

```bash
git clone https://github.com/Lowara1243/PicoBlog.git
cd PicoBlog
```

### 2. Set up Virtual Environment and Install Python Dependencies

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
uv venv
source .venv/bin/activate
uv sync
```

> [!TIP]
> **Termux (Android) users:** To install image processing dependencies on ARM, run:
> `pkg install python-pillow`
> or ensure you have system libraries installed: `pkg install libjpeg-turbo libpng libwebp`

### 3. Install Node.js Dependencies and Build CSS

PicoBlog uses Tailwind CSS which needs to be compiled.

```bash
npm install
npm run build:css
```

For development with automatic CSS rebuilding:
```bash
npm run watch:css
```

### 4. Environment Variables

Create a `.env` file in the project root directory based on `.env.example` and fill in your secret key and database URL. For development, you can use the provided defaults.

```bash
cp .env.example .env
# Open .env with your editor and modify if necessary
```

### 5. Database Setup

Apply the database migrations to set up the database schema.

```bash
export FLASK_APP=app
flask db upgrade
```

### 6. Create an Admin User

An admin user is required to access the administration panel and manage users, tags, and posts. You can create one using the Flask shell.

```bash
export FLASK_APP=app
flask shell
```

Inside the Flask shell, run the following commands:

```python
from app import db
from app.models import User

admin_user = User.query.filter_by(username='admin').first()
if admin_user is None:
    admin_user = User(username='admin', email='admin@example.com', is_admin=True)
    admin_user.set_password(r'adminpassword') # IMPORTANT: Change this to a strong, unique password!
    db.session.add(admin_user)
    db.session.commit()
    print('Admin user created.')
else:
    print('Admin user already exists.')
exit()
```

### 7. Run the Application

```bash
export FLASK_APP=app
flask run
```

The application will typically run on `http://127.0.0.1:5000/`.

## Admin Panel Access

1.  Navigate to `http://127.0.0.1:5000/login` and log in with the admin credentials you created.
2.  Once logged in, you will see an "Admin" link in the navigation bar. Click on it to access the admin dashboard.
3.  From the admin dashboard, you can manage users, tags, and posts.

## Administrative Tasks via Flask Shell

Some critical administrative tasks can only be performed via the Flask shell for security reasons. Below are common scenarios.

### Resetting a User's Password

If a user forgot their password or you need to reset it:

```bash
export FLASK_APP=app
flask shell
```

```python
from app import db
from app.models import User

# Find the user by username
user = User.query.filter_by(username='username_here').first()

if user:
    user.set_password(r'new_secure_password')
    db.session.commit()
    print(f'Password for {user.username} has been reset.')
else:
    print('User not found.')

exit()
```

### Changing the Administrator

To transfer admin rights to another user or replace the current administrator:

```bash
export FLASK_APP=app
flask shell
```

```python
from app import db
from app.models import User

# Remove admin rights from current admin
old_admin = User.query.filter_by(username='old_admin_username').first()
if old_admin:
    old_admin.is_admin = False
    print(f'Admin rights removed from {old_admin.username}')

# Grant admin rights to new user
new_admin = User.query.filter_by(username='new_admin_username').first()
if new_admin:
    new_admin.is_admin = True
    print(f'Admin rights granted to {new_admin.username}')

db.session.commit()
exit()
```

**Note:** Admin status cannot be changed through the web interface. Only one administrator is recommended for security and simplicity.

### Resetting the Database Completely

**WARNING:** This will delete ALL data including users, posts, tags, and comments. Use with extreme caution!

```bash
# Stop the application if it's running

# Remove the database file
rm data/app.db

# Remove uploaded files (optional)
rm -rf app/static/uploads/*

# Recreate the database schema
export FLASK_APP=app
flask db upgrade

# Create a new admin user (see step 6 in setup instructions)
flask shell
```

```python
from app import db
from app.models import User

admin = User(username='admin', email='admin@example.com', is_admin=True)
admin.set_password(r'your_secure_password')
db.session.add(admin)
db.session.commit()
print('Database reset complete. New admin user created.')
exit()
```

After resetting, restart the application.

For detailed deployment instructions (Nginx, Gunicorn, systemd), see **[docs/EN/DEPLOYMENT.md](docs/EN/DEPLOYMENT.md)**.

---

For more technical details, check out:
- [Specifications](docs/EN/specifications.md)
- [Deployment Guide](docs/EN/DEPLOYMENT.md)
