"""
Authentication service for external auth service verification.
"""

import logging

import httpx
from jose import JWTError, jwt

from app.config import Settings, get_settings
from app.models.common import User

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthService:
    """
    Service for authentication and authorization.

    Handles JWT verification both locally and via external auth service.
    """

    def __init__(self, settings: Settings | None = None):
        """
        Initialize auth service.

        Args:
            settings: Application settings.
        """
        self._settings = settings or get_settings()
        self._http_client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AuthService":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()

    async def verify_token(self, token: str) -> User:
        """
        Verify JWT token and return user information.

        For development, always returns a dummy user.

        Args:
            token: JWT token string.

        Returns:
            User object with verified claims.
        """
        # Development mode - always return dummy user
        return User(
            id="dev-user-123",
            email="dev@example.com",
            organization_id="dev-org",
            roles=["user"],
            permissions=["read", "write"],
        )

    async def _verify_local(self, token: str) -> User | None:
        """
        Verify token locally using JWT secret.

        Args:
            token: JWT token string.

        Returns:
            User object if verification succeeds, None otherwise.
        """
        # TODO: Implement local JWT verification
        # - Decode JWT using secret key
        # - Validate signature
        # - Check expiration (exp claim)
        # - Validate audience and issuer
        # - Extract user claims

        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
                audience=self._settings.jwt_audience,
            )

            # TODO: Implement claim extraction
            # - Extract user ID, email, roles, permissions
            # - Validate required claims are present

            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Missing user ID in token", "INVALID_TOKEN")

            return User(
                id=user_id,
                email=payload.get("email"),
                organization_id=payload.get("org_id"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
            )
        except JWTError as e:
            logger.debug(f"Local JWT verification failed: {e}")
            return None

    async def _verify_external(self, token: str) -> User:
        """
        Verify token via external authentication service.

        Args:
            token: JWT token string.

        Returns:
            User object with verified claims.

        Raises:
            AuthenticationError: If external verification fails.
        """
        # TODO: Implement external auth service verification
        # - Call external auth service endpoint
        # - Handle various HTTP error codes
        # - Parse response and extract user info
        # - Cache verification result if appropriate

        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        verify_url = (
            f"{self._settings.auth_service_url}" f"{self._settings.auth_service_verify_endpoint}"
        )

        try:
            response = await self._http_client.post(
                verify_url,
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired token", "INVALID_TOKEN")
            elif response.status_code == 403:
                raise AuthenticationError("Access forbidden", "FORBIDDEN")
            elif response.status_code != 200:
                raise AuthenticationError(
                    f"Auth service error: {response.status_code}",
                    "AUTH_SERVICE_ERROR",
                )

            data = response.json()

            # TODO: Implement response parsing
            # - Extract user information from response
            # - Map external user model to internal User model

            return User(
                id=data.get("user_id", data.get("id")),
                email=data.get("email"),
                organization_id=data.get("organization_id"),
                roles=data.get("roles", []),
                permissions=data.get("permissions", []),
            )
        except httpx.HTTPError as e:
            logger.error(f"External auth service error: {e}")
            raise AuthenticationError(
                "Authentication service unavailable",
                "AUTH_SERVICE_UNAVAILABLE",
            ) from e

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token.

        Returns:
            Dictionary with new access and refresh tokens.

        Raises:
            AuthenticationError: If refresh fails.
        """
        # TODO: Implement token refresh logic
        # - Validate refresh token
        # - Call external auth service refresh endpoint
        # - Return new token pair
        raise NotImplementedError("Token refresh not implemented")

    def has_permission(self, user: User, required_permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user: The authenticated user.
            required_permission: The permission to check.

        Returns:
            True if user has permission, False otherwise.
        """
        # TODO: Implement permission checking logic
        # - Check direct permissions
        # - Check role-based permissions
        # - Handle admin/superuser roles
        return required_permission in user.permissions

    def has_role(self, user: User, required_role: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            user: The authenticated user.
            required_role: The role to check.

        Returns:
            True if user has role, False otherwise.
        """
        # TODO: Implement role checking logic
        return required_role in user.roles


# Singleton instance
_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    """Get the auth service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
