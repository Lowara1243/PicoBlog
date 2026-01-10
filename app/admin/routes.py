from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.forms import (
    AdminRegistrationForm,
    AdminEditUserForm,
    AdminChangePasswordForm,
    TagForm,
    PostForm,
)
from app.models import User, Tag, Post, Comment
from app import db
from app.utils import save_uploaded_file, cleanup_unused_images, safe_db_commit
import os


@admin_bp.before_request
@login_required
def before_request():
    if not current_user.is_admin:
        flash("You do not have permission to access the admin panel.", "error")
        return redirect(url_for("index"))


@admin_bp.route("/admin")
def admin_dashboard():
    return render_template(
        "admin/dashboard.html",
        title="Admin Dashboard",
        User=User,
        Post=Post,
        Tag=Tag,
        Comment=Comment,
    )


@admin_bp.route("/admin/register_user", methods=["GET", "POST"])
def admin_register_user():
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        # Note: New users are always created as non-admin (is_admin=False by default)
        # To make a user admin, use Flask shell: user.is_admin = True
        email = form.email.data if form.email.data else None
        user = User(username=form.username.data, email=email)
        user.set_password(form.password.data)
        user.allowed_tags = form.allowed_tags.data
        db.session.add(user)
        if safe_db_commit(db.session, "User has been registered successfully!"):
            return redirect(url_for("admin.admin_dashboard"))
    return render_template(
        "admin/register_user.html", title="Register New User", form=form
    )


@admin_bp.route("/admin/users")
def admin_users():
    users = User.query.all()
    return render_template("admin/users.html", title="Manage Users", users=users)


@admin_bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminEditUserForm(original_username=user.username, original_email=user.email)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data if form.email.data else None
        # Note: is_admin status cannot be changed via web interface
        # To change admin status, use Flask shell: user.is_admin = True/False
        user.allowed_tags = form.allowed_tags.data
        if safe_db_commit(db.session, "User has been updated successfully!"):
            return redirect(url_for("admin.admin_users"))
    elif request.method == "GET":
        form.username.data = user.username
        form.email.data = user.email
        form.allowed_tags.data = user.allowed_tags.all()
    return render_template(
        "admin/edit_user.html", title="Edit User", form=form, user=user
    )


@admin_bp.route("/admin/users/<int:user_id>/change_password", methods=["GET", "POST"])
def admin_change_user_password(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminChangePasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        if safe_db_commit(
            db.session,
            f"Password for user {user.username} has been updated successfully!",
        ):
            return redirect(url_for("admin.admin_users"))
    return render_template(
        "admin/change_password.html", title="Change Password", form=form, user=user
    )


@admin_bp.route("/admin/tags")
def admin_tags():
    tags = Tag.query.all()
    return render_template("admin/tags.html", title="Manage Tags", tags=tags)


@admin_bp.route("/admin/tags/new", methods=["GET", "POST"])
def admin_create_tag():
    try:
        current_app.logger.info("Entering admin_create_tag route.")
        form = TagForm()
        current_app.logger.info("TagForm instantiated successfully.")

        if form.validate_on_submit():
            current_app.logger.info("Form validation successful.")
            tag = Tag(name=form.name.data, is_master=form.is_master.data)
            db.session.add(tag)
            if safe_db_commit(db.session, "Tag has been created successfully!"):
                return redirect(url_for("admin.admin_tags"))

        current_app.logger.info("Rendering create_edit_tag.html template.")
        return render_template(
            "admin/create_edit_tag.html", title="Create New Tag", form=form
        )
    except Exception as e:
        current_app.logger.error(
            f"An error occurred in admin_create_tag: {e}", exc_info=True
        )
        # Re-raise the exception to trigger Flask's default 500 handler
        raise


@admin_bp.route("/admin/tags/<int:tag_id>/edit", methods=["GET", "POST"])
def admin_edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    form = TagForm(original_name=tag.name)
    if form.validate_on_submit():
        tag.name = form.name.data
        tag.is_master = form.is_master.data
        if safe_db_commit(db.session, "Tag has been updated successfully!"):
            return redirect(url_for("admin.admin_tags"))
    elif request.method == "GET":
        form.name.data = tag.name
        form.is_master.data = tag.is_master
    return render_template(
        "admin/create_edit_tag.html", title="Edit Tag", form=form, tag=tag
    )


@admin_bp.route("/admin/tags/<int:tag_id>/delete", methods=["POST"])
def admin_delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    safe_db_commit(db.session, "Tag has been deleted successfully!")
    return redirect(url_for("admin.admin_tags"))


@admin_bp.route("/admin/posts")
def admin_posts():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("admin/posts.html", title="Manage Posts", posts=posts)


@admin_bp.route("/admin/posts/new", methods=["GET", "POST"])
def admin_create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data, author=current_user)
        post.tags = form.tags.data

        post.comments_enabled = form.comments_enabled.data
        # Determine if draft based on which button was clicked
        post.is_draft = form.save_draft.data
        db.session.add(post)
        success_msg = (
            "Draft has been saved successfully!"
            if post.is_draft
            else "Post has been published successfully!"
        )
        if safe_db_commit(db.session, success_msg):
            return redirect(url_for("admin.admin_posts"))
    all_tags = Tag.query.all()
    return render_template(
        "admin/create_edit_post.html",
        title="Create New Post",
        form=form,
        all_tags=all_tags,
    )


