from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Association table for Users and Tags
user_tags = db.Table(
    "user_tags",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
)

# Association table for Posts and Tags
post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    posts = db.relationship("Post", backref="author", lazy="dynamic")

    # Relationship to tags that the user is allowed to see
    allowed_tags = db.relationship(
        "Tag",
        secondary=user_tags,
        backref=db.backref("users", lazy="dynamic"),
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_tag_ids(self):
        """Get list of allowed tag IDs for this user."""
        return [tag.id for tag in self.allowed_tags]

    def can_view_post(self, post):
        """Check if this user can view a specific post."""
        from app.services.access_control import user_can_view_post

        return user_can_view_post(self, post)

    def __repr__(self):
        return f"<User {self.username}>"


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comments_enabled = db.Column(db.Boolean, default=True)
    is_draft = db.Column(db.Boolean, default=False, index=True)
    comments = db.relationship(
        "Comment", backref="post", lazy="dynamic", cascade="all, delete-orphan"
    )

    # Relationship to tags
    tags = db.relationship(
        "Tag",
        secondary=post_tags,
        backref=db.backref("posts", lazy="dynamic"),
        lazy="dynamic",
    )

    def get_tag_ids(self):
        """Get list of tag IDs for this post."""
        return [tag.id for tag in self.tags]

    def is_public(self):
        """Check if this post is public (has no tags)."""
        return not self.tags.all()

    @property
    def rendered_body(self):
        """Get HTML-rendered markdown body."""
        from app.utils import render_markdown

        return render_markdown(self.body)

    def is_visible_to_user(self, user):
        """Check if this post is visible to a user."""
        from app.services.access_control import user_can_view_post

        return user_can_view_post(user, self)

    def __repr__(self):
        return f"<Post {self.title}>"


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    is_master = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Tag {self.name}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id")
    )  # Optional: for registered users' comments
    author_name = db.Column(db.String(64))  # For guest comments

    @property
    def rendered_body(self):
        """Get HTML-rendered markdown body."""
        from app.utils import render_markdown

        return render_markdown(self.body)

    @property
    def author_display_name(self):
        """Get display name for comment author."""
        if self.user_id:
            return self.author_name or "Unknown User"
        return self.author_name or "Anonymous"

    def __repr__(self):
        return f"<Comment {self.body[:20]}...>"
