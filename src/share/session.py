from typing import Optional

ROLE_ADMIN = "admin"
ROLE_GUEST = "guest"

class Session:
    """Global session state to hold the current user's role."""
    _role : Optional[str] = ""

    @classmethod
    def set_role(cls, role: str):
        """Set the current user role ('guest' or 'admin')."""
        cls._role = role

    @classmethod
    def get_role(cls) -> str:
        """Get the current user role."""
        return cls._role

    @classmethod
    def clear(cls) -> None:
        """Clear session (e.g., on logout)."""
        cls._role = None

    @classmethod
    def is_admin(cls) -> bool:
        return cls._role == ROLE_ADMIN

    @classmethod
    def is_guest(cls) -> bool:
        return cls._role == ROLE_GUEST

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._role is not None

    @classmethod
    def role_label(cls) -> str:
        """Human-readable role label for display in the UI."""
        if cls._role == ROLE_ADMIN:
            return "Admin"
        if cls._role == ROLE_GUEST:
            return "Guest"
        return "Unknown"
