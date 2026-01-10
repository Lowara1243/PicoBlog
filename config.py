import os
import secrets
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    REQUIRE_LOGIN = os.getenv("REQUIRE_LOGIN", "True").lower() == "true"

    # Generate random secret key for development if not set
    if SECRET_KEY is None:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError(
                "SECRET_KEY must be set in production environment. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        else:
            # Auto-generate for development (will change on restart)
            SECRET_KEY = secrets.token_hex(32)
            print(
                "WARNING: Using auto-generated SECRET_KEY for development. Set SECRET_KEY in .env for persistence."
            )

    # Database settings
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie settings (security)
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = "Lax"  # CSRF protection
    # Uncomment the following line when using HTTPS in production
    # SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS

    REMEMBER_COOKIE_HTTPONLY = True  # Prevent JavaScript access to remember cookie
    REMEMBER_COOKIE_SAMESITE = "Lax"
    # Uncomment the following line when using HTTPS in production
    # REMEMBER_COOKIE_SECURE = True

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "app", "static", "uploads"
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    IMAGE_MAX_WIDTH = 1200  # Automatically resize images to this width
    IMAGE_QUALITY = 85  # WebP quality (1-100)

    # Rate limiting configuration
    COMMENT_RATE_LIMIT = "10 per minute"
    LOGIN_RATE_LIMIT = "5 per minute"

    # Markdown rendering configuration
    MARKDOWN_ALLOWED_TAGS = [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "br",
        "code",
        "div",
        "em",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "span",
        "strong",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
        "del",
        "ins",
        "sup",
        "sub",
    ]

    MARKDOWN_ALLOWED_ATTRIBUTES = {
        "a": ["href", "title", "rel"],
        "abbr": ["title"],
        "acronym": ["title"],
        "img": ["src", "alt", "title", "width", "height", "class"],
        "div": ["class", "style"],  # Pygments wrapper
        "span": [
            "class",
            "style",
            "data-lang",
        ],  # Pygments syntax tokens and language markers
        "code": ["class", "style"],  # Code elements
        "pre": ["class", "style"],  # Code blocks
        "td": ["align"],
        "th": ["align"],
        "h1": ["id"],  # For header anchors
        "h2": ["id"],
        "h3": ["id"],
        "h4": ["id"],
        "h5": ["id"],
        "h6": ["id"],
    }

    MARKDOWN_ALLOWED_PROTOCOLS = ["http", "https", "mailto", "vless"]
