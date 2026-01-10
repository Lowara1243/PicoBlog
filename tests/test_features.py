import unittest
from app import create_app, db
from app.models import User, Post, Tag
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test_secret_key"
    WTF_CSRF_ENABLED = False

class RSSAndThemeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_rss_feed_anonymous(self):
        # Anonymous users should be redirected to login
        response = self.client.get("/rss")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_rss_feed_authorized(self):
        # Create user and log in
        user = User(username="testuser", email="test@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        
        # Log in
        self.client.post("/login", data=dict(username="testuser", password="password"), follow_redirects=True)
        
        response = self.client.get("/rss")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/rss+xml")
        self.assertIn(b"<title>PicoBlog</title>", response.data)

    def test_rss_feed_with_posts(self):
        # Create a public post
        admin = User(username="admin", email="admin@example.com")
        admin.set_password("adminpass")
        db.session.add(admin)
        post = Post(title="Public Title", body="Public Body", author=admin)
        db.session.add(post)
        db.session.commit()

        # Log in as admin
        self.client.post("/login", data=dict(username="admin", password="adminpass"), follow_redirects=True)

        response = self.client.get("/rss")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Public Title", response.data)
        self.assertIn(b"Public Body", response.data)

    def test_rss_feed_with_tagged_posts(self):
        # Create user and tag
        user = User(username="user_t", email="user_t@example.com")
        user.set_password("password")
        tag = Tag(name="secret")
        db.session.add_all([user, tag])
        user.allowed_tags.append(tag)
        
        # Create tagged post
        admin = User(username="admin_s", email="admin_s@example.com")
        admin.set_password("adminpass")
        db.session.add(admin)
        post = Post(title="Secret Title", body="Secret Body", author=admin)
        post.tags.append(tag)
        db.session.add(post)
        db.session.commit()

        # Log in as user
        self.client.post("/login", data=dict(username="user_t", password="password"), follow_redirects=True)

        response = self.client.get("/rss")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Secret Title", response.data)
        self.assertIn(b"Secret Body", response.data)

    def test_theme_toggle(self):
        # Initial theme toggle (light -> dark)
        response = self.client.get("/toggle-theme", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        # Check if cookie is set
        self.assertIn("theme=dark", response.headers.get("Set-Cookie"))

        # Toggle again (dark -> light)
        self.client.set_cookie("theme", "dark")
        response = self.client.get("/toggle-theme", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("theme=light", response.headers.get("Set-Cookie"))

if __name__ == "__main__":
    unittest.main()
