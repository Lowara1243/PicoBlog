"""Utility functions for the application."""

import os
import secrets
import imghdr
import re
from flask import current_app, flash
import markdown2
import bleach
from PIL import Image


def safe_db_commit(session, success_message=None, error_message=None):
    """
    Safely commit database changes with error handling.

    Args:
        session: Database session to commit
        success_message (str, optional): Flash message on successful commit
        error_message (str, optional): Flash message on error (default: generic message)

    Returns:
        bool: True if commit succeeded, False if it failed
    """
    try:
        session.commit()
        if success_message:
            flash(success_message, "success")
        return True
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Database commit failed: {e}")
        if error_message:
            flash(error_message, "error")
        else:
            flash("An error occurred. Please try again.", "error")
        return False


def render_markdown(text):
    """
    Render Markdown to HTML with syntax highlighting and sanitize the output to prevent XSS attacks.

    Markdown2 automatically uses Pygments for syntax highlighting when it's installed.
    The CSS styles for Pygments classes are included in the compiled output.css.

    Args:
        text (str): Markdown text to render

    Returns:
        str: Sanitized HTML output with syntax-highlighted code blocks
    """

    # Inject temporary language markers for fenced code blocks
    # This allows the frontend to identify the language of each block
    def inject_lang_marker(match):
        lang = match.group(1)
        if lang:
            return (
                f'<span class="code-lang-marker" data-lang="{lang}"></span>\n\n'
                + match.group(0)
            )
        return match.group(0)

    text_with_markers = re.sub(
        r"^```(\w+)", inject_lang_marker, text, flags=re.MULTILINE
    )

    # Render Markdown to HTML with comprehensive extras
    # markdown2 will automatically use Pygments for syntax highlighting when available
    html = markdown2.markdown(
        text_with_markers,
        extras=[
            "fenced-code-blocks",  # Enable ``` code blocks (auto-uses Pygments if available)
            "tables",  # Enable Markdown tables
            "strike",  # Enable ~~strikethrough~~
            "break-on-newline",  # Preserve single line breaks
            "header-ids",  # Add IDs to headers for linking
            "cuddled-lists",  # Allow lists without blank line before them
        ],
    )

    # Then sanitize the HTML to prevent XSS (using config values)
    clean_html = bleach.clean(
        html,
        tags=current_app.config["MARKDOWN_ALLOWED_TAGS"],
        attributes=current_app.config["MARKDOWN_ALLOWED_ATTRIBUTES"],
        protocols=current_app.config["MARKDOWN_ALLOWED_PROTOCOLS"],
        strip=True,  # Strip disallowed tags instead of escaping them
    )

    return clean_html


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.

    Args:
        filename (str): The name of the uploaded file

    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def validate_image(file_stream):
    """
    Validate that the uploaded file is actually an image by checking its content.

    Uses magic numbers (file headers) to verify the actual file type,
    preventing malicious files with valid extensions from being uploaded.

    Args:
        file_stream: File stream to validate

    Returns:
        bool: True if the file is a valid image, False otherwise
    """
    # Save current position
    pos = file_stream.tell()

    # Read header for validation
    header = file_stream.read(512)

    # Reset stream position
    file_stream.seek(pos)

    # Check actual image format using magic numbers
    format = imghdr.what(None, header)

    # Verify format matches allowed extensions
    allowed_formats = {"png", "jpeg", "gif", "webp"}
    return format in allowed_formats


def save_uploaded_file(file):
    """
    Save an uploaded file with a secure random filename.

    Args:
        file: The FileStorage object from the request

    Returns:
        str: The filename of the saved file, or None if validation fails
    """
    if not file or not allowed_file(file.filename):
        return None

    # Validate file content (check magic numbers)
    if not validate_image(file.stream):
        current_app.logger.warning(f"Invalid image file rejected: {file.filename}")
        return None

    # Generate a random filename with .webp extension
    random_hex = secrets.token_hex(8)
    filename = f"{random_hex}.webp"

    # Ensure the upload folder exists
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    try:
        # Open image with Pillow
        img = Image.open(file.stream)

        # Resize if image is too wide
        max_width = current_app.config.get("IMAGE_MAX_WIDTH", 1200)
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save as WebP with optimized quality
        # Pillow handles transparency automatically when saving to WEBP if mode is RGBA
        quality = current_app.config.get("IMAGE_QUALITY", 85)
        img.save(file_path, "WEBP", quality=quality, method=6)

        return filename
    except Exception as e:
        current_app.logger.error(f"Image processing failed for {file.filename}: {e}")
        return None


def cleanup_unused_images():
    """
    Find and delete images that are not referenced in any post or comment.

    Returns:
        tuple: (deleted_count, deleted_files) - number of deleted files and their names
    """
    from app.models import Post, Comment

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # Check if upload folder exists
    if not os.path.exists(upload_folder):
        return 0, []

    # Get all image files
    image_files = [
        f
        for f in os.listdir(upload_folder)
        if os.path.isfile(os.path.join(upload_folder, f))
        and f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    ]

    if not image_files:
        return 0, []

    # Find unused images by checking database for each file
    unused_images = []
    for image_file in image_files:
        # Check if filename is referenced in any post or comment body
        # Using contains() for case-sensitive substring matching
        post_count = Post.query.filter(Post.body.contains(image_file)).count()
        comment_count = Comment.query.filter(Comment.body.contains(image_file)).count()

        # If not referenced anywhere, mark as unused
        if post_count == 0 and comment_count == 0:
            unused_images.append(image_file)

    # Delete unused images
    deleted_count = 0
    deleted_files = []
    for image_file in unused_images:
        try:
            file_path = os.path.join(upload_folder, image_file)
            os.remove(file_path)
            deleted_count += 1
            deleted_files.append(image_file)
        except Exception as e:
            # Log error but continue with other files
            current_app.logger.error(f"Error deleting {image_file}: {e}")

    return deleted_count, deleted_files
