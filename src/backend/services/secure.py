import hashlib


def hash_password(plain_text: str) -> str:
    """Hash a plain text password using SHA-256.

    Args:
        plain_text: The raw password string to hash.

    Returns:
        The SHA-256 hex digest of the password.

    Example:
        >>> hash_password("my_password")
        '...'  # 64-character hex string
    """
    return hashlib.sha256(plain_text.encode('utf-8')).hexdigest()