@admin_bp.route("/admin/posts/<int:post_id>/edit", methods=["GET", "POST"])
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.tags = form.tags.data

        post.comments_enabled = form.comments_enabled.data
        # Determine if draft based on which button was clicked
        post.is_draft = form.save_draft.data
        success_msg = (
            "Draft has been saved successfully!"
            if post.is_draft
            else "Post has been updated successfully!"
        )
        if safe_db_commit(db.session, success_msg):
            return redirect(url_for("admin.admin_posts"))
    elif request.method == "GET":
        form.title.data = post.title
        form.body.data = post.body
        form.tags.data = post.tags.all()

        form.comments_enabled.data = post.comments_enabled
    all_tags = Tag.query.all()
    return render_template(
        "admin/create_edit_post.html",
        title="Edit Post",
        form=form,
        post=post,
        all_tags=all_tags,
    )


@admin_bp.route("/admin/posts/<int:post_id>/delete", methods=["POST"])
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    safe_db_commit(db.session, "Post has been deleted successfully!")
    return redirect(url_for("admin.admin_posts"))


@admin_bp.route("/admin/upload", methods=["POST"])
def admin_upload_image():
    """Upload an image and return the URL."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = save_uploaded_file(file)

    if filename:
        # Return the URL to the uploaded file
        file_url = url_for("static", filename=f"uploads/{filename}")
        return jsonify({"url": file_url, "filename": filename}), 200
    else:
        return jsonify(
            {"error": "Invalid file type. Allowed types: png, jpg, jpeg, gif, webp"}
        ), 400


@admin_bp.route("/admin/images")
def admin_images():
    """List all uploaded images."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # Get all image files from the upload folder
    if os.path.exists(upload_folder):
        images = [
            f
            for f in os.listdir(upload_folder)
            if os.path.isfile(os.path.join(upload_folder, f))
            and f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
        ]
    else:
        images = []

    # Create URLs for each image
    image_data = [
        {"filename": img, "url": url_for("static", filename=f"uploads/{img}")}
        for img in images
    ]

    return render_template(
        "admin/images.html", title="Manage Images", images=image_data
    )


@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        flash("You cannot delete your own account!", "error")
        return redirect(url_for("admin.admin_users"))

    db.session.delete(user)
    safe_db_commit(db.session, "User has been deleted successfully!")
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/admin/images/cleanup", methods=["POST"])
def admin_cleanup_images():
    """Clean up unused images."""
    deleted_count, deleted_files = cleanup_unused_images()

    if deleted_count > 0:
        flash(f"Successfully deleted {deleted_count} unused image(s).", "success")
    else:
        flash("No unused images found.", "success")

    return redirect(url_for("admin.admin_images"))
