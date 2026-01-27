from flask import render_template, flash, redirect, url_for, request, abort, make_response, send_from_directory, current_app
import os
from app import db, limiter, main_bp  # Import main_bp, db and limiter
from app.forms import LoginForm, CommentForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post, Comment
from app.utils import safe_db_commit
from app.services.access_control import get_posts_for_user, user_can_view_post
from urllib.parse import urlsplit


@main_bp.route("/")
@main_bp.route("/index")
def index():
    """Display list of posts visible to current user."""
    if current_app.config.get("REQUIRE_LOGIN", True) and not current_user.is_authenticated:
        return redirect(url_for("main.login"))
    posts = get_posts_for_user(current_user)
    return render_template("index.html", title="Home", posts=posts)


@main_bp.route("/post/<int:post_id>", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def post(post_id):
    """Display individual post with comments."""
    if current_app.config.get("REQUIRE_LOGIN", True) and not current_user.is_authenticated:
        return redirect(url_for("main.login", next=url_for("main.post", post_id=post_id)))

    post = Post.query.get_or_404(post_id)

    # Check if user has access to view this post
    if not user_can_view_post(current_user, post):
        # If user is anonymous and post is tagged/private, redirect to login
        if not current_user.is_authenticated:
            return redirect(url_for("main.login", next=url_for("main.post", post_id=post.id)))
        
        # Hide drafts (404) vs forbidden access (403)
        if post.is_draft:
            abort(404)
        else:
            abort(403)

    # Handle comment submission
    form = CommentForm()
    if form.validate_on_submit():
        # Check if comments are enabled for this post
        if not post.comments_enabled:
            flash("Comments are disabled for this post.", "error")
            return redirect(url_for("main.post", post_id=post.id))  # Use blueprint name

        comment = Comment(body=form.body.data, post_id=post.id)

        # Only authenticated users can comment
        if current_user.is_authenticated:
            comment.user_id = current_user.id
            comment.author_name = current_user.username
        else:
            # This should not happen due to access control, but handle gracefully
            flash("You must be logged in to comment.", "error")
            return redirect(url_for("main.login"))  # Use blueprint name

        db.session.add(comment)
        if safe_db_commit(db.session, "Your comment has been posted!"):
            return redirect(url_for("main.post", post_id=post.id))  # Use blueprint name
        # If commit failed, error message already flashed by safe_db_commit

    # Get all comments for this post, ordered by timestamp
    comments = (
        Comment.query.filter_by(post_id=post.id).order_by(Comment.timestamp.asc()).all()
    )

    # Note: post.rendered_body and comment.rendered_body are now properties in models
    return render_template(
        "post.html", title=post.title, post=post, comments=comments, form=form
    )


@main_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))  # Use blueprint name
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password", "error")
            return redirect(url_for("main.login"))  # Use blueprint name
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("main.index")  # Use blueprint name
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@main_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.login"))  # Use blueprint name


# Public registration is disabled - only admins can register users via admin panel
# @main_bp.route("/register", methods=["GET", "POST"])
# @limiter.limit("3 per hour")
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('main.index'))
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data, email=form.email.data)
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Congratulations, you are now a registered user!', 'success')
#         return redirect(url_for('main.login'))
#     return render_template('register.html', title='Register', form=form)

@main_bp.route("/rss")
def rss_feed():
    """Generate RSS feed for posts visible to current user."""
    if current_app.config.get("REQUIRE_LOGIN", True) and not current_user.is_authenticated:
        abort(401)  # Unauthorized for RSS if login required
    
    # Use service to get posts this user is allowed to see
    posts = get_posts_for_user(current_user)
    # Exclude drafts from RSS feed (even for admins)
    visible_posts = [p for p in posts if not p.is_draft]
    # Limit to 20 latest posts
    visible_posts = visible_posts[:20]

    response = make_response(render_template("rss.xml", posts=visible_posts))
    response.headers["Content-Type"] = "application/rss+xml"
    return response


@main_bp.route("/toggle-theme")
def toggle_theme():
    """Toggle between light and dark theme using a cookie."""
    current_theme = request.cookies.get("theme", "light")
    new_theme = "dark" if current_theme == "light" else "light"

    response = redirect(request.referrer or url_for("main.index"))
    response.set_cookie("theme", new_theme, max_age=30 * 24 * 60 * 60, samesite="Lax")
    return response


@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(main_bp.root_path, "static", "assets"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
