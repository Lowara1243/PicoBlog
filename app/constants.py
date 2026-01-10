"""Application-wide constants to avoid magic strings and improve maintainability."""


class FlashCategory:
    """Flash message categories for consistent messaging."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ImageFormat:
    """Allowed image file extensions and formats."""

    ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
    ALLOWED_FORMATS = {"png", "jpeg", "gif", "webp"}  # For imghdr validation


class Pagination:
    """Pagination settings for listing pages."""

    POSTS_PER_PAGE = 20
    COMMENTS_PER_PAGE = 50


class RateLimit:
    """Rate limiting constants for different operations."""

    COMMENT = "10 per minute"
    LOGIN = "5 per minute"
    REGISTER = "3 per hour"
