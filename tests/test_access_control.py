import unittest
from app import create_app, db
from app.models import User, Post, Tag
from app.services.access_control import get_posts_for_user, user_can_view_post
from config import Config
from flask_login import AnonymousUserMixin


class MockAnonymousUser(AnonymousUserMixin):
    """A mock anonymous user for testing purposes."""

    def __init__(self):
        # AnonymousUserMixin already provides is_authenticated=False, is_active=False, get_id=None
        self.is_admin = False

    @property
    def allowed_tags(self):
        # Mimic the relationship property, which returns a list-like object
        return []

    def __repr__(self):
        return "<AnonymousUser>"


class TestConfig(Config):
    """Test-specific configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test_secret_key"
    WTF_CSRF_ENABLED = False


class AccessControlTestCase(unittest.TestCase):
    """Test suite for access control logic based on tag `is_master` field."""

    def setUp(self):
        """Set up the test environment."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # --- Create Users ---
        self.admin_user = User(
            username="admin", email="admin@example.com", is_admin=True
        )
        self.admin_user.set_password("adminpass")

        self.user_a = User(
            username="user_a", email="user_a@example.com", is_admin=False
        )
        self.user_a.set_password("user_a_pass")

        self.user_b = User(
            username="user_b", email="user_b@example.com", is_admin=False
        )
        self.user_b.set_password("user_b_pass")

        self.user_c = User(
            username="user_c", email="user_c@example.com", is_admin=False
        )
        self.user_c.set_password("user_c_pass")

        db.session.add_all([self.admin_user, self.user_a, self.user_b, self.user_c])
        db.session.commit()

        # --- Create Tags ---
        self.tag_master = Tag(name="secret", is_master=True)  # This is the master tag
        self.tag_regular = Tag(name="drawing", is_master=False)
        self.tag_another_regular = Tag(name="tech", is_master=False)

        db.session.add_all(
            [self.tag_master, self.tag_regular, self.tag_another_regular]
        )
        db.session.commit()

        # --- Assign Tags to Users ---
        self.user_a.allowed_tags.append(self.tag_regular)
        self.user_a.allowed_tags.append(self.tag_another_regular)

        self.user_b.allowed_tags.append(self.tag_master)

        self.user_c.allowed_tags.append(self.tag_master)
        self.user_c.allowed_tags.append(self.tag_regular)

        db.session.commit()

        # --- Create Posts ---
        self.post_public = Post(
            title="Public Post", body="Content", author=self.admin_user
        )
        self.post_regular = Post(
            title="Regular Post", body="Content", author=self.admin_user
        )
        self.post_master_only = Post(
            title="Master Only Post", body="Content", author=self.admin_user
        )
        self.post_master_and_regular = Post(
            title="Master and Regular Post", body="Content", author=self.admin_user
        )
        self.post_draft = Post(
            title="Draft Post", body="Content", author=self.admin_user, is_draft=True
        )

        db.session.add_all(
            [
                self.post_public,
                self.post_regular,
                self.post_master_only,
                self.post_master_and_regular,
                self.post_draft,
            ]
        )
        db.session.commit()

        # --- Assign Tags to Posts ---
        self.post_regular.tags.append(self.tag_regular)
        self.post_master_only.tags.append(self.tag_master)
        self.post_master_and_regular.tags.append(self.tag_master)
        self.post_master_and_regular.tags.append(self.tag_regular)

        db.session.commit()

    def tearDown(self):
        """Tear down the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_admin_sees_all(self):
        """Admin should see all posts, including drafts."""
        posts = get_posts_for_user(self.admin_user)
        self.assertIn(self.post_public, posts)
        self.assertIn(self.post_regular, posts)
        self.assertIn(self.post_master_only, posts)
        self.assertIn(self.post_master_and_regular, posts)
        self.assertIn(self.post_draft, posts)

    def test_anonymous_user_sees_nothing(self):
        """Anonymous user should see no posts."""
        anon_user = MockAnonymousUser()
        posts = get_posts_for_user(anon_user)
        self.assertEqual(len(posts), 0)

    def test_user_with_regular_tags_access(self):
        """Test access for a user with only regular tags."""
        posts = get_posts_for_user(self.user_a)

        self.assertIn(self.post_public, posts, "User should see public posts")
        self.assertIn(
            self.post_regular, posts, "User should see post with their regular tag"
        )
        self.assertNotIn(
            self.post_master_only,
            posts,
            "User should NOT see post with only a master tag",
        )
        self.assertNotIn(
            self.post_master_and_regular,
            posts,
            "User should NOT see post with a master tag, even if they have a regular tag on it",
        )
        self.assertNotIn(self.post_draft, posts, "User should NOT see draft posts")

    def test_user_with_master_tag_access(self):
        """Test access for a user with a master tag."""
        posts = get_posts_for_user(self.user_b)

        self.assertIn(self.post_public, posts, "User should see public posts")
        self.assertNotIn(
            self.post_regular,
            posts,
            "User should NOT see post with a regular tag they don't have",
        )
        self.assertIn(
            self.post_master_only,
            posts,
            "User should see post with a master tag they have",
        )
        self.assertNotIn(
            self.post_master_and_regular,
            posts,
            "User should NOT see post with both master and regular tags if they only have the master tag",
        )
        self.assertNotIn(self.post_draft, posts, "User should NOT see draft posts")

    def test_user_with_master_and_regular_tag_access(self):
        """Test access for a user with both master and regular tags."""
        posts = get_posts_for_user(self.user_c)

        self.assertIn(self.post_public, posts, "User should see public posts")
        self.assertIn(
            self.post_master_and_regular,
            posts,
            "User should see post with master and regular tags they have",
        )
        self.assertIn(
            self.post_master_only, posts, "User should see post with only a master tag"
        )
        self.assertIn(
            self.post_regular,
            posts,
            "User should see post with a regular tag they have",
        )

    def test_individual_post_view_logic(self):
        """Test the user_can_view_post function directly."""
        anon_user = MockAnonymousUser()

        # Admin can view all
        self.assertTrue(user_can_view_post(self.admin_user, self.post_draft))
        self.assertTrue(
            user_can_view_post(self.admin_user, self.post_master_and_regular)
        )

        # User A (regular tags only)
        self.assertTrue(user_can_view_post(self.user_a, self.post_public))
        self.assertTrue(user_can_view_post(self.user_a, self.post_regular))
        self.assertFalse(user_can_view_post(self.user_a, self.post_master_only))
        self.assertFalse(user_can_view_post(self.user_a, self.post_master_and_regular))

        # User B (master tag)
        self.assertTrue(user_can_view_post(self.user_b, self.post_public))
        self.assertFalse(user_can_view_post(self.user_b, self.post_regular))
        self.assertTrue(user_can_view_post(self.user_b, self.post_master_only))
        self.assertFalse(user_can_view_post(self.user_b, self.post_master_and_regular))

        # User C (master and regular tag)
        self.assertTrue(user_can_view_post(self.user_c, self.post_public))
        self.assertTrue(user_can_view_post(self.user_c, self.post_regular))
        self.assertTrue(user_can_view_post(self.user_c, self.post_master_only))
        self.assertTrue(user_can_view_post(self.user_c, self.post_master_and_regular))

        # Anonymous user
        self.assertFalse(user_can_view_post(anon_user, self.post_public))
        self.assertFalse(user_can_view_post(anon_user, self.post_master_and_regular))


if __name__ == "__main__":
    unittest.main()
