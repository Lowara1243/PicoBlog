from flask import current_app
from app.models import Post


def user_can_view_post(user, post):
    """
    Check if a user can view a specific post.

    Args:
        user: Current user (can be anonymous via current_user)
        post: Post object to check access for

    Returns:
        bool: True if user can view the post, False otherwise

    Access Rules:
        - Admins can see all posts.
        - Drafts are only visible to admins.
        - If a user is not authenticated, they can't see any posts.
        - Posts with no tags are visible to all authenticated users.
        - If a post has master tags, the user MUST have ALL of them.
        - If a post has regular tags, the user MUST have at least ONE of them.
        - If a post has both, the user must satisfy both conditions.
    """
    # Admin bypass - can see everything
    if user.is_authenticated and user.is_admin:
        return True

    # Draft posts only visible to admins
    if post.is_draft:
        return False

    # Anonymous users handling
    if not user.is_authenticated:
        # If login is required (default), anonymous users see nothing
        if current_app.config.get("REQUIRE_LOGIN", True):
            return False
        # If login is NOT required, anonymous users can ONLY see untagged posts
        # (they continue to the tag check below, which handles untagged posts)

    post_tags = post.tags.all()

    # Posts with no tags are visible to all authenticated users (and guests if allowed)
    if not post_tags:
        return True

    # For posts with tags, anonymous users can NEVER see them
    if not user.is_authenticated:
        return False

    user_tag_ids = {t.id for t in user.allowed_tags.all()}
    master_tags_on_post = {t.id for t in post_tags if t.is_master}
    regular_tags_on_post = {t.id for t in post_tags if not t.is_master}

    # Master tag check (AND logic)
    if master_tags_on_post:
        if not master_tags_on_post.issubset(user_tag_ids):
            return False

    # Regular tag check (OR logic)
    if regular_tags_on_post:
        if not regular_tags_on_post.isdisjoint(user_tag_ids):
            # User has the required master tags (if any) and at least one regular tag
            return True
        else:
            # User has the master tags but is missing any of the regular tags
            return False

    # If we are here, it means the post had only master tags, and the user has them.
    if master_tags_on_post:
        return True

    # Fallback, should not be reached
    return False


def get_posts_for_user(user):
    """
    Get all posts visible to a user.

    Args:
        user: Current user (can be anonymous via current_user)

    Returns:
        list: List of Post objects visible to the user, ordered by timestamp descending.
    """
    # Admin bypass - see everything including drafts
    if user.is_authenticated and user.is_admin:
        return Post.query.order_by(Post.timestamp.desc()).all()

    # Anonymous users handling
    if not user.is_authenticated:
        # If login is required, they see nothing
        if current_app.config.get("REQUIRE_LOGIN", True):
            return []
        # Otherwise, they see only published, untagged posts
        # We handle this via the loop below to keep logic consistent

    # For authenticated users, filter posts in Python for correct logic
    all_posts = (
        Post.query.filter_by(is_draft=False).order_by(Post.timestamp.desc()).all()
    )

    visible_posts = []
    for post in all_posts:
        if user_can_view_post(user, post):
            visible_posts.append(post)

    return visible_posts
